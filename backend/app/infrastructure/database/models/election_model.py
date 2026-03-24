from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, Index, func, DateTime,
)
from sqlalchemy.orm import relationship

from app.infrastructure.database.session import Base


class ElectionModel(Base):
    __tablename__ = "election_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    politician_id = Column(Integer, ForeignKey("politicians.id", ondelete="CASCADE"), nullable=False, index=True)
    constituency_id = Column(Integer, ForeignKey("constituencies.id", ondelete="SET NULL"), nullable=True, index=True)
    election_year = Column(Integer, nullable=False, index=True)
    election_type = Column(String(50), nullable=True)
    party = Column(String(255), nullable=False)
    result = Column(String(20), nullable=False)
    votes = Column(Integer, nullable=True)
    vote_share = Column(Float, nullable=True)
    margin = Column(Integer, nullable=True)
    deposit_lost = Column(Boolean, nullable=True)
    affidavit_url = Column(String(500), nullable=True)
    source_id = Column(Integer, ForeignKey("source_records.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    politician = relationship("PoliticianModel", back_populates="elections")

    __table_args__ = (
        Index("ix_election_politician_year", "politician_id", "election_year"),
        Index("ix_election_constituency_year", "constituency_id", "election_year"),
    )
