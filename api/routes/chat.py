import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.models.chat_models import ChatMessage, ChatRequest
from api.services import chat_service

router = APIRouter()


@router.websocket("/ws")
async def ws_chat(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_json()
            req = ChatRequest(**data)
            async for chunk in chat_service.stream_response(
                message=req.message,
                history=req.history,
                project_filter=req.project_filter,
            ):
                await ws.send_json(chunk)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
