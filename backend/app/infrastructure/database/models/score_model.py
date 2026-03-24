from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, Index, func, DateTime,
)
from app.infrastructure.database.types import FlexibleJSON
from sqlalchemy.orm import relationship

from app.infrastructure.database.session import Base


class ScoreModel(Base):
    __tablename__ = "score_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    politician_id = Column(Integer, ForeignKey("politicians.id", ondelete="CASCADE"), nullable=False, index=True)
    overall_score = Column(Float, nullable=False)
    participation_score = Column(Float, nullable=False)
    disclosure_score = Column(Float, nullable=False)
    integrity_risk_adjustment = Column(Float, nullable=False)

    # Detailed breakdowns for transparency
    participation_breakdown = Column(FlexibleJSON, nullable=True)
    disclosure_breakdown = Column(FlexibleJSON, nullable=True)
    integrity_breakdown = Column(FlexibleJSON, nullable=True)

    formula_version = Column(String(20), nullable=False, index=True)
    computed_at = Column(DateTime, server_default=func.now())
    is_current = Column(Boolean, default=True, index=True)

    politician = relationship("PoliticianModel", back_populates="scores")

    __table_args__ = (
        Index("ix_score_politician_current", "politician_id", "is_current"),
        Index("ix_score_leaderboard", "is_current", "overall_score"),
    )
