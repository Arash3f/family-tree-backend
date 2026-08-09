from fastapi import UploadFile

from app.application.dto.media.media_upload_dto import MediaUploadResponseDTO
from app.application.services.person_photo_service import PersonPhotoService


class UploadMediaUseCase:
    def __init__(self, photo_service: PersonPhotoService):
        self.photo_service = photo_service

    async def execute(self, file: UploadFile) -> MediaUploadResponseDTO:
        data = await file.read()
        object_key = await self.photo_service.upload_person_photo(
            data, file.content_type
        )
        return MediaUploadResponseDTO(object_key=object_key)
