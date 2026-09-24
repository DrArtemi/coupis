from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from coupis.api.routers import (
    occurrences_router,
    regions_router,
    species_router,
)
from coupis.api.schemas import HealthResponse
from coupis.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="Coupis API",
        version="0.1.0",
        description="API for biodiversity occurrence exploration.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    async def health() -> HealthResponse:
        return HealthResponse(status="ok")

    api_v1 = APIRouter(prefix="/api/v1")
    api_v1.include_router(occurrences_router)
    api_v1.include_router(regions_router)
    api_v1.include_router(species_router)
    app.include_router(api_v1)
    return app


app = create_app()
