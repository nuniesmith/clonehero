import configparser
import uuid
import os
import shutil
from loguru import logger
from typing import List
from src.services import content_utils
from src.database import get_connection
import psycopg2
from psycopg2 import errors
from psycopg2.extras import Json

OPTIONAL_FIELDS = [
    "genre",
    "year",
    "album_track",
    "playlist_track",
    "charter",
    "icon",
    "diff_guitar",
    "diff_rhythm",
    "diff_bass",
    "diff_guitar_coop",
    "diff_drums",
    "diff_drums_real",
    "diff_guitarghl",
    "diff_bassghl",
    "diff_rhythm_ghl",
    "diff_guitar_coop_ghl",
    "diff_keys",
    "song_length",
    "preview_start_time",
    "video_start_time",
    "modchart",
    "loading_phrase",
    "delay"
]

def parse_song_ini(ini_path: str):
    """
    Parse the song.ini file to retrieve mandatory + optional metadata.
    """
    config = configparser.ConfigParser()
    with open(ini_path, "r", encoding="utf-8-sig") as f:
        config.read_file(f)

    if not config.has_section("song"):
        raise ValueError(f"Missing [song] section in {ini_path}")

    # Mandatory
    name = config.get("song", "name", fallback="Unknown Title").strip()
    artist = config.get("song", "artist", fallback="Unknown Artist").strip()
    album = config.get("song", "album", fallback="Unknown Album").strip()

    # Build metadata dict for optional fields
    metadata = {}
    for field in OPTIONAL_FIELDS:
        if config.has_option("song", field):
            raw_val = config.get("song", field).strip()
            metadata[field] = raw_val

    return {
        "title": name,
        "artist": artist,
        "album": album,
        "metadata": metadata
    }

def add_song_to_db(
    title: str,
    artist: str,
    album: str,
    file_path: str,
    metadata: dict = None
):
    """Insert a new song into Postgres, including optional metadata in JSON."""
    if metadata is None:
        metadata = {}

    try:
        conn = get_connection()
        cursor = conn.cursor()

        insert_sql = """
            INSERT INTO songs (title, artist, album, file_path, metadata)
            VALUES (%s, %s, %s, %s, %s)
        """
        # Wrap metadata with Json() to adapt the dictionary for PostgreSQL
        cursor.execute(insert_sql, (title, artist, album, file_path, Json(metadata)))
        conn.commit()

        cursor.close()
        conn.close()
        logger.success(f"Song added to database: {title} - {artist} ({album})")
    except errors.UniqueViolation:
        logger.warning(f"Duplicate song detected, skipping DB insert: {file_path}")
    except Exception as e:
        logger.exception(f"Error inserting song into PostgreSQL: {str(e)}")

def organize_and_add_songs(temp_extract_dir: str) -> List[dict]:
    """
    Find any song.ini files, parse them, move folders to
    /app/clonehero_content/songs/<artist>/<title>/, then insert in DB.
    """
    songs_found = []

    for root, dirs, files in os.walk(temp_extract_dir):
        if "song.ini" in files:
            ini_path = os.path.join(root, "song.ini")
            try:
                parsed = parse_song_ini(ini_path)
            except Exception as e:
                logger.error(f"Failed to parse {ini_path}: {e}")
                continue

            title = parsed["title"]
            artist = parsed["artist"]
            album = parsed["album"]
            metadata = parsed["metadata"]

            # Construct final path
            artist_dir = os.path.join(content_utils.get_final_directory("songs"), artist)
            os.makedirs(artist_dir, exist_ok=True)

            final_dir = os.path.join(artist_dir, title)
            if os.path.exists(final_dir):
                final_dir += f"_{uuid.uuid4().hex[:6]}"

            # Move the entire folder containing song.ini
            shutil.move(root, final_dir)

            # Insert into DB
            add_song_to_db(title, artist, album, final_dir, metadata)

            songs_found.append({
                "title": title,
                "artist": artist,
                "album": album,
                "folder_path": final_dir,
                "metadata": metadata
            })

    return songs_found

def list_all_songs():
    """
    Fetch all songs from the DB, including metadata.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, artist, album, file_path, metadata FROM songs ORDER BY id DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        output = []
        for row in rows:
            output.append({
                "id": row[0],
                "title": row[1],
                "artist": row[2],
                "album": row[3],
                "file_path": row[4],
                "metadata": row[5] if row[5] else {}
            })
        return output

    except Exception as e:
        logger.exception(f"Error fetching songs from DB: {e}")
        raise