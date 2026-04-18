from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Integer, String, Text, DateTime, Float, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    iu_username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    campus: Mapped[str] = mapped_column(String(50), nullable=False)
    major: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    year: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    bonus_points: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    attendance: Mapped[List["Attendance"]] = relationship(
        "Attendance", back_populates="student", cascade="all, delete-orphan"
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g. Academic, Career, Social
    campus: Mapped[str] = mapped_column(String(50), nullable=False)
    event_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    check_in_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=10)
    event_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    attendance: Mapped[List["Attendance"]] = relationship(
        "Attendance", back_populates="event", cascade="all, delete-orphan"
    )
    event_code: Mapped[Optional["EventCode"]] = relationship(
        "EventCode", back_populates="event", uselist=False
    )


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("student_id", "event_id", name="uq_student_event"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), nullable=False)
    points_earned: Mapped[int] = mapped_column(Integer, nullable=False)
    checked_in_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    student: Mapped["Student"] = relationship("Student", back_populates="attendance")
    event: Mapped["Event"] = relationship("Event", back_populates="attendance")


class EventCode(Base):
    __tablename__ = "event_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), unique=True, nullable=False)
    event_name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    set_by: Mapped[str] = mapped_column(String(50), default="system")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    event: Mapped["Event"] = relationship("Event", back_populates="event_code")


class EndpointPerformance(Base):
    __tablename__ = "endpoint_performance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    endpoint: Mapped[str] = mapped_column(String(100), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    response_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    called_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
