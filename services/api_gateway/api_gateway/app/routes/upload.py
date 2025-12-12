from fastapi import APIRouter, File, UploadFile, HTTPException
import os
import shutil
from shared.config import config
import logging
from pathlib import Path

logger = logging.getLogger("API-Gateway.Routes.Upload")

router = APIRouter()


@router.post("/")
async def upload_document(file: UploadFile = File(...)):
    """
    Uploads document
    """
    logger.info(f"Received upload request for file: {file.filename}")
    try:
        filename = file.filename or ""
        logger.info(f"Processing upload for filename: {filename}")
        
        os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    
        file_location = Path(config.UPLOAD_DIR) / filename
        logger.info(f"Saving file to: {file_location}")

        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File saved successfully to {file_location}")

        return {
            "status": "success",
            "doc_id": filename, # Using filename as doc_id for simplicity
            "path": str(file_location),
        }
    except Exception as e:
        logger.error(f"Upload failed for file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
