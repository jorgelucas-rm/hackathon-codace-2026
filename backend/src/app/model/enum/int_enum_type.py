from enum import IntEnum
from typing import Type, TypeVar

from sqlalchemy import Integer
from sqlalchemy.types import TypeDecorator

E = TypeVar("E", bound=IntEnum)


class IntEnumType(TypeDecorator):
    """Coluna SQLAlchemy que persiste um IntEnum como inteiro e o reidrata na leitura."""

    impl = Integer
    cache_ok = True

    def __init__(self, enum_class: Type[E], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum_class = enum_class

    def process_bind_param(self, value, dialect):
        if isinstance(value, self.enum_class):
            return value.value
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return self.enum_class(value)
        return value
