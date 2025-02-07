from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from loguru import logger
from pydantic import BaseModel
import os
import shutil
import requests
import tempfile
from typing import Dict, Any
from src.services.content_utils import extract_content
from src.services.song_upload import list_all_songs

router = APIRouter()

class URLDownloadRequest(BaseModel):
    url: str

# Allowed extensions
ALLOWED_EXTENSIONS = {".zip", ".rar"}

def get_temp_file(file_name: str) -> str:
    """Returns a secure temp file path"""
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, file_name)

def validate_file_extension(file_name: str):
    """Ensure the uploaded/downloaded file has a valid extension"""
    ext = os.path.splitext(file_name)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file extension: {ext}")

@router.post("/upload/", summary="Upload Song Archive", tags=["Songs"])
async def upload_song(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    (LEGACY) Upload an archive (zip/rar) for songs only.
    
    The uploaded file is saved to a temporary location, processed by extracting its content,
    and the result is returned.
    """
    validate_file_extension(file.filename)

    temp_file_path = get_temp_file(file.filename)
    logger.info(f"Uploading file: {file.filename} for SONGS")

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

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


@router.post("/download/", summary="Download Song Archive", tags=["Songs"])
async def download_and_extract(request: URLDownloadRequest) -> Dict[str, Any]:
    """
    (LEGACY) Download an archive (zip/rar) for songs only.
    
    The endpoint downloads the file from the provided URL, saves it temporarily,
    processes it by extracting its content, and returns the result.
    """
    file_name = request.url.split("/")[-1]
    validate_file_extension(file_name)

    temp_file_path = get_temp_file(file_name)
    logger.info(f"Downloading file: {request.url}")

    try:
        with requests.get(request.url, stream=True, timeout=15) as response:
            response.raise_for_status()
            with open(temp_file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=16384):  # Use larger chunk for efficiency
                    f.write(chunk)

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
async def list_songs() -> Any:
    """
    List all stored songs (including metadata).
    """
    try:
        songs = list_all_songs()
        if isinstance(songs, list):
            return songs  # Ensure it returns a list, not a dict
        elif isinstance(songs, dict) and "songs" in songs:
            return songs["songs"]
        else:
            logger.error("Unexpected songs data format.")
            raise HTTPException(status_code=500, detail="Unexpected data format from database")
    except Exception as e:
        logger.exception("Error listing songs")
        raise HTTPException(status_code=500, detail="Failed to fetch songs")