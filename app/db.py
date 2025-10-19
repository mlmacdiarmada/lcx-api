import os
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.dialects.postgresql import JSONB

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://user:pass@host:5432/db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)
    project_id = Column(String, nullable=True)
    status = Column(String, default="queued")
    input_prompt = Column(Text)
    script_text = Column(Text, nullable=True)
    duration_sec = Column(Integer, default=45)
    voice_id = Column(String, nullable=True)
    provider = Column(String, default="ffmpeg")
    provider_job_id = Column(String, nullable=True)
    video_url = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    meta = Column(JSONB, nullable=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
