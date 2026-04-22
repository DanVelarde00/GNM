import asyncio
import json
from queue import Queue

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.services.process_manager import ProcessManager

router = APIRouter()


@router.get("/status")
def get_status():
    return ProcessManager.instance().get_status()


@router.post("/start")
def start_processor():
    ProcessManager.instance().start()
    return ProcessManager.instance().get_status()


@router.post("/stop")
def stop_processor():
    ProcessManager.instance().stop()
    return ProcessManager.instance().get_status()


@router.post("/restart")
def restart_processor():
    ProcessManager.instance().restart()
    return ProcessManager.instance().get_status()


@router.get("/log")
def get_log(n: int = 100):
    return ProcessManager.instance().get_recent_log(n)


@router.websocket("/ws")
async def ws_processor_log(ws: WebSocket):
    await ws.accept()
    pm = ProcessManager.instance()
    q: Queue = Queue()
    pm.subscribe(q)

    # Send recent history first
    for entry in pm.get_recent_log(50):
        await ws.send_json(entry)

    try:
        while True:
            await asyncio.sleep(0.3)
            while not q.empty():
                entry = q.get_nowait()
                await ws.send_json(entry)
    except WebSocketDisconnect:
        pass
    finally:
        pm.unsubscribe(q)
