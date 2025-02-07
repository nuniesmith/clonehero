from fastapi import APIRouter, HTTPException
from loguru import logger

router = APIRouter()

@router.get("/health", summary="Health Check", tags=["Health"])
async def health_check():
    """
    Check the health of the API service.

    Returns:
        A JSON object with a 'status' key indicating the API is operational.
    """
    try:
        logger.info("Health check endpoint called.")
        return {"status": "ok"}
    except Exception as e:
        logger.exception("Health check failed")
        raise HTTPException(status_code=500, detail="Health check failed")