from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os

app = FastAPI()

BASE_PATH = os.getenv("SIMULATIONS_OUT_DIR", "simulations_storage")

def find_job_folder(job_id: str):
    for tank_folder in os.listdir(BASE_PATH):
        folder = os.path.join(BASE_PATH, tank_folder, f"{job_id}_cache")
        if os.path.exists(folder):
            return folder
    return None

@app.get("/cache/{job_id}/metadata")
def get_metadata(job_id: str):  
    
    folder = find_job_folder(job_id)
    if not folder:
        raise HTTPException(404, "job not found")

    meta = os.path.join(folder, "index.json")
    return FileResponse(meta, media_type="application/json")

@app.get("/cache/{job_id}/chunk/{n}")
def get_chunk(job_id: str, n: int):
    folder = find_job_folder(job_id)
    if not folder:
        raise HTTPException(404, "job not found")

    chunk = os.path.join(folder, f"chunk_{n}.json")
    if not os.path.exists(chunk):
        raise HTTPException(404, "chunk not found")

    return FileResponse(chunk, media_type="application/json")

@app.get("/health")
def health():
    return {"status": "ok"}
