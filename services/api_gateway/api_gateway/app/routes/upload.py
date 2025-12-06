from fastapi import APIRouter, File, UploadFile, HTTPException
import os
import shutil
from shared.config import config
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Uploads a file to the shared volume so the RAG Worker can access it.
    Returns the doc_id (which is just the filename for now).
    """
    try:
        filename = file.filename or ""
        os.makedirs(config.UPLOAD_DIR, exist_ok=True)
        file_location = os.path.join(config.UPLOAD_DIR, filename)

        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {"status": "success", "doc_id": filename, "path": file_location}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
