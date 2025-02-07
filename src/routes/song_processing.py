from fastapi import APIRouter, UploadFile, File, HTTPException
import os
from src.services.song_processing import process_song_file
from loguru import logger

router = APIRouter()

OUTPUT_DIR = "processed_songs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@router.post("/process_song/")
async def process_song(file: UploadFile = File(...)):
    """Handles song uploads and processes them into Clone Hero format."""
    try:
        file_path = os.path.join(OUTPUT_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        
        logger.info(f"Processing uploaded song: {file.filename}")
        result = process_song_file(file_path)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "message": "Song processed successfully",
            "notes_chart": result["notes_chart"],
            "tempo": result["tempo"],
            "file_name": file.filename
        }
    except Exception as e:
        logger.error(f"Failed to process song {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))