from typing import Optional, Type

from src.app.model.entity.group_member import GroupMember
from src.app.model.enum.group_member_status import GroupMemberStatus
from src.app.repository.base_repository import BaseRepository

# `repository/group_member_repository.py` — novo (Onda 3, T-C). Segue o
# mesmo padrão de `BookingRepository`/`GroupRepository`.

ACTIVE_MEMBER_STATUSES = (GroupMemberStatus.PENDING, GroupMemberStatus.CONFIRMED)


class GroupMemberRepository(BaseRepository[GroupMember]):

    @property
    def model(self) -> Type[GroupMember]:
        return GroupMember

    def get_active_member(self, group_id: int, user_id: int) -> Optional[GroupMember]:
        """Membro `PENDING` (não checa TTL aqui — expiração preguiçosa é
        responsabilidade do caller, mesmo padrão de
        `BookingRepository.get_active_by_court_and_date`) ou `CONFIRMED` do
        usuário no grupo — usado para `ALREADY_MEMBER`/`NOT_GROUP_MEMBER`."""
        return (
            self.session.query(GroupMember)
            .filter(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id,
                GroupMember.status.in_(ACTIVE_MEMBER_STATUSES),
            )
            .order_by(GroupMember.id.desc())
            .first()
        )

    def get_by_group(self, group_id: int) -> list[GroupMember]:
        return (
            self.session.query(GroupMember)
            .filter(GroupMember.group_id == group_id)
            .order_by(GroupMember.joined_at.asc())
            .all()
        )

    def get_active_by_group(self, group_id: int) -> list[GroupMember]:
        """`PENDING` (checagem de TTL a cargo do caller) + `CONFIRMED` — base
        da contagem de vagas ocupadas (`GROUP_FULL`, `filled_spots`)."""
        return (
            self.session.query(GroupMember)
            .filter(
                GroupMember.group_id == group_id,
                GroupMember.status.in_(ACTIVE_MEMBER_STATUSES),
            )
            .all()
        )

    def get_confirmed_by_group(self, group_id: int) -> list[GroupMember]:
        return (
            self.session.query(GroupMember)
            .filter(
                GroupMember.group_id == group_id,
                GroupMember.status == GroupMemberStatus.CONFIRMED,
            )
            .all()
        )

    def count_confirmed(self, group_id: int) -> int:
        return (
            self.session.query(GroupMember)
            .filter(
                GroupMember.group_id == group_id,
                GroupMember.status == GroupMemberStatus.CONFIRMED,
            )
            .count()
        )

    @property
    def orderable_fields(self) -> dict:
        return {
            "id": GroupMember.id,
            "joined_at": GroupMember.joined_at,
            "status": GroupMember.status,
        }

    @property
    def equal_filters(self) -> dict:
        return {
            "group_id": GroupMember.group_id,
            "user_id": GroupMember.user_id,
            "status": GroupMember.status,
        }
