from pydantic import BaseModel

class SyncRequest(BaseModel):
    doc_id: str
    filename: str

class SyncResponse(BaseModel):
    job_id: str
    status: str
