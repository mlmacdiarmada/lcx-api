from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from .db import SessionLocal, Job

router = APIRouter()

@router.get("/download/{job_id}")
def download(job_id: str):
    db = SessionLocal(); job = db.get(Job, job_id)
    if not job or not job.video_url: raise HTTPException(404, "Not found")
    if not job.video_url.startswith("file://"):
        raise HTTPException(400, "Hosted externally; use external URL.")
    path = job.video_url.replace("file://","")
    return FileResponse(path, media_type="video/mp4", filename=f"{job_id}.mp4")
