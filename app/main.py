from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime

from .db import SessionLocal, Job, Base, engine
from .providers import generate_script, tts_elevenlabs_or_texttone, render_wave_video
from .util import contains_phi
from .downloads import router as downloads_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# create DB tables on boot (simple and fine for MVP)
Base.metadata.create_all(engine)

class CreateJob(BaseModel):
    project_id: str | None = None
    topic: str
    audience: str = "patients"
    length_sec: int = Field(ge=10, le=120)
    tone: str = "clear, empathetic"
    style: str = "waveform + captions"
    voice_id: str | None = None
    provider: str = "ffmpeg"
    block_phi: bool = True

@app.post("/api/jobs")
async def create_job(payload: CreateJob):
    if payload.block_phi and contains_phi(payload.topic):
        raise HTTPException(400, detail="PHI detected in prompt. Remove identifiers.")
    db = SessionLocal()
    job = Job(
        id=str(uuid4()), project_id=payload.project_id, status="generating",
        input_prompt=payload.topic, duration_sec=payload.length_sec,
        voice_id=payload.voice_id or "female_en_us_01", provider=payload.provider,
        created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    )
    db.add(job); db.commit()
    try:
        script = generate_script(payload.topic, audience=payload.audience, tone=payload.tone)
        job.script_text = script; db.commit()
        audio_path = await tts_elevenlabs_or_texttone(script, job.voice_id)
        video_path = render_wave_video(audio_path, script, duration_sec=payload.length_sec)
        job.video_url = f"file://{video_path}"
        job.status = "completed"; job.updated_at = datetime.utcnow(); db.commit()
    except Exception as e:
        job.status = "failed"; job.error = str(e); job.updated_at = datetime.utcnow(); db.commit()
        raise HTTPException(500, detail=str(e))
    return {"id": job.id, "status": job.status}

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    db = SessionLocal(); job = db.get(Job, job_id)
    if not job: raise HTTPException(404, "Job not found")
    return {
        "id": job.id, "status": job.status, "provider": job.provider,
        "video_url": job.video_url, "script_text": job.script_text,
        "error": job.error, "updated_at": job.updated_at.isoformat() if job.updated_at else None
    }

app.include_router(downloads_router, prefix="/api")
