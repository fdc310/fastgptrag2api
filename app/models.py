from datetime import datetime

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class SettingRobot(Base):
    """ya_setting_robot - read-only mapping, no auto table creation."""

    __tablename__ = "ya_setting_robot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(255), nullable=False, comment="device code")
    device_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_disable: Mapped[int] = mapped_column(Integer, default=0)
    is_delete: Mapped[int] = mapped_column(Integer, default=0)
    create_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    update_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class MemberRobotAttributes(Base):
    """ya_member_robot_attributes - read-only mapping, no auto table creation."""

    __tablename__ = "ya_member_robot_attributes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(Integer, nullable=False)
    robot_id: Mapped[int] = mapped_column(Integer, nullable=False)
    dataset_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_disable: Mapped[int] = mapped_column(Integer, default=0)
    is_delete: Mapped[int] = mapped_column(Integer, default=0)
    create_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    update_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
