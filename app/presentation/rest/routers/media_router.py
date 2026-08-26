from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import Response

from app.application.services.person_photo_service import (
    PersonPhotoService,
    verify_media_access,
)
from app.application.use_cases.media.upload_media_use_case import UploadMediaUseCase
from app.domain.exceptions.media_exceptions import (
    InvalidMediaObjectKeyException,
)
from app.presentation.dependencies import get_person_photo_service
from app.presentation.rest.dependencies.tree_guard import require_tree_upload_photo
from app.presentation.rest.schemas.dto.media_schema import MediaUploadResponse

upload_router = APIRouter(prefix="/media", tags=["Media"])
serve_router = APIRouter(prefix="/media", tags=["Media"])


@upload_router.post(
    "/upload",
    response_model=MediaUploadResponse,
    dependencies=[Depends(require_tree_upload_photo)],
)
async def upload_media(
    file: UploadFile = File(...),
    photo_service: PersonPhotoService = Depends(get_person_photo_service),
) -> MediaUploadResponse:
    usecase = UploadMediaUseCase(photo_service)
    result = await usecase.execute(file)
    return MediaUploadResponse(object_key=result.object_key)


@serve_router.get("/{object_key:path}")
async def get_media(
    object_key: str,
    exp: int = Query(..., ge=1),
    sig: str = Query(..., min_length=32, max_length=128),
    photo_service: PersonPhotoService = Depends(get_person_photo_service),
) -> Response:
    """Stream a person photo. Auth is the HMAC query (img tags cannot send Bearer)."""
    if not verify_media_access(object_key, exp, sig):
        raise InvalidMediaObjectKeyException(detail=["invalid or expired media link"])

    data, content_type = await photo_service.read_person_photo(object_key)
    return Response(
        content=data,
        media_type=content_type,
        headers={
            "Cache-Control": "private, max-age=300",
            "X-Content-Type-Options": "nosniff",
        },
    )
