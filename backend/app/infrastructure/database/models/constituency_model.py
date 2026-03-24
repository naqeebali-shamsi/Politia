from sqlalchemy import Column, Integer, String, Index, func, DateTime
from app.infrastructure.database.types import FlexibleJSON

from app.infrastructure.database.session import Base


class ConstituencyModel(Base):
    __tablename__ = "constituencies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)
    chamber = Column(String(50), nullable=False, index=True)
    constituency_type = Column(String(20), nullable=True)  # General, SC, ST
    geo_data = Column(FlexibleJSON, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_constituency_name_state", "name", "state", unique=True),
    )
