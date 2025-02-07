import os
import shutil
import zipfile
import patoolib
from loguru import logger
from src.services.song_upload import organize_and_add_songs
from src.services.song_processing import process_song_file
from typing import Dict, Any
import uuid

CONTENT_BASE_DIR = "/app/data/clonehero_content"

# Map content_type => subfolder
CONTENT_FOLDERS = {
    "backgrounds":       "backgrounds",
    "colors":            "colors",
    "highways":          "highways",
    "songs":             "songs",
    "temp":              "temp",
}


def get_final_directory(content_type: str) -> str:
    """Return subfolder path for the given content_type, ensuring the directory exists."""
    subfolder = CONTENT_FOLDERS.get(content_type, content_type)
    final_dir = os.path.join(CONTENT_BASE_DIR, subfolder)
    os.makedirs(final_dir, exist_ok=True)
    return final_dir


def process_extracted_songs(songs: list) -> list:
    """Process extracted songs with song processing service."""
    processed_songs = []
    for song in songs:
        song_path = song.get("folder_path")
        if song_path:
            logger.info(f"Processing extracted song: {song_path}")
            result = process_song_file(song_path)
            song["processing_result"] = result
            processed_songs.append(song)
    return processed_songs


def store_extracted_content(temp_extract_dir: str, content_type: str) -> Dict[str, Any]:
    """Store extracted content in the final directory."""
    final_dir = get_final_directory(content_type)
    try:
        for item in os.listdir(temp_extract_dir):
            src_path = os.path.join(temp_extract_dir, item)
            dst_path = os.path.join(final_dir, item)
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, dst_path)
        return {"message": f"Stored extracted content in {final_dir}"}
    except Exception as e:
        logger.exception(f"Error storing extracted content from {temp_extract_dir} to {final_dir}: {e}")
        return {"error": str(e)}

def extract_content(file_path: str, content_type: str) -> Dict[str, Any]:
    """
    If file is .zip/.rar, extract to a temporary directory, then:
      - If content_type is 'songs', process song.ini files & generate charts.
      - Else, store the extracted items in the final folder.
    If not an archive, just move it directly.
    """
    from_path = os.path.basename(file_path)
    base_name, ext = os.path.splitext(from_path)
    temp_extract_dir = os.path.join("/tmp", f"extract_{uuid.uuid4().hex[:6]}")

    if ext.lower() in [".zip", ".rar"]:
        os.makedirs(temp_extract_dir, exist_ok=True)
        logger.info(f"Extracting {file_path} to {temp_extract_dir}")
        try:
            if ext.lower() == ".zip":
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    zip_ref.extractall(temp_extract_dir)
            elif ext.lower() == ".rar":
                patoolib.extract_archive(file_path, outdir=temp_extract_dir)
            else:
                logger.error(f"Unsupported file format: {from_path}")
                return {"error": "Unsupported file format"}

            os.remove(file_path)  # Remove the original archive file

            if content_type == "songs":
                songs = organize_and_add_songs(temp_extract_dir)
                processed_songs = process_extracted_songs(songs)
                return {"message": f"Processed {len(processed_songs)} song(s).", "songs": processed_songs}
            else:
                return store_extracted_content(temp_extract_dir, content_type)
        except Exception as e:
            logger.exception(f"Error extracting file {file_path}: {e}")
            return {"error": str(e)}
        finally:
            shutil.rmtree(temp_extract_dir, ignore_errors=True)
    else:
        final_dir = get_final_directory(content_type)
        dst_path = os.path.join(final_dir, from_path)
        if content_type == "songs":
            return {"error": "Please upload a .zip or .rar file containing a song.ini"}
        try:
            shutil.move(file_path, dst_path)
            return {"message": f"Stored file: {from_path}", "file": dst_path}
        except Exception as e:
            logger.exception(f"Error moving file {file_path} to {dst_path}: {e}")
            return {"error": str(e)}