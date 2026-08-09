from pydantic import BaseModel


class MediaUploadResponseDTO(BaseModel):
    object_key: str
