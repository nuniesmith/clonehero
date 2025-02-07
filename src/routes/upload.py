from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Request, Depends
import os
import shutil
import tempfile
from loguru import logger
from src.services.content_utils import extract_content
from typing import Dict, Any

router = APIRouter()

# Allowed content types (for validation)
ALLOWED_CONTENT_TYPES = {"songs", "backgrounds"}

@router.post("/upload_content/", summary="Upload Clone Hero Content", tags=["Upload"])
async def upload_content(
    request: Request,
    file: UploadFile = File(...),
    content_type: str = Form(...)
) -> Dict[str, Any]:
    """
    Upload a file (archive or single) for any kind of Clone Hero content.

    The uploaded file is saved to a temporary location, then processed using
    the extract_content function based on the provided content_type. The result
    of the extraction is returned as JSON.

    Parameters:
        - request: The incoming request object (used for logging client info).
        - file: The file to upload.
        - content_type: The type of content (e.g., "songs", "backgrounds").

    Returns:
        A dictionary with the result of the content extraction.
    """

    # Validate content type
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid content type.")

    # Use a safer temp directory
    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, file.filename)

    logger.info(
        f"Received upload from {request.client.host} for content_type={content_type}, file={file.filename}"
    )

    try:
        # Save the uploaded file to a temporary location
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process the file
        result = extract_content(temp_file_path, content_type)

        if "error" in result:
            logger.error(f"Extraction error for {file.filename}: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except Exception as e:
        logger.exception(f"Error processing file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)