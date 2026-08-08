import logging

from fastapi import FastAPI

from app.core.config import get_settings
from app.api.v1.router import api_router
from app.db.init_db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.main")


def create_app() -> FastAPI:
    """
    Application factory. Keeps app creation isolated and testable.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description="API-based platform for cross-AI codebase context sharing.",
        version="0.1.0",
        debug=settings.DEBUG,
    )

    app.include_router(api_router, prefix="/api/v1")

    @app.on_event("startup")
    def on_startup() -> None:
        """
        Runs once when the app boots. Creates SQLite tables if they don't
        already exist. Fails loudly (crashes startup) if the DB can't be
        initialized, since running with a broken DB layer is worse than
        not starting at all.
        """
        logger.info("Initializing database...")
        init_db()
        logger.info("Startup complete.")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )
