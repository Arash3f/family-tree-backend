from pydantic import BaseModel


class IdDTO(BaseModel):
    id: int


class ResultDTO(BaseModel):
    result: str
