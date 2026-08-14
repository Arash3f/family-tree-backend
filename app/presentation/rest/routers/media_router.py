from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response

from app.application.services.person_photo_service import PersonPhotoService
from app.application.use_cases.media.get_media_use_case import GetMediaUseCase
from app.application.use_cases.media.upload_media_use_case import UploadMediaUseCase
from app.domain.shared.permissions import Permissions
from app.presentation.rest.dependencies.permission_guard import RequirePermission
from app.presentation.rest.schemas.dto.media_schema import MediaUploadResponse
from app.presentation.rest.utils.dependencies import get_person_photo_service

router = APIRouter(prefix="/media", tags=["Media"])


@router.post(
    "/upload",
    response_model=MediaUploadResponse,
    dependencies=[Depends(RequirePermission(Permissions.MEDIA_UPLOAD))],
)
async def upload_media(
    file: UploadFile = File(...),
    photo_service: PersonPhotoService = Depends(get_person_photo_service),
) -> MediaUploadResponse:
    usecase = UploadMediaUseCase(photo_service)
    result = await usecase.execute(file)
    return MediaUploadResponse(object_key=result.object_key)


@router.get(
    "/{object_key:path}",
    response_class=Response,
    responses={200: {"content": {"image/jpeg": {}, "image/png": {}, "image/webp": {}}}},
)
async def get_media(
    object_key: str,
    photo_service: PersonPhotoService = Depends(get_person_photo_service),
) -> Response:
    # <img> cannot send Authorization; keys are unguessable UUIDs.
    body, content_type = await GetMediaUseCase(photo_service).execute(object_key)
    return Response(
        content=body,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=86400, immutable",
            "Content-Disposition": "inline",
        },
    )
