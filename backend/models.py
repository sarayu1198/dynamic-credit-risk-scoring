
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True
    )
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Borrower(Base):
    __tablename__ = "borrowers"

    borrower_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True
    )
    managed_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id"),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(150))
    external_reference: Mapped[str | None] = mapped_column(
        String(50), unique=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    assessment_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True
    )
    borrower_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("borrowers.borrower_id"),
        nullable=False,
    )
    default_probability: Mapped[Decimal] = mapped_column(
        Numeric(7, 6)
    )
    risk_score: Mapped[int] = mapped_column(SmallInteger)
    risk_category: Mapped[str] = mapped_column(String(20))
    model_name: Mapped[str] = mapped_column(String(100))
    model_version: Mapped[str] = mapped_column(String(50))
    threshold_used: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4)
    )
    snapshot_id: Mapped[str | None] = mapped_column(String(100))
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
