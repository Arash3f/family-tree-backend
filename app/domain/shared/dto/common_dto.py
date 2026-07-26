from uuid import UUID

from pydantic import BaseModel


class IdDTO(BaseModel):
    id: UUID


class ResultDTO(BaseModel):
    result: str
