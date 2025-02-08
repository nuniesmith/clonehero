from src.database import get_connection
from loguru import logger
import psycopg2.extras  # For DictCursor
from pathlib import Path
from typing import List, Dict, Any, Optional


def get_all_songs(search_query: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """Retrieve songs from the database, optionally filtering by search query with pagination."""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                query = "SELECT id, title, artist, album, file_path, metadata FROM songs"
                params = []

                if search_query:
                    query += " WHERE title ILIKE %s OR artist ILIKE %s OR album ILIKE %s"
                    params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])

                query += " ORDER BY id DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                cursor.execute(query, params)
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
        logger.exception(f"Error fetching songs from database: {e}")
        return []


def delete_song_by_id(song_id: int) -> bool:
    """Delete a song from the database by its ID."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM songs WHERE id = %s RETURNING id", (song_id,))
                deleted = cursor.fetchone()
                conn.commit()

        return bool(deleted)
    except Exception as e:
        logger.exception(f"Error deleting song with ID {song_id}: {e}")
        return False