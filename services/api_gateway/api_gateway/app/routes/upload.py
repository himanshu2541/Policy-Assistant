from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from api_gateway.core.dependencies import get_storage_service
from shared.interfaces import StorageProvider
from shared.config import config
import logging

logger = logging.getLogger("API-Gateway.Routes.Upload")

router = APIRouter()


@router.post("/")
async def upload_document(
    file: UploadFile = File(...),
    storage: StorageProvider = Depends(get_storage_service),
):
    """
    Uploads document
    """
    logger.info(f"Received upload request for file: {file.filename}")
    try:
        location = storage.save_file(file)
        return {
            "status": "success",
            "doc_id": file.filename,  # Using filename as doc_id for simplicity
            "path": str(location),
        }
    except Exception as e:
        logger.error(f"Upload failed for file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
