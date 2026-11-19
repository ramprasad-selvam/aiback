import logging

from fastapi import FastAPI

from .routes.claims import router as claims_router


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.INFO)
    app = FastAPI(
        title="Health Insurance Claims Processing API",
        version="0.1.0",
        description="LangGraph-based claim extraction, validation, and fraud analysis.",
    )
    app.include_router(claims_router, prefix="/api")

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "healthy"}

    @app.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        return {
            "health": "/health",
            "documentation": "/docs",
            "evaluate": "/api/claims/evaluate",
        }

    return app


app = create_app()
