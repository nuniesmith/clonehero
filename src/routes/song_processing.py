from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import aiofiles
from src.services.song_processing import process_song_file
from loguru import logger

router = APIRouter()

OUTPUT_DIR = Path("processed_songs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

async def save_uploaded_file(uploaded_file: UploadFile, destination: Path):
    """Asynchronously saves an uploaded file."""
    try:
        async with aiofiles.open(destination, "wb") as out_file:
            while chunk := await uploaded_file.read(1024 * 1024):  # Read in 1MB chunks
                await out_file.write(chunk)
    except Exception as e:
        logger.error(f"Error saving file {uploaded_file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Error saving file.")

@router.post("/process_song/")
async def process_song(file: UploadFile = File(...)):
    """Handles song uploads and processes them into Clone Hero format."""
    if not file.filename.lower().endswith((".mp3", ".ogg", ".wav", ".flac")):
        raise HTTPException(status_code=400, detail="Invalid file format. Supported formats: .mp3, .ogg, .wav, .flac")

    try:
        # Prevent filename conflicts
        file_path = OUTPUT_DIR / f"{Path(file.filename).stem}_{file.content_type.replace('/', '_')}.wav"

        logger.info(f"Saving uploaded song: {file.filename}")
        await save_uploaded_file(file, file_path)

        logger.info(f"Processing uploaded song: {file.filename}")
        result = process_song_file(str(file_path))

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "message": "Song processed successfully",
            "notes_chart": result["notes_chart"],
            "tempo": result["tempo"],
            "file_name": file.filename
        }
    except HTTPException:
        raise  # Re-raise known HTTP errors
    except Exception as e:
        logger.error(f"Unexpected error processing song {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during song processing.")