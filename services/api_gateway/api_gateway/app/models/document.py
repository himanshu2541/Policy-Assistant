from pydantic import BaseModel
from typing import Dict, Any

class DocumentContext(BaseModel):
    page_content: str
    metadata: Dict[str, Any]

class DeleteVectorResponse(BaseModel):
    success: bool