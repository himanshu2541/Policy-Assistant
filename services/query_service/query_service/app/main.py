from fastapi import FastAPI, WebSocket
from shared.config import config as settings
from pydantic import BaseModel

app = FastAPI(title="Query Service")

@app.get("/")
async def root():
    return {"message": "Welcome to the Query Service"}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "query_service", "env": settings.ENV}

class ChatRequest(BaseModel):
    query: str

@app.post("/chat")
async def chat(req: ChatRequest):
    return {"answer": f"mock reply to: {req.query}"}

@app.websocket("/ws/chat")
async def ws_chat(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            msg = await ws.receive_text()
            await ws.send_json({"echo": msg})
    except Exception:
        await ws.close()
