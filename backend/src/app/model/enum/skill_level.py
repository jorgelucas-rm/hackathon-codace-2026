from enum import IntEnum


class SkillLevel(IntEnum):
    """Nível de habilidade autodeclarado do jogador (perfil de `User`).

    Próprio de `entity/user.py` (T-A2) — não registrado em
    `model/enum/__init__.py` (arquivo compartilhado); importe direto deste
    módulo onde precisar.
    """

    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
