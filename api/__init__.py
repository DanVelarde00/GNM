import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import files, search, chat, processor, action_items, trackers, submit, weekly_reports, otter
from api.services.process_manager import ProcessManager
from api.services import search_service
import config


def create_app() -> FastAPI:
    app = FastAPI(title="GNM Dashboard API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(files.router, prefix="/api/files", tags=["files"])
    app.include_router(search.router, prefix="/api/search", tags=["search"])
    app.include_router(action_items.router, prefix="/api/action-items", tags=["action-items"])
    app.include_router(trackers.router, prefix="/api/trackers", tags=["trackers"])
    app.include_router(submit.router, prefix="/api/submit", tags=["submit"])
    app.include_router(processor.router, prefix="/api/processor", tags=["processor"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(weekly_reports.router, prefix="/api/weekly-reports", tags=["weekly-reports"])
    app.include_router(otter.router, prefix="/api/otter", tags=["otter"])

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.on_event("startup")
    async def startup():
        ProcessManager.instance().start()
        search_service.build_full_index()
        if config.OTTER_MCP_URL and config.OTTER_MCP_TOKEN:
            asyncio.create_task(_otter_poll_loop())

    @app.on_event("shutdown")
    async def shutdown():
        ProcessManager.instance().stop()

    return app


async def _otter_poll_loop():
    from api.services import otter_service
    while True:
        await asyncio.sleep(config.OTTER_POLL_INTERVAL)
        try:
            new_files = await asyncio.to_thread(otter_service.pull_new_transcripts)
            if new_files:
                print(f"[Otter] Pulled {len(new_files)} new transcript(s): {[f.name for f in new_files]}")
        except Exception as e:
            print(f"[Otter] Poll error: {e}")
