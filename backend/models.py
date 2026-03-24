from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Politician(Base):
    __tablename__ = 'politicians'
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True, nullable=False)
    photo_url = Column(String, nullable=True)
    current_office = Column(String, nullable=True) # e.g. MP, MLA
    current_chamber = Column(String, nullable=True)
    party = Column(String, nullable=True)
    state = Column(String, nullable=True)
    last_updated = Column(DateTime, nullable=True)
    
    # Relationships
    offices = relationship("Office", back_populates="politician")
    scores = relationship("ScoreRecord", back_populates="politician")
    activities = relationship("ActivityRecord", back_populates="politician")
    disclosures = relationship("DisclosureRecord", back_populates="politician")

class Office(Base):
    __tablename__ = 'offices'
    id = Column(Integer, primary_key=True, index=True)
    politician_id = Column(Integer, ForeignKey('politicians.id'))
    title = Column(String, nullable=False) # MP
    chamber = Column(String, nullable=False) # Lok Sabha, Rajya Sabha
    term_start = Column(DateTime, nullable=True)
    term_end = Column(DateTime, nullable=True)
    active_status = Column(Boolean, default=True)
    
    politician = relationship("Politician", back_populates="offices")
    
class Constituency(Base):
    __tablename__ = 'constituencies'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    state = Column(String, nullable=False)
    chamber = Column(String, nullable=False)

class ElectionRecord(Base):
    __tablename__ = 'election_records'
    id = Column(Integer, primary_key=True, index=True)
    politician_id = Column(Integer, ForeignKey('politicians.id'))
    constituency_id = Column(Integer, ForeignKey('constituencies.id'))
    election_year = Column(Integer, nullable=False)
    party = Column(String, nullable=False)
    result = Column(String, nullable=False) # Won, Lost
    votes = Column(Integer, nullable=True)

class ActivityRecord(Base):
    __tablename__ = 'activity_records'
    id = Column(Integer, primary_key=True, index=True)
    politician_id = Column(Integer, ForeignKey('politicians.id'))
    session_name = Column(String, nullable=True)
    attendance_count = Column(Integer, default=0)
    debates_count = Column(Integer, default=0)
    questions_count = Column(Integer, default=0)
    
    politician = relationship("Politician", back_populates="activities")

class DisclosureRecord(Base):
    __tablename__ = 'disclosure_records'
    id = Column(Integer, primary_key=True, index=True)
    politician_id = Column(Integer, ForeignKey('politicians.id'))
    assets = Column(Float, default=0.0)
    liabilities = Column(Float, default=0.0)
    criminal_cases = Column(Integer, default=0)
    filing_year = Column(Integer, nullable=False)
    
    politician = relationship("Politician", back_populates="disclosures")

class ScoreRecord(Base):
    __tablename__ = 'score_records'
    id = Column(Integer, primary_key=True, index=True)
    politician_id = Column(Integer, ForeignKey('politicians.id'))
    overall_score = Column(Float, nullable=False)
    participation_score = Column(Float, nullable=False)
    disclosure_score = Column(Float, nullable=False)
    integrity_risk_adjustment = Column(Float, nullable=False)
    formula_version = Column(String, nullable=False)
    computed_at = Column(DateTime, nullable=False)
    
    politician = relationship("Politician", back_populates="scores")

class SourceRecord(Base):
    __tablename__ = 'source_records'
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    document_snapshot = Column(Text, nullable=True)
    checksum = Column(String, nullable=True)
    fetch_timestamp = Column(DateTime, nullable=False)
    parse_status = Column(String, nullable=False)
