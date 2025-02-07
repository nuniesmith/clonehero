from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from loguru import logger
from pydantic import BaseModel, HttpUrl
import os
import uuid
import shutil
import aiofiles
import tempfile
from typing import Dict, Any
import requests
from src.services.content_utils import extract_content
from src.services.song_manager import list_all_songs

router = APIRouter()

class URLDownloadRequest(BaseModel):
    url: HttpUrl  # Ensures valid URLs

# Allowed extensions
ALLOWED_EXTENSIONS = {".zip", ".rar"}
MAX_FILE_SIZE_MB = 100  # Limit max file upload size to prevent crashes

def get_temp_file(file_name: str) -> str:
    """Returns a secure temp file path in the system temp directory."""
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, f"{uuid.uuid4().hex}_{file_name}")

def validate_file_extension(file_name: str):
    """Ensure the uploaded/downloaded file has a valid extension"""
    ext = os.path.splitext(file_name)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file extension: {ext}")

async def validate_file_size(file: UploadFile):
    """Check if uploaded file exceeds the allowed size limit"""
    file.file.seek(0, os.SEEK_END)
    size_in_mb = file.file.tell() / (1024 * 1024)
    file.file.seek(0)  # Reset file pointer for reading later

    if size_in_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=413, detail=f"File too large (max {MAX_FILE_SIZE_MB} MB)")

@router.post("/upload/", summary="Upload Song Archive", tags=["Songs"])
async def upload_song(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload an archive (zip/rar) for songs.
    
    The uploaded file is saved to a temporary location, processed by extracting its content,
    and the result is returned.
    """
    validate_file_extension(file.filename)
    await validate_file_size(file)  # Ensure file isn't too large

    temp_file_path = get_temp_file(file.filename)
    logger.info(f"Uploading file: {file.filename} for SONGS")

    try:
        async with aiofiles.open(temp_file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # Read in 1MB chunks
                await buffer.write(chunk)

        logger.info(f"File saved temporarily at: {temp_file_path}")
        result = extract_content(temp_file_path, "songs")
        return result

    except OSError as e:
        logger.exception(f"File system error while processing {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="File system error")
    
    except Exception as e:
        logger.exception(f"Error uploading file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@router.post("/download/", summary="Download and Extract Song Archive", tags=["Songs"])
async def download_and_extract(request: URLDownloadRequest) -> Dict[str, Any]:
    """
    Download an archive (zip/rar) from a provided URL, save it temporarily,
    process it by extracting its content, and return the result.
    """
    file_name = request.url.path.split("/")[-1]  # Extract filename from URL
    validate_file_extension(file_name)

    temp_file_path = get_temp_file(file_name)
    logger.info(f"Downloading file from: {request.url}")

    try:
        with requests.get(request.url, stream=True, timeout=30) as response:
            response.raise_for_status()

            async with aiofiles.open(temp_file_path, "wb") as f:
                async for chunk in response.iter_content(chunk_size=8192):  # Use async file writing
                    await f.write(chunk)

        logger.info(f"File downloaded to: {temp_file_path}")
        result = extract_content(temp_file_path, "songs")
        return result

    except requests.Timeout:
        logger.exception(f"Download timed out: {request.url}")
        raise HTTPException(status_code=504, detail="Download timed out")

    except requests.RequestException as e:
        logger.exception(f"Error downloading from {request.url}: {e}")
        raise HTTPException(status_code=500, detail="Download failed")

    except OSError as e:
        logger.exception(f"File system error while saving {file_name}: {e}")
        raise HTTPException(status_code=500, detail="File system error")

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@router.get("/songs/", summary="List All Songs", tags=["Songs"])
async def list_songs() -> Dict[str, Any]:
    """
    List all stored songs (including metadata).
    """
    try:
        songs = list_all_songs()
        return {"total": len(songs), "songs": songs}

    except Exception as e:
        logger.exception("Error listing songs")
        raise HTTPException(status_code=500, detail="Failed to fetch songs")