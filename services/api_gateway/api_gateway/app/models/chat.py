from pydantic import BaseModel
from api_gateway.app.models.document import DocumentContext
from typing import List


class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    answer: str
    contexts: List[DocumentContext]
