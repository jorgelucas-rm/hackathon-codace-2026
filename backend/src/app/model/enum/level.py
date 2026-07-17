from enum import IntEnum


class Level(IntEnum):
    """Nível de permissão do ator autenticado (independe do tipo de ator).

    ADMIN e USER se aplicam a registros da entidade User; COMPANY é
    atribuído automaticamente a atores autenticados como Company (acesso
    das empresas) — ajuste livremente para os papéis reais do seu domínio.
    """

    ADMIN = 1
    USER = 2
    COMPANY = 3
