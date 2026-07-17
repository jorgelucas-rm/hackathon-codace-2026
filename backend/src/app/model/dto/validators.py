import re
from enum import IntEnum
from typing import Annotated, Type, TypeVar

from pydantic import WithJsonSchema
from pydantic.functional_serializers import PlainSerializer
from pydantic.functional_validators import AfterValidator, BeforeValidator

E = TypeVar("E", bound=IntEnum)


# ── CPF ──────────────────────────────────────────────────────────────────────

def _parse_cpf(v: str) -> str:
    digits = re.sub(r"\D", "", v)
    if len(digits) != 11:
        raise ValueError("CPF deve conter 11 dígitos")
    if len(set(digits)) == 1:
        raise ValueError("CPF inválido")
    total = sum(int(d) * (10 - i) for i, d in enumerate(digits[:9]))
    r = (total * 10) % 11
    if r == 10:
        r = 0
    if r != int(digits[9]):
        raise ValueError("CPF inválido")
    total = sum(int(d) * (11 - i) for i, d in enumerate(digits[:10]))
    r = (total * 10) % 11
    if r == 10:
        r = 0
    if r != int(digits[10]):
        raise ValueError("CPF inválido")
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


CpfStr = Annotated[str, BeforeValidator(_parse_cpf)]


# ── CNPJ ─────────────────────────────────────────────────────────────────────

def _cnpj_char_value(c: str) -> int:
    return ord(c) - 48


def _parse_cnpj(v: str) -> str:
    cleaned = re.sub(r"[.\-/\s]", "", v).upper()
    if len(cleaned) != 14:
        raise ValueError("CNPJ deve conter 14 caracteres")
    if not re.match(r"^[A-Z0-9]{14}$", cleaned):
        raise ValueError("CNPJ contém caracteres inválidos")
    if len(set(cleaned)) == 1:
        raise ValueError("CNPJ inválido")
    if not cleaned[12].isdigit() or not cleaned[13].isdigit():
        raise ValueError("CNPJ inválido: dígitos verificadores devem ser numéricos")

    def _check(chars: str, weights: list) -> int:
        total = sum(_cnpj_char_value(c) * w for c, w in zip(chars, weights))
        r = total % 11
        return 0 if r < 2 else 11 - r

    if _check(cleaned[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]) != int(cleaned[12]):
        raise ValueError("CNPJ inválido")
    if _check(cleaned[:13], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]) != int(cleaned[13]):
        raise ValueError("CNPJ inválido")
    return f"{cleaned[:2]}.{cleaned[2:5]}.{cleaned[5:8]}/{cleaned[8:12]}-{cleaned[12:]}"


CnpjStr = Annotated[str, BeforeValidator(_parse_cnpj)]


# ── Password ──────────────────────────────────────────────────────────────────

def _validate_password(v: str) -> str:
    errors = []
    if len(v) < 8:
        errors.append("mínimo 8 caracteres")
    if not re.search(r"[A-Z]", v):
        errors.append("ao menos uma letra maiúscula")
    if not re.search(r"[a-z]", v):
        errors.append("ao menos uma letra minúscula")
    if not re.search(r"\d", v):
        errors.append("ao menos um dígito")
    if not re.search(r"[^A-Za-z0-9]", v):
        errors.append("ao menos um caractere especial")
    if errors:
        raise ValueError("Senha deve conter: " + ", ".join(errors))
    return v


PasswordStr = Annotated[str, AfterValidator(_validate_password)]


# ── Serializable Enum ─────────────────────────────────────────────────────────

def serializable_enum(enum_class: Type[E]):
    """Annotated type for IntEnum fields.

    Input       — accepts the enum member, int value, or str name (case-insensitive).
    JSON output — serializes to the member's name string.
    """
    def _parse(v):
        if isinstance(v, enum_class):
            return v
        if isinstance(v, int):
            return enum_class(v)
        if isinstance(v, str):
            try:
                return enum_class[v.upper()]
            except KeyError:
                try:
                    return enum_class(int(v))
                except (ValueError, KeyError):
                    raise ValueError(
                        f"'{v}' não é um valor válido para {enum_class.__name__}. "
                        f"Valores aceitos: {[e.name for e in enum_class]}"
                    )
        raise ValueError(f"Não foi possível converter {v!r} para {enum_class.__name__}")

    return Annotated[
        enum_class,
        BeforeValidator(_parse),
        PlainSerializer(
            lambda v: v.name,
            return_type=str,
            when_used="json",
        ),
        WithJsonSchema({"type": "string", "enum": [e.name for e in enum_class]}),
    ]
