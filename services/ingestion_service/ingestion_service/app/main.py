from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from shared.config import config as settings
import os, shutil

app = FastAPI(title="Ingestion Service")

DATA_DIR = os.environ.get("INGEST_DATA_DIR") or "/data/uploads"
os.makedirs(DATA_DIR, exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Welcome to the Ingestion Service"}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "ingestion_service"}

@app.post("/admin/upload")
async def upload(file: UploadFile = File(...)):
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    dest = os.path.join(DATA_DIR, filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"filename": filename}

class SyncRequest(BaseModel):
    filename: str
    document_id: str

@app.post("/admin/sync")
async def sync(req: SyncRequest):
    filepath = os.path.join(DATA_DIR, req.filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return {"status": "ingestion scheduled", "filename": req.filename, "document_id": req.document_id}

class DeleteVectorsRequest(BaseModel):
    document_id: str

@app.delete("/admin/vectors")
async def delete_vectors(req: DeleteVectorsRequest):
    return {"status": "vectors deleted", "document_id": req.document_id}