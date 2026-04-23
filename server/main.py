from typing import Any, Optional, Union

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    from server.agent_card import AGENT_CARD, validate_card
    from server.handlers import handle_task
except ModuleNotFoundError:
    from agent_card import AGENT_CARD, validate_card
    from handlers import handle_task

app = FastAPI(title="Echo A2A Agent")


@app.get("/.well-known/agent.json")
async def get_agent_card():
    if not validate_card(AGENT_CARD):
        raise HTTPException(status_code=500, detail="Invalid agent card")
    return AGENT_CARD


@app.get("/health")
async def health():
    return {"status": "ok", "agent": AGENT_CARD["id"]}


class TextPart(BaseModel):
    type: str = "text"
    text: str


class FileContent(BaseModel):
    url: str
    mimeType: str


class FilePart(BaseModel):
    type: str = "file"
    file: FileContent


class Message(BaseModel):
    role: str
    parts: list[Union[TextPart, FilePart]] = Field(default_factory=list)


class TaskRequest(BaseModel):
    id: str
    sessionId: Optional[str] = None
    message: Message
    metadata: Optional[dict[str, Any]] = None


@app.post("/tasks/send")
async def send_task(request: TaskRequest):
    if not request.message.parts:
        raise HTTPException(status_code=400, detail="message.parts must not be empty")

    result_text = handle_task(request)

    return {
        "id": request.id,
        "status": {
            "state": "completed",
            "message": None
        },
        "artifacts": [
            {
                "index": 0,
                "name": "result",
                "parts": [
                    {"type": "text", "text": result_text}
                ]
            }
        ]
    }