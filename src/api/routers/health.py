from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "osint-research"}


@router.get("/")
async def root():
    return {
        "name": "OSINT Research API",
        "version": "0.1.0",
        "docs": "/docs",
    }
