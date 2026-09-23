# Google Drive backups

> Off-site copy of the nightly Postgres and Neo4j dumps.

`backup.database` already writes both dumps into `BACKUP_DIR` every night. That directory is a Docker
volume on the same host as the databases, so a disk or host loss takes the backups with it. With this
feature on, each run is also copied to a Google Drive folder under a dated folder tree.

**Off by default.** A deployment that never configures it keeps behaving exactly as before.

---

## Contents

- [What it does](#what-it-does)
- [Setup — what you have to fill in](#setup--what-you-have-to-fill-in)
- [Configuration reference](#configuration-reference)
- [Verifying it works](#verifying-it-works)
- [Restoring from Drive](#restoring-from-drive)
- [Retention](#retention)
- [Troubleshooting](#troubleshooting)
- [Security notes](#security-notes)

---

## What it does

After the nightly dumps finish, `backup.database` queues a second task,
`backup.upload_to_drive`, which:

1. zips the Neo4j export directory into a single file,
2. renames both artefacts to self-describing names,
3. uploads them plus a `manifest.json` into a dated folder,
4. trashes folders older than the retention window.

```
<GOOGLE_DRIVE_FOLDER_ID>/
  2026/
    2026-09/
      2026-09-23_00-00-00/
        postgres_family_tree_2026-09-23_00-00-00.dump
        neo4j_2026-09-23_00-00-00.zip
        manifest.json
```

Year / month / run, so the Drive UI sorts chronologically on its own and "the backup of 2026-09-23"
is something you navigate to rather than grep a log for. `manifest.json` records the run timestamp,
the database name, the environment and the size of each file, so a downloaded folder explains itself
without the log history.

**Why the upload is a separate task.** A Drive outage retries only the transfer, on its own backoff,
instead of running `pg_dump` against the live database five more times. And because the local dumps
are already on disk by then, an upload that fails permanently costs you the off-site copy only —
never the backup itself.

| Piece | Where |
|-------|-------|
| Upload, folders, pruning | [`app/infrastructure/storage/google_drive_backup.py`](app/infrastructure/storage/google_drive_backup.py) |
| The two Celery tasks | [`app/celery/tasks/backup.py`](app/celery/tasks/backup.py) |
| Settings | [`app/core/config.py`](app/core/config.py) |
| Key mount for Compose | [`docker/compose.google-drive.yml`](docker/compose.google-drive.yml) |

---

## Setup — what you have to fill in

Authentication is a **service account**: its own identity, no interactive consent, and no refresh
token to expire — which is what an unattended nightly job needs.

| # | Where | Action | What you end up with |
|---|-------|--------|----------------------|
| 1 | [console.cloud.google.com](https://console.cloud.google.com/) | Create a project, then **APIs & Services → Library → Google Drive API → Enable** | A project with the Drive API on |
| 2 | **IAM & Admin → Service Accounts → Create** | Name it, e.g. `family-tree-backup`. No project role is needed — access comes from the folder share, not from IAM | The account's email, `…@….iam.gserviceaccount.com` |
| 3 | That account → **Keys → Add key → Create new key → JSON** | Download the key | A `.json` key file — treat it as a password |
| 4 | [drive.google.com](https://drive.google.com/) | Create the destination folder, then **Share** it with the service-account email as **Editor** | A folder the job may write to |
| 5 | Open that folder | Copy the last segment of its URL, `…/folders/<THIS>` | `GOOGLE_DRIVE_FOLDER_ID` |

> [!IMPORTANT]
> A service account has **no Drive storage quota of its own**. The destination folder must be owned by
> a normal Google account — whose quota is then used — or live in a **Shared Drive**, in which case
> also set `GOOGLE_DRIVE_SHARED_DRIVE_ID` to that drive's id. A folder created *by* the service
> account fails at upload time with `storageQuotaExceeded`.

### Place the key

```bash
mkdir -p secrets
cp ~/Downloads/<key>.json secrets/google-drive-service-account.json
chmod 600 secrets/google-drive-service-account.json
```

`secrets/` is in `.gitignore`. The key is never read by the API or beat containers — only the Celery
worker mounts it, read-only.

### Fill in `.env`

```bash
GOOGLE_DRIVE_BACKUP_ENABLED=true
GOOGLE_DRIVE_CREDENTIALS_FILE=/run/secrets/google-drive-service-account.json
GOOGLE_DRIVE_FOLDER_ID=1AbCdEfGhIjKlMnOpQrStUvWxYz
GOOGLE_DRIVE_SHARED_DRIVE_ID=
GOOGLE_DRIVE_RETENTION_DAYS=30
```

Enabling the feature without a key path or a folder id is rejected **at start-up**, not at midnight.

### Start with the mount overlay

```bash
docker compose -f docker/compose.yml -f docker/compose.google-drive.yml --env-file .env up -d
```

The overlay is separate from `compose.yml` on purpose: a bind mount whose source file does not exist
makes Docker create a *directory* in its place, which would break every deployment that has not set
this up. Passing the overlay is the explicit statement that the key file is there.

---

## Configuration reference

| Setting | Default | Meaning |
|---------|---------|---------|
| `GOOGLE_DRIVE_BACKUP_ENABLED` | `false` | Master switch. While false nothing here runs, and the Google client libraries need not even be installed |
| `GOOGLE_DRIVE_CREDENTIALS_FILE` | `/run/secrets/google-drive-service-account.json` | Path to the service-account JSON key **inside the container** |
| `GOOGLE_DRIVE_FOLDER_ID` | *(empty)* | Id of the Drive folder shared with the service account |
| `GOOGLE_DRIVE_SHARED_DRIVE_ID` | *(empty)* | Set only when that folder lives in a Shared Drive |
| `GOOGLE_DRIVE_RETENTION_DAYS` | `30` | Dated folders older than this are trashed after each successful upload; `0` keeps everything forever |

One Compose-only variable is **not** an application setting and therefore not in `.env.example`:

| Variable | Default | Meaning |
|----------|---------|---------|
| `GOOGLE_DRIVE_CREDENTIALS_HOST_FILE` | `./secrets/google-drive-service-account.json` | Path to the key **on the host**. Export it in the shell to keep the key somewhere else |

---

## Verifying it works

Trigger a run instead of waiting for midnight:

```bash
docker compose -f docker/compose.yml -f docker/compose.google-drive.yml --env-file .env \
  exec -T celery_worker python -c \
  "from app.celery.tasks.backup import create_postgres_backup; print(create_postgres_backup.delay().id)"

docker compose -f docker/compose.yml --env-file .env logs -f celery_worker
```

A successful run logs:

```
Uploaded backup 2026-09-23_00-00-00 to Drive folder 2026/2026-09/2026-09-23_00-00-00 (3 file(s), 0 expired folder(s))
```

---

## Restoring from Drive

The Drive copy holds the same artefacts as `BACKUP_DIR`, so a restore is a download plus the existing
restore script:

```bash
# 1. Download the dated folder from Drive.
# 2. Put its contents back where the worker expects them:
docker compose -f docker/compose.yml --env-file .env cp \
  ./2026-09-23_00-00-00/postgres_family_tree_2026-09-23_00-00-00.dump \
  celery_worker:/mnt/backups/backup_2026-09-23_00-00-00.sql

unzip neo4j_2026-09-23_00-00-00.zip -d neo_2026-09-23_00-00-00
docker compose -f docker/compose.yml --env-file .env cp \
  ./neo_2026-09-23_00-00-00 celery_worker:/mnt/backups/neo_2026-09-23_00-00-00

# 3. Restore as usual.
docker compose -f docker/compose.yml --env-file .env exec -T celery_worker \
  python scripts/restore_backup.py --timestamp 2026-09-23_00-00-00
```

The local names are positional (`backup_<ts>.sql`, `neo_<ts>/`); the Drive names are self-describing.
`restore_backup.py` reads the local ones, which is why the copy step renames them back.

As with any restore here, the two dumps are taken back to back rather than in one transaction, so a
write landing between them can appear on only one side — and Neo4j can always be rebuilt from
Postgres by reconciliation if the graph side looks wrong.

---

## Retention

Pruning runs **after** a successful upload, never before, so a failing upload can never be the reason
old backups disappear. Only folders whose name parses as `%Y-%m-%d_%H-%M-%S` are considered — a folder
someone added by hand is left alone. Deleted folders go to the Drive trash, which gives you the usual
30-day grace period on top.

`GOOGLE_DRIVE_RETENTION_DAYS=0` disables pruning entirely.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Service-account key not found at …` | The key is not mounted | Start with `-f docker/compose.google-drive.yml`, and check `GOOGLE_DRIVE_CREDENTIALS_HOST_FILE` points at a real *file* |
| `GOOGLE_DRIVE_BACKUP_ENABLED is true but GOOGLE_DRIVE_FOLDER_ID is empty` at boot | Half-configured | Fill in the folder id, or set the flag back to `false` |
| `File not found: <id>` | The folder was never shared with the service account, or the id is wrong | Re-share as **Editor**; re-copy the id from the folder URL |
| `storageQuotaExceeded` | The folder is owned by the service account | Recreate it under a real account or a Shared Drive |
| `…the Google client libraries are missing` | Image built before the dependency was added | Rebuild the image (`--build`) |
| Uploads never start | The `backup_database` queue has no consumer | The worker must run `-Q …,backup_database` — `backup.upload_to_drive` is routed to the same queue |

---

## Security notes

- The key is mounted **read-only**, on the worker only. Beat merely enqueues the task and never sees it.
- The scope requested is full `drive` rather than `drive.file`, because pruning has to delete dated
  folders that earlier deploys created, which `drive.file` cannot be relied on to cover across
  credential rotations. The account still only reaches what has been shared with it — which should be
  that one folder and nothing else.
- Rotating the key is a file swap plus a worker restart; no application change is involved.
- The dumps are **not encrypted at rest** beyond Google's own storage encryption. If the tree data
  warrants it, encrypt the dump before upload — that hook belongs in `upload_backup_run`.
