from fastapi import FastAPI
from src.api_routers import farseer_api_router
from src.meta import title, description
from src.logger import log


def configure_app() -> FastAPI:
    farseer_app = FastAPI(title=title, description=description)
    farseer_app.include_router(farseer_api_router)

    return farseer_app


farseer_app = configure_app()
log.info("app configured")
