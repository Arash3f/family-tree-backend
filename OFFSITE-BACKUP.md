# Off-site backups (Arvan Object Storage)

> Off-site copy of the nightly Postgres and Neo4j dumps to S3-compatible storage.
> Intended target: **Arvan Cloud Object Storage** (گنجینه) free / basic plan.

`backup.database` already writes both dumps into `BACKUP_DIR` every night. That directory is a Docker
volume on the same host as the databases, so a disk or host loss takes the backups with it. With this
feature on, each run is also copied to an object-storage bucket under a dated key tree.

**Off by default.** Separate from MinIO (photos/media). A deployment that never configures it keeps
behaving exactly as before.

---

## What it does

After the nightly dumps finish, `backup.database` queues `backup.upload_offsite`, which:

1. zips the Neo4j export directory into a single file,
2. renames both artefacts to self-describing names,
3. uploads them plus a `manifest.json` under a dated prefix,
4. deletes run prefixes older than the retention window.

```
<OFFSITE_BACKUP_BUCKET>/<OFFSITE_BACKUP_PREFIX>/
  2026/
    2026-09/
      2026-09-23_00-00-00/
        postgres_family_tree_2026-09-23_00-00-00.dump
        neo4j_2026-09-23_00-00-00.zip
        manifest.json
```

**Why the upload is a separate task.** An object-storage outage retries only the transfer, on its own
backoff, instead of running `pg_dump` against the live database five more times. Local dumps stay on
disk either way.

| Piece | Where |
|-------|-------|
| Upload, keys, pruning | [`app/infrastructure/storage/object_storage_backup.py`](app/infrastructure/storage/object_storage_backup.py) |
| The two Celery tasks | [`app/celery/tasks/backup.py`](app/celery/tasks/backup.py) |
| Settings | [`app/core/config.py`](app/core/config.py) |

---

## Setup — Arvan (پلن پایه / رایگان)

1. در [پنل ابر آروان](https://panel.arvancloud.ir/) محصول **گنجینه (Object Storage)** را باز کن.
2. یک **باکت** بساز (مثلاً `family-tree-backups`).
3. از بخش کلیدها یک **Access Key** و **Secret Key** بساز.
4. Endpoint دیتاسنتر را بردار (مثلاً تهران: `s3.ir-thr-at1.arvanstorage.ir`).

### Fill in `.env`

```bash
OFFSITE_BACKUP_ENABLED=true
OFFSITE_BACKUP_ENDPOINT=s3.ir-thr-at1.arvanstorage.ir
OFFSITE_BACKUP_ACCESS_KEY=<access-key>
OFFSITE_BACKUP_SECRET_KEY=<secret-key>
OFFSITE_BACKUP_BUCKET=family-tree-backups
OFFSITE_BACKUP_REGION=ir-thr-at1
OFFSITE_BACKUP_SECURE=true
OFFSITE_BACKUP_PREFIX=backups
OFFSITE_BACKUP_RETENTION_DAYS=30
```

Enabling the feature without endpoint, keys or bucket is rejected **at start-up**, not at midnight.

No Compose overlay is required — keys travel via env into the Celery worker like other secrets.

Restart the worker after changing `.env`:

```bash
docker compose -f docker/compose.yml --env-file .env up -d celery_worker
```

---

## Configuration reference

| Setting | Default | Meaning |
|---------|---------|---------|
| `OFFSITE_BACKUP_ENABLED` | `false` | Master switch |
| `OFFSITE_BACKUP_ENDPOINT` | *(empty)* | Host or URL of the S3 API (Arvan regional endpoint) |
| `OFFSITE_BACKUP_ACCESS_KEY` | *(empty)* | Access key id |
| `OFFSITE_BACKUP_SECRET_KEY` | *(empty)* | Secret key |
| `OFFSITE_BACKUP_BUCKET` | *(empty)* | Destination bucket name |
| `OFFSITE_BACKUP_REGION` | `ir-thr-at1` | Region label sent to the S3 client |
| `OFFSITE_BACKUP_SECURE` | `true` | Use HTTPS |
| `OFFSITE_BACKUP_PREFIX` | `backups` | Key prefix inside the bucket |
| `OFFSITE_BACKUP_RETENTION_DAYS` | `30` | Delete dated runs older than this after a successful upload; `0` keeps everything |

---

## Verifying it works

```bash
docker compose -f docker/compose.yml --env-file .env \
  exec -T celery_worker python -c \
  "from app.celery.tasks.backup import create_postgres_backup; print(create_postgres_backup.delay().id)"

docker compose -f docker/compose.yml --env-file .env logs -f celery_worker
```

A successful run logs:

```
Uploaded backup 2026-09-23_00-00-00 to off-site prefix 2026/2026-09/2026-09-23_00-00-00 (3 file(s), 0 expired run(s))
```

---

## Restoring from object storage

1. Download the dated prefix from the bucket (panel, `aws s3 cp`, or any S3 client).
2. Put contents back where the worker expects them:

```bash
docker compose -f docker/compose.yml --env-file .env cp \
  ./2026-09-23_00-00-00/postgres_family_tree_2026-09-23_00-00-00.dump \
  celery_worker:/mnt/backups/backup_2026-09-23_00-00-00.sql

unzip neo4j_2026-09-23_00-00-00.zip -d neo_2026-09-23_00-00-00
docker compose -f docker/compose.yml --env-file .env cp \
  ./neo_2026-09-23_00-00-00 celery_worker:/mnt/backups/neo_2026-09-23_00-00-00

docker compose -f docker/compose.yml --env-file .env exec -T celery_worker \
  python scripts/restore_backup.py --timestamp 2026-09-23_00-00-00
```

---

## Retention

Pruning runs **after** a successful upload, never before. Only key prefixes whose run segment parses as
`%Y-%m-%d_%H-%M-%S` are considered. `OFFSITE_BACKUP_RETENTION_DAYS=0` disables pruning.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `OFFSITE_BACKUP_ENABLED is true but … is empty` at boot | Half-configured | Fill endpoint, keys and bucket, or set the flag back to `false` |
| `AccessDenied` / `InvalidAccessKeyId` | Wrong keys or bucket ACL | Recreate keys in the panel; confirm bucket name |
| `NoSuchBucket` | Typo or wrong region endpoint | Match endpoint to the bucket's datacenter |
| Uploads never start | The `backup_database` queue has no consumer | Worker must run `-Q …,backup_database` |

---

## Security notes

- Keep Access/Secret keys out of git (`.env` is ignored). Rotate by creating a new key in the panel and restarting the worker.
- Dumps are **not encrypted at rest** beyond the provider's storage encryption. If needed, encrypt before upload in `upload_backup_run`.
- Free-tier quotas (storage + egress) are small — watch dump size and retention so you stay inside the plan.
