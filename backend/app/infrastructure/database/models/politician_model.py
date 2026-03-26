from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Index,
    func,
)
from sqlalchemy.orm import relationship

from app.infrastructure.database.session import Base
from app.infrastructure.database.types import StringArray, SearchVector


class PoliticianModel(Base):
    __tablename__ = "politicians"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(255), nullable=False, index=True)
    name_variants = Column(StringArray, default=list)
    photo_url = Column(String(500), nullable=True)
    gender = Column(String(20), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    education = Column(String(255), nullable=True)
    profession = Column(String(255), nullable=True)

    # Denormalized current status for fast queries
    current_party = Column(String(255), nullable=True, index=True)
    current_chamber = Column(String(50), nullable=True, index=True)
    current_constituency = Column(String(255), nullable=True)
    current_state = Column(String(100), nullable=True, index=True)
    is_active = Column(Boolean, default=True, index=True)

    # Cross-source identifiers for entity resolution
    tcpd_id = Column(String(100), nullable=True, unique=True, index=True)
    myneta_id = Column(String(100), nullable=True, index=True)
    prs_slug = Column(String(255), nullable=True, index=True)
    opensanctions_id = Column(String(100), nullable=True, index=True)

    # Full-text search vector
    search_vector = Column(SearchVector, nullable=True)

    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    offices = relationship("OfficeModel", back_populates="politician", lazy="selectin")
    scores = relationship("ScoreModel", back_populates="politician", lazy="noload")
    activities = relationship("ActivityModel", back_populates="politician", lazy="noload")
    disclosures = relationship("DisclosureModel", back_populates="politician", lazy="noload")
    elections = relationship("ElectionModel", back_populates="politician", lazy="noload")
    questions = relationship("QuestionModel", back_populates="politician", lazy="noload")

    __table_args__ = (
        Index("ix_politicians_state_party", "current_state", "current_party"),
        Index("ix_politicians_chamber_active", "current_chamber", "is_active"),
    )
