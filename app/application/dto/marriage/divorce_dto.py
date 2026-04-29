from datetime import date

from pydantic import BaseModel


class DivorceDTO(BaseModel):
    marriage_id: int
    divorced_at: date
