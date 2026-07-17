from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, model_validator

from src.app.model.enum import ResponseStatus

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    code: int
    message: str
    error_code: Optional[str] = None
    data: Optional[T] = None
    status: ResponseStatus | None = None

    @model_validator(mode="after")
    def _set_status(self):
        self.status = (
            ResponseStatus.ERROR if self.code >= 400 else ResponseStatus.SUCCESS
        )
        return self
