import os
import sys
import logging
from datetime import datetime

backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
sys.path.append(backend_path)

from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import Politician, Office, Constituency, ScoreRecord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_ingestion():
    logger.info("Starting ingestion process...")
    
    db: Session = SessionLocal()
    try:
        mock_mps = [
            {"full_name": "Rahul Gandhi", "party": "INC", "state": "Kerala", "constituency": "Wayanad", "chamber": "Lok Sabha", "participation_score": 85.0, "disclosure_score": 90.0, "integrity": 0.0},
            {"full_name": "Narendra Modi", "party": "BJP", "state": "Uttar Pradesh", "constituency": "Varanasi", "chamber": "Lok Sabha", "participation_score": 95.0, "disclosure_score": 98.0, "integrity": 0.0},
            {"full_name": "Shashi Tharoor", "party": "INC", "state": "Kerala", "constituency": "Thiruvananthapuram", "chamber": "Lok Sabha", "participation_score": 92.0, "disclosure_score": 88.0, "integrity": 0.0}
        ]
        
        for mp in mock_mps:
            existing = db.query(Politician).filter_by(full_name=mp["full_name"]).first()
            if not existing:
                p = Politician(
                    full_name=mp["full_name"],
                    party=mp["party"],
                    state=mp["state"],
                    current_chamber=mp["chamber"],
                    current_office="MP",
                    last_updated=datetime.utcnow()
                )
                db.add(p)
                db.flush() # get ID
                
                # Add constituency dummy
                c = Constituency(name=mp["constituency"], state=mp["state"], chamber=mp["chamber"])
                db.add(c)
                
                # Add score dummy to populate Frontend immediately
                overall = (mp["participation_score"] * 0.6) + (mp["disclosure_score"] * 0.25) - mp["integrity"]
                s = ScoreRecord(
                    politician_id=p.id,
                    overall_score=overall,
                    participation_score=mp["participation_score"],
                    disclosure_score=mp["disclosure_score"],
                    integrity_risk_adjustment=mp["integrity"],
                    formula_version="MVP-v0.1",
                    computed_at=datetime.utcnow()
                )
                db.add(s)
                logger.info(f"Added MP & scores: {mp['full_name']}")
            else:
                logger.info(f"MP already exists: {mp['full_name']}")
                
        db.commit()
        logger.info("Ingestion completed successfully.")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_ingestion()
