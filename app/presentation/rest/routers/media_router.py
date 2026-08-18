from fastapi import APIRouter, Depends, File, UploadFile

from app.application.services.person_photo_service import PersonPhotoService
from app.application.use_cases.media.upload_media_use_case import UploadMediaUseCase
from app.presentation.rest.dependencies.tree_guard import require_tree_upload_photo
from app.presentation.rest.schemas.dto.media_schema import MediaUploadResponse
from app.presentation.rest.utils.dependencies import get_person_photo_service

upload_router = APIRouter(prefix="/media", tags=["Media"])


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
