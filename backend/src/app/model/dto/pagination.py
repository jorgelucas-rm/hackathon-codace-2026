from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Pagination(BaseModel, Generic[T]):
    items: List[T]
    total: int
    total_filtered: int
    page: int
    page_size: int
    total_pages: int
