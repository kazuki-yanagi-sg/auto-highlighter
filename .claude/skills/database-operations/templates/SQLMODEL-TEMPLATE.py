# SQLModel テンプレート
# 参考: api/src/models/tickets/models.py

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Column, String, Text
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship

from src.models.base import BaseModel


class ModelStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


@dataclass(frozen=True)
class ModelConstraints:
    TITLE_MAX_LENGTH: int = 300
    TITLE_MIN_LENGTH: int = 1
    DESCRIPTION_MAX_LENGTH: int | None = None


if TYPE_CHECKING:
    from src.models.child_models.models import ChildModel
    from src.models.users.models import User


class Model(BaseModel, table=True):
    __tablename__ = "models"

    title: str = Field(
        sa_column=Column(
            String(ModelConstraints.TITLE_MAX_LENGTH),
            nullable=False,
        ),
    )

    description: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        nullable=False,
    )

    status: ModelStatus = Field(
        default=ModelStatus.ACTIVE,
        sa_column=Column(SAEnum(ModelStatus), nullable=False),
    )

    # 親リレーション
    user: "User" = Relationship(back_populates="models")

    # 子リレーション（cascade_delete 必須）
    children: list["ChildModel"] = Relationship(
        back_populates="parent",
        cascade_delete=True,
    )


# 中間テーブル例
# from sqlalchemy import UniqueConstraint
#
# class ModelsUsers(BaseModel, table=True):
#     __tablename__ = "models_users"
#     __table_args__ = (UniqueConstraint("model_id", "user_id"),)
#
#     model_id: UUID = Field(foreign_key="models.id", index=True, nullable=False)
#     user_id: UUID = Field(foreign_key="users.id", index=True, nullable=False)
#
#     model: "Model" = Relationship(back_populates="models_users")
#     user: "User" = Relationship(back_populates="models_users")


# 複数外部キー例（sa_relationship_kwargs で明示）
# assigned_user: Optional["User"] = Relationship(
#     back_populates="assigned_tickets",
#     sa_relationship_kwargs={"foreign_keys": "[Ticket.assigned_user_id]"},
# )
