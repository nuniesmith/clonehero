from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Request
import os
import aiofiles
import tempfile
from loguru import logger
from typing import Dict, Any
from src.services.content_utils import extract_content

router = APIRouter()

# Allowed content types
ALLOWED_CONTENT_TYPES = {"backgrounds", "colors", "highways"}
ALLOWED_EXTENSIONS = {".zip", ".rar", ".png", ".jpg"}
MAX_FILE_SIZE_MB = 100  # Limit max file size (e.g., 100MB)

def get_secure_temp_file(file_name: str) -> str:
    """Generate a secure temp file path to avoid overwrites."""
    temp_dir = tempfile.gettempdir()
    unique_file_name = f"{os.urandom(6).hex()}_{file_name}"  # Random prefix for uniqueness
    return os.path.join(temp_dir, unique_file_name)

def validate_file(file: UploadFile):
    """Ensure the uploaded file has a valid extension and does not exceed max size."""
    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file extension: {ext}")

    file.file.seek(0, os.SEEK_END)
    size_in_mb = file.file.tell() / (1024 * 1024)
    file.file.seek(0)  # Reset file pointer

    if size_in_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=413, detail=f"File too large (max {MAX_FILE_SIZE_MB}MB)")

@router.post("/upload_content/", summary="Upload Clone Hero Content (Backgrounds, Colors, Highways)", tags=["Upload"])
async def upload_content(
    request: Request,
    file: UploadFile = File(...),
    content_type: str = Form(...)
) -> Dict[str, Any]:
    """
    Upload an archive (zip/rar) or image (png/jpg) for Clone Hero visual content.

    The uploaded file is saved to a secure temporary location and processed by extract_content.

    Parameters:
    - file: The file to upload.
    - content_type: The type of content (e.g., "backgrounds", "colors", "highways").

    Returns:
    - A dictionary with the extraction result.
    """

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid content type: {content_type}")

    validate_file(file)
    temp_file_path = get_secure_temp_file(file.filename)

    logger.info(
        f"Received upload from {request.client.host} for content_type={content_type}, file={file.filename}"
    )

    try:
        async with aiofiles.open(temp_file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # Read in 1MB chunks
                await buffer.write(chunk)

        logger.info(f"File saved temporarily at: {temp_file_path}")
        result = extract_content(temp_file_path, content_type)

        if "error" in result:
            logger.error(f"Extraction error for {file.filename}: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except Exception as e:
        logger.exception(f"Error processing file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)