from src.database import get_connection
from loguru import logger

def get_all_songs(search_query: str = None):
    """Retrieve all songs from the database, optionally filtering by search query."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if search_query:
            cursor.execute("SELECT id, title, artist, album, file_path, metadata FROM songs WHERE title ILIKE %s OR artist ILIKE %s OR album ILIKE %s ORDER BY id DESC", (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
        else:
            cursor.execute("SELECT id, title, artist, album, file_path, metadata FROM songs ORDER BY id DESC")
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return [{
            "id": row[0],
            "title": row[1],
            "artist": row[2],
            "album": row[3],
            "file_path": row[4],
            "metadata": row[5] if row[5] else {}
        } for row in rows]
    except Exception as e:
        logger.exception(f"Error fetching songs from database: {e}")
        raise

def delete_song_by_id(song_id: int) -> bool:
    """Delete a song from the database by its ID."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM songs WHERE id = %s RETURNING id", (song_id,))
        deleted = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        return bool(deleted)
    except Exception as e:
        logger.exception(f"Error deleting song with ID {song_id}: {e}")
        raise