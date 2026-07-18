from typing import Optional

from pydantic import BaseModel, ConfigDict


class SportReadDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    icon: Optional[str] = None
