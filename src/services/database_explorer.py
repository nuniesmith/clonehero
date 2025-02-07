from src.database import get_connection
from loguru import logger
import psycopg2.extras  # For DictCursor

def get_all_songs(search_query: str = None, limit: int = 50, offset: int = 0):
    """Retrieve songs from the database, optionally filtering by search query with pagination."""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                if search_query:
                    query = """
                        SELECT id, title, artist, album, file_path, metadata 
                        FROM songs 
                        WHERE title ILIKE %s OR artist ILIKE %s OR album ILIKE %s 
                        ORDER BY id DESC 
                        LIMIT %s OFFSET %s
                    """
                    cursor.execute(query, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", limit, offset))
                else:
                    cursor.execute("SELECT id, title, artist, album, file_path, metadata FROM songs ORDER BY id DESC LIMIT %s OFFSET %s", (limit, offset))
                
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
        raise

def delete_song_by_id(song_id: int) -> bool:
    """Delete a song from the database by its ID."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM songs WHERE id = %s", (song_id,))
                song_exists = cursor.fetchone()
                
                if not song_exists:
                    logger.warning(f"Song ID {song_id} not found.")
                    return False  # Song doesn't exist
                
                cursor.execute("DELETE FROM songs WHERE id = %s RETURNING id", (song_id,))
                deleted = cursor.fetchone()
                conn.commit()

        return bool(deleted)
    except Exception as e:
        logger.exception(f"Error deleting song with ID {song_id}: {e}")
        raise