from datetime import date
from uuid import UUID

from pydantic import BaseModel


class DivorceDTO(BaseModel):
    marriage_id: UUID
    divorced_at: date
