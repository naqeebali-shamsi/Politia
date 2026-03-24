from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Index, func,
)
from sqlalchemy.orm import relationship

from app.infrastructure.database.session import Base


class OfficeModel(Base):
    __tablename__ = "offices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    politician_id = Column(Integer, ForeignKey("politicians.id", ondelete="CASCADE"), nullable=False, index=True)
    constituency_id = Column(Integer, ForeignKey("constituencies.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(50), nullable=False, default="MP")
    chamber = Column(String(50), nullable=False)
    party = Column(String(255), nullable=False)
    term_number = Column(Integer, nullable=True)
    term_start = Column(DateTime, nullable=True)
    term_end = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime, server_default=func.now())

    politician = relationship("PoliticianModel", back_populates="offices")

    __table_args__ = (
        Index("ix_office_politician_active", "politician_id", "is_active"),
    )
