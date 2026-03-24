import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'politia.db'))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
