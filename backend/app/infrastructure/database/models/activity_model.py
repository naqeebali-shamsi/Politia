from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, Index, func, DateTime,
)
from app.infrastructure.database.types import StringArray
from sqlalchemy.orm import relationship

from app.infrastructure.database.session import Base


class ActivityModel(Base):
    __tablename__ = "activity_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    politician_id = Column(Integer, ForeignKey("politicians.id", ondelete="CASCADE"), nullable=False, index=True)
    term_number = Column(Integer, nullable=True, index=True)
    session_name = Column(String(255), nullable=True)
    attendance_percentage = Column(Float, nullable=True)
    questions_asked = Column(Integer, default=0)
    debates_participated = Column(Integer, default=0)
    private_bills_introduced = Column(Integer, default=0)
    committee_memberships = Column(Integer, default=0)
    committee_names = Column(StringArray, nullable=True)
    source_id = Column(Integer, ForeignKey("source_records.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    politician = relationship("PoliticianModel", back_populates="activities")

    __table_args__ = (
        Index("ix_activity_politician_term", "politician_id", "term_number"),
    )
