import os
import shutil
import zipfile
import patoolib
import uuid
import tempfile
import asyncio
import aiofiles
from src.database import get_connection
from psycopg2.extras import DictCursor
from loguru import logger
from dotenv import load_dotenv
from typing import Dict, Any, List
from src.services.content_manager import process_and_store_content

# Load environment variables
load_dotenv()

CONTENT_BASE_DIR = os.getenv("CONTENT_BASE_DIR", "/app/data/clonehero_content").rstrip("/")

if not CONTENT_BASE_DIR:
    logger.warning("⚠️ CONTENT_BASE_DIR is not set in .env. Using default: /app/data/clonehero_content")

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


async def store_extracted_content(temp_extract_dir: str, content_type: str) -> Dict[str, Any]:
    """Move extracted content to the final directory asynchronously."""
    return await process_and_store_content(temp_extract_dir, content_type)


async def extract_archive(file_path: str, extract_dir: str, file_ext: str) -> Dict[str, Any]:
    """Extracts .zip or .rar archives to a specified directory asynchronously."""
    try:
        if file_ext == ".zip":
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
        elif file_ext == ".rar":
            await asyncio.to_thread(patoolib.extract_archive, file_path, outdir=extract_dir)
        else:
            logger.error(f"🚨 Unsupported file format: {file_path}")
            return {"error": "Unsupported file format"}

        return {"success": True}
    except Exception as e:
        logger.exception(f"❌ Error extracting archive {file_path}: {e}")
        return {"error": str(e)}


async def extract_content(file_path: str, content_type: str) -> Dict[str, Any]:
    """
    Extracts an archive or moves a file to its designated folder.
    - For `songs`, ensures song content is handled properly.
    - For `backgrounds`, `colors`, `highways`, moves extracted content.
    """
    file_name = os.path.basename(file_path)
    temp_extract_dir = os.path.join(tempfile.gettempdir(), f"extract_{uuid.uuid4().hex[:6]}")

    try:
        file_ext = os.path.splitext(file_name)[1].lower()

        if file_ext in [".zip", ".rar"]:
            os.makedirs(temp_extract_dir, exist_ok=True)
            logger.info(f"📦 Extracting {file_path} to {temp_extract_dir}")

            extract_result = await extract_archive(file_path, temp_extract_dir, file_ext)
            if "error" in extract_result:
                return extract_result

            os.remove(file_path)  # Delete original archive after extraction
            return await store_extracted_content(temp_extract_dir, content_type)

        # Handle direct file storage
        final_dir = get_final_directory(content_type)
        dst_path = os.path.join(final_dir, file_name)

        if content_type == "songs":
            return {"error": "⚠️ Please upload a .zip or .rar file containing a song.ini"}

        shutil.move(file_path, dst_path)
        return {"message": f"✅ Stored file: {file_name}", "file": dst_path}

    except Exception as e:
        logger.exception(f"❌ Error processing {file_path}: {e}")
        return {"error": str(e)}

    finally:
        shutil.rmtree(temp_extract_dir, ignore_errors=True)  # Cleanup temp dir even on failure


async def list_all_content() -> List[Dict[str, Any]]:
    """List all stored content (songs, backgrounds, highways, colors)."""
    try:
        conn = await asyncio.to_thread(get_connection)  # Ensure connection runs asynchronously
        async with conn:
            async with conn.cursor(cursor_factory=DictCursor) as cursor:
                await cursor.execute("SELECT * FROM songs")
                content = await cursor.fetchall()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "artist": row["artist"],
                "album": row["album"],
                "file_path": row["file_path"],
                "metadata": row["metadata"] if row["metadata"] else {}
            }
            for row in content
        ]
    except Exception as e:
        logger.exception(f"❌ Error listing content: {e}")
        return []  # Always return a list (consistent with function signature)