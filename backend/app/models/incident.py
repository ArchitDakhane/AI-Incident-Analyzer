"""Incident ORM model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.ai_report import AIReport
    from app.models.comment import Comment
    from app.models.log_file import LogFile
    from app.models.user import User


class Incident(Base):
    """An incident captured from uploaded logs and analysis data."""

    __tablename__ = "incidents"
    __table_args__ = (
        Index("ix_incidents_status", "status"),
        Index("ix_incidents_severity", "severity"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    incident_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True)
    severity: Mapped[str] = mapped_column(
        String(50), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="open")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_by: Mapped[User | None] = relationship(back_populates="incidents")
    log_files: Mapped[list[LogFile]] = relationship(back_populates="incident")
    ai_reports: Mapped[list[AIReport]] = relationship(
        back_populates="incident")
    comments: Mapped[list[Comment]] = relationship(back_populates="incident")
