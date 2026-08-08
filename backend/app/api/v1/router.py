from fastapi import APIRouter
from app.api.v1.routes import health, db_check, repositories, files, symbols

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(db_check.router)
api_router.include_router(repositories.router)
api_router.include_router(files.router)
api_router.include_router(symbols.router)
