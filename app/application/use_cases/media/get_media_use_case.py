from app.application.services.person_photo_service import PersonPhotoService


class GetMediaUseCase:
    def __init__(self, photo_service: PersonPhotoService):
        self.photo_service = photo_service

    async def execute(self, object_key: str) -> tuple[bytes, str]:
        return await self.photo_service.get_person_photo(object_key)
