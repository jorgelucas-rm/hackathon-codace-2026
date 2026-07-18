from fastapi import Depends
from sqlalchemy.orm import Session

from src.app.model.dto.sport import SportReadDTO
from src.app.model.entity.sport import Sport
from src.app.repository.sport_repository import SportRepository

# Seed idempotente — pelo menos 5 esportes conforme docs/STATUS.md (Onda 1).
DEFAULT_SPORTS: list[tuple[str, str | None]] = [
    ("Beach Tênis", "🏖️"),
    ("Futebol Society", "⚽"),
    ("Vôlei", "🏐"),
    ("Padel", "🎾"),
    ("Basquete", "🏀"),
]


def seed_sports(session: Session) -> None:
    """Seed idempotente dos esportes padrão.

    Decisão local (T-A1): função pura chamável tanto no lifespan do app
    quanto em testes — verifica os nomes já existentes antes de inserir, por
    isso rodar duas vezes não duplica. Não plugada em `main.py` por este
    executor (arquivo compartilhado) — ver seção REGISTRAR do relatório
    final para a chamada exata a acrescentar no lifespan.
    """
    existing_names = {name for (name,) in session.query(Sport.name).all()}
    for name, icon in DEFAULT_SPORTS:
        if name not in existing_names:
            session.add(Sport(name=name, icon=icon))
    session.commit()


class SportService:

    def __init__(self, sport_repository: SportRepository):
        self.sport_repository = sport_repository

    def list_all(self) -> list[SportReadDTO]:
        sports = self.sport_repository.get_all()
        return [SportReadDTO.model_validate(s) for s in sports]

    @staticmethod
    def get_service(
        sport_repository: SportRepository = Depends(SportRepository.get_instance()),
    ) -> "SportService":
        return SportService(sport_repository=sport_repository)
