from pydantic import BaseModel


class MediaUploadResponse(BaseModel):
    object_key: str
