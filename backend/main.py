from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import List
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

import models
from database import engine, get_db

app = FastAPI(title="Politia MVP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://politia-mvp.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/api/politicians")
def search_politicians(q: str = "", state: str = None, party: str = None, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    query = db.query(models.Politician, models.ScoreRecord).outerjoin(
        models.ScoreRecord, models.ScoreRecord.politician_id == models.Politician.id
    )
    
    if q:
        query = query.filter(models.Politician.full_name.ilike(f"%{q}%"))
    if state:
        query = query.filter(models.Politician.state == state)
    if party:
        query = query.filter(models.Politician.party == party)
        
    results = query.offset(skip).limit(limit).all()
    
    out = []
    for p, s in results:
        out.append({
            "id": p.id,
            "full_name": p.full_name,
            "party": p.party,
            "state": p.state,
            "chamber": p.current_chamber,
            "score": s.overall_score if s else None
        })
    return out

@app.get("/api/politicians/{id}")
def get_politician(id: int, db: Session = Depends(get_db)):
    p = db.query(models.Politician).filter(models.Politician.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Politician not found")
        
    scores = db.query(models.ScoreRecord).filter(models.ScoreRecord.politician_id == p.id).first()
    
    return {
        "id": p.id,
        "full_name": p.full_name,
        "party": p.party,
        "state": p.state,
        "chamber": p.current_chamber,
        "last_updated": p.last_updated,
        "scores": {
            "overall": scores.overall_score if scores else None,
            "participation": scores.participation_score if scores else None,
            "disclosure": scores.disclosure_score if scores else None,
            "integrity_risk": scores.integrity_risk_adjustment if scores else None
        } if scores else None
    }

@app.get("/api/leaderboards")
def get_leaderboards(chamber: str = "Lok Sabha", limit: int = 10, db: Session = Depends(get_db)):
    politicians = db.query(models.Politician).filter(models.Politician.current_chamber == chamber).all()
    results = db.query(models.Politician, models.ScoreRecord).join(models.ScoreRecord, models.ScoreRecord.politician_id == models.Politician.id).filter(models.Politician.current_chamber == chamber).order_by(desc(models.ScoreRecord.overall_score)).limit(limit).all()
    
    out = []
    for p, s in results:
        out.append({
            "id": p.id,
            "full_name": p.full_name,
            "party": p.party,
            "state": p.state,
            "chamber": p.current_chamber,
            "score": s.overall_score
        })
    return out
