# backend/database.py

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

engine = create_engine("sqlite:///./secure_rag.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class QueryLog(Base):
    __tablename__ = "query_logs"
    id          = Column(Integer, primary_key=True)
    query       = Column(String)
    strategy    = Column(String)
    answer      = Column(String)
    time_ms     = Column(Float)
    chunks_used = Column(Integer)
    created_at  = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
