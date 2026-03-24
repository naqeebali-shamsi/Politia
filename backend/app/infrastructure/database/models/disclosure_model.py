from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, Index, Text, func, DateTime,
)
from sqlalchemy.orm import relationship

from app.infrastructure.database.session import Base


class DisclosureModel(Base):
    __tablename__ = "disclosure_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    politician_id = Column(Integer, ForeignKey("politicians.id", ondelete="CASCADE"), nullable=False, index=True)
    election_year = Column(Integer, nullable=False)

    # Assets (all in INR)
    total_assets = Column(Float, nullable=True)
    movable_assets = Column(Float, nullable=True)
    immovable_assets = Column(Float, nullable=True)
    cash_on_hand = Column(Float, nullable=True)
    bank_deposits = Column(Float, nullable=True)

    # Liabilities
    total_liabilities = Column(Float, nullable=True)

    # Criminal disclosures
    criminal_cases = Column(Integer, default=0)
    serious_criminal_cases = Column(Integer, default=0)
    criminal_case_details = Column(Text, nullable=True)

    # Completeness flags
    affidavit_complete = Column(Boolean, default=False)
    pan_declared = Column(Boolean, default=False)

    source_id = Column(Integer, ForeignKey("source_records.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    politician = relationship("PoliticianModel", back_populates="disclosures")

    __table_args__ = (
        Index("ix_disclosure_politician_year", "politician_id", "election_year"),
    )
