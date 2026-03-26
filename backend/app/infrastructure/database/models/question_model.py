from sqlalchemy import (
    Column, Integer, String, Text, Date, ForeignKey, Index, func, DateTime,
)
from sqlalchemy.orm import relationship

from app.infrastructure.database.session import Base


class QuestionModel(Base):
    __tablename__ = "question_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    politician_id = Column(
        Integer,
        ForeignKey("politicians.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    term_number = Column(Integer, nullable=True, index=True)
    question_date = Column(Date, nullable=True)
    ministry = Column(String(255), nullable=True, index=True)
    question_type = Column(String(50), nullable=True)  # Starred / Unstarred
    question_title = Column(Text, nullable=True)
    question_text = Column(Text, nullable=True)
    answer_text = Column(Text, nullable=True)
    source_url = Column(String(500), nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    politician = relationship("PoliticianModel", back_populates="questions")

    __table_args__ = (
        Index("ix_question_politician_term", "politician_id", "term_number"),
        Index("ix_question_date", "question_date"),
        Index("ix_question_ministry_type", "ministry", "question_type"),
    )
