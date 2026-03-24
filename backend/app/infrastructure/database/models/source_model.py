from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Index, func,
)

from app.infrastructure.database.session import Base


class SourceModel(Base):
    __tablename__ = "source_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(String(100), nullable=False, index=True)
    url = Column(String(1000), nullable=False)
    snapshot_url = Column(String(1000), nullable=True)
    checksum = Column(String(64), nullable=True, index=True)
    content_type = Column(String(20), nullable=True)
    fetch_timestamp = Column(DateTime, server_default=func.now())
    parse_status = Column(String(20), nullable=False, default="pending", index=True)
    parser_version = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    ingestion_batch_id = Column(String(100), nullable=True, index=True)

    __table_args__ = (
        Index("ix_source_name_status", "source_name", "parse_status"),
    )
