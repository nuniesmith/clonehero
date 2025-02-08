import os
import shutil
import zipfile
import patoolib
import uuid
import tempfile
import asyncio
import aiofiles
from loguru import logger
from dotenv import load_dotenv
from typing import Dict, Any, List
from src.services.content_manager import organize_and_add_songs
from src.services.song_generator import process_song_file

# Load environment variables
load_dotenv()

# Base directory for Clone Hero content
CONTENT_BASE_DIR = os.getenv("CONTENT_BASE_DIR", "/app/data/clonehero_content").rstrip("/")

if not CONTENT_BASE_DIR:
    logger.warning("⚠️ CONTENT_BASE_DIR is not set in .env. Using default: /app/data/clonehero_content")

# Allowed content types
CONTENT_FOLDERS = {
    "backgrounds": "backgrounds",
    "colors": "colors",
    "highways": "highways",
    "songs": "songs",
    "temp": "temp",
}

def get_final_directory(content_type: str) -> str:
    """Return subfolder path for the given content_type, ensuring the directory exists."""
    subfolder = CONTENT_FOLDERS.get(content_type, content_type)
    final_dir = os.path.join(CONTENT_BASE_DIR, subfolder)
    
    try:
        os.makedirs(final_dir, exist_ok=True)
    except Exception as e:
        logger.exception(f"❌ Failed to create directory {final_dir}: {e}")
    
    return final_dir

async def process_extracted_songs(songs: List[dict]) -> List[dict]:
    """Process extracted songs asynchronously using the song processing service."""
    processed_songs = []
    
    for song in songs:
        song_path = song.get("folder_path")
        if song_path:
            logger.info(f"🎵 Processing extracted song: {song_path}")
            result = await asyncio.to_thread(process_song_file, song_path)
            song["processing_result"] = result
            processed_songs.append(song)
    
    return processed_songs

async def store_extracted_content(temp_extract_dir: str, content_type: str) -> Dict[str, Any]:
    """Move extracted content to the final directory asynchronously."""
    final_dir = get_final_directory(content_type)
    try:
        for item in os.listdir(temp_extract_dir):
            src_path = os.path.join(temp_extract_dir, item)
            dst_path = os.path.join(final_dir, item)

            if os.path.isdir(src_path):
                shutil.move(src_path, dst_path)  # Move directories instead of copying
            else:
                async with aiofiles.open(src_path, "rb") as src_file, aiofiles.open(dst_path, "wb") as dst_file:
                    await dst_file.write(await src_file.read())

        shutil.rmtree(temp_extract_dir, ignore_errors=True)  # Cleanup temp directory
        return {"message": f"✅ Stored extracted content in {final_dir}"}
    except Exception as e:
        logger.exception(f"❌ Error storing extracted content: {e}")
        return {"error": str(e)}

async def extract_archive(file_path: str, extract_dir: str, file_ext: str) -> Dict[str, Any]:
    """Extracts .zip or .rar archives to a specified directory asynchronously."""
    try:
        if file_ext == ".zip":
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
        elif file_ext == ".rar":
            await asyncio.wait_for(asyncio.to_thread(patoolib.extract_archive, file_path, outdir=extract_dir), timeout=300)
        else:
            logger.error(f"🚨 Unsupported file format: {file_path}")
            return {"error": "Unsupported file format"}
        
        return {"success": True}
    except asyncio.TimeoutError:
        logger.error(f"⏳ Extraction timeout for {file_path}")
        return {"error": "Extraction took too long"}
    except Exception as e:
        logger.exception(f"❌ Error extracting archive {file_path}: {e}")
        return {"error": str(e)}

async def extract_content(file_path: str, content_type: str) -> Dict[str, Any]:
    """
    Extracts an archive or moves a file to its designated folder.
    - For `songs`, processes `song.ini` and generates charts.
    - For `backgrounds`, `colors`, `highways`, stores extracted content in the final folder.
    """
    file_name = os.path.basename(file_path)
    base_name, ext = os.path.splitext(file_name)
    temp_extract_dir = os.path.join(tempfile.gettempdir(), f"extract_{uuid.uuid4().hex[:6]}")

    try:
        if ext.lower() in [".zip", ".rar"]:
            os.makedirs(temp_extract_dir, exist_ok=True)
            logger.info(f"📦 Extracting {file_path} to {temp_extract_dir}")

            extract_result = await extract_archive(file_path, temp_extract_dir, ext.lower())
            if "error" in extract_result:
                return extract_result

            os.remove(file_path)  # Delete original archive after extraction

            if content_type == "songs":
                songs = await asyncio.to_thread(organize_and_add_songs, temp_extract_dir)
                processed_songs = await process_extracted_songs(songs)
                shutil.rmtree(temp_extract_dir, ignore_errors=True)  # Cleanup temp dir
                return {"message": f"🎵 Processed {len(processed_songs)} song(s).", "songs": processed_songs}
            else:
                return await store_extracted_content(temp_extract_dir, content_type)

        else:
            final_dir = get_final_directory(content_type)
            dst_path = os.path.join(final_dir, file_name)

            if content_type == "songs":
                return {"error": "⚠️ Please upload a .zip or .rar file containing a song.ini"}

            async with aiofiles.open(file_path, "rb") as src_file, aiofiles.open(dst_path, "wb") as dst_file:
                await dst_file.write(await src_file.read())

            return {"message": f"✅ Stored file: {file_name}", "file": dst_path}

    except Exception as e:
        logger.exception(f"❌ Error processing {file_path}: {e}")
        return {"error": str(e)}
    finally:
        shutil.rmtree(temp_extract_dir, ignore_errors=True)  # Cleanup temp dir even on failure