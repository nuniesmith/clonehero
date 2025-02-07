import configparser
import uuid
import shutil
from pathlib import Path
from loguru import logger
from typing import List
from src.services import content_utils
from src.database import get_connection
import psycopg2
from psycopg2 import errors
from psycopg2.extras import Json, DictCursor

OPTIONAL_FIELDS = [
    "genre", "year", "album_track", "playlist_track", "charter", "icon",
    "diff_guitar", "diff_rhythm", "diff_bass", "diff_guitar_coop", "diff_drums",
    "diff_drums_real", "diff_guitarghl", "diff_bassghl", "diff_rhythm_ghl",
    "diff_guitar_coop_ghl", "diff_keys", "song_length", "preview_start_time",
    "video_start_time", "modchart", "loading_phrase", "delay"
]

def parse_song_ini(ini_path: Path):
    """Parse the song.ini file to retrieve mandatory and optional metadata."""
    config = configparser.ConfigParser()
    try:
        with ini_path.open("r", encoding="utf-8-sig") as f:
            config.read_file(f)
    except Exception as e:
        raise ValueError(f"Failed to read {ini_path}: {e}")

    if not config.has_section("song"):
        raise ValueError(f"Missing [song] section in {ini_path}")

    # Extract mandatory fields
    name = config.get("song", "name", fallback="Unknown Title").strip()
    artist = config.get("song", "artist", fallback="Unknown Artist").strip()
    album = config.get("song", "album", fallback="Unknown Album").strip()

    # Extract optional metadata
    metadata = {
        field: config.get("song", field).strip()
        for field in OPTIONAL_FIELDS if config.has_option("song", field)
    }

    return {
        "title": name,
        "artist": artist,
        "album": album,
        "metadata": metadata
    }

def add_song_to_db(title: str, artist: str, album: str, file_path: str, metadata: dict = None):
    """Insert a new song into PostgreSQL."""
    metadata = metadata or {}

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO songs (title, artist, album, file_path, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (title, artist, album, file_path, Json(metadata))
                )
                conn.commit()

        logger.success(f"Song added: {title} - {artist} ({album})")
    except errors.UniqueViolation:
        logger.warning(f"Duplicate song detected, skipping insert: {file_path}")
    except Exception as e:
        logger.exception(f"Error inserting song: {e}")

def organize_and_add_songs(temp_extract_dir: str) -> List[dict]:
    """
    Locate `song.ini` files, parse them, move folders to the final destination,
    and insert song details into the database.
    """
    songs_found = []
    temp_extract_dir = Path(temp_extract_dir)

    for ini_path in temp_extract_dir.rglob("song.ini"):
        try:
            parsed = parse_song_ini(ini_path)
        except Exception as e:
            logger.error(f"Failed to parse {ini_path}: {e}")
            continue

        title = parsed["title"]
        artist = parsed["artist"]
        album = parsed["album"]
        metadata = parsed["metadata"]

        # Define final storage path
        artist_dir = Path(content_utils.get_final_directory("songs")) / artist
        artist_dir.mkdir(parents=True, exist_ok=True)

        final_dir = artist_dir / title

        # Ensure uniqueness if folder already exists
        counter = 1
        while final_dir.exists():
            final_dir = artist_dir / f"{title}_{counter}"
            counter += 1

        # Move song folder
        shutil.move(str(ini_path.parent), str(final_dir))

        # Insert song details into DB
        add_song_to_db(title, artist, album, str(final_dir), metadata)

        songs_found.append({
            "title": title,
            "artist": artist,
            "album": album,
            "folder_path": str(final_dir),
            "metadata": metadata
        })

    return songs_found

def list_all_songs():
    """Fetch all songs from the database, including metadata."""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute("SELECT id, title, artist, album, file_path, metadata FROM songs ORDER BY id DESC")
                songs = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "artist": row["artist"],
                "album": row["album"],
                "file_path": row["file_path"],
                "metadata": row["metadata"] if row["metadata"] else {}
            }
            for row in songs
        ]
    except Exception as e:
        logger.exception(f"Error fetching songs: {e}")
        return []