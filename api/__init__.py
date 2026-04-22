from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import files, search, chat, processor, action_items, trackers, submit, weekly_reports
from api.services.process_manager import ProcessManager
from api.services import search_service


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

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.on_event("startup")
    async def startup():
        ProcessManager.instance().start()
        search_service.build_full_index()

    @app.on_event("shutdown")
    async def shutdown():
        ProcessManager.instance().stop()

    return app
