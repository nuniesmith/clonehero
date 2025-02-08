from fastapi import APIRouter, HTTPException, Query
from src.services.database_explorer import get_all_songs, delete_song_by_id
from loguru import logger

router = APIRouter()

@router.get("/songs/")
async def fetch_songs(
    search: str = Query(None, title="Search Query", description="Filter by title, artist, or album"),
    limit: int = Query(50, ge=1, le=100, title="Limit", description="Number of results to return"),
    offset: int = Query(0, ge=0, title="Offset", description="Pagination offset")
):
    """Fetch all songs from the database with optional search and pagination."""
    try:
        songs = get_all_songs(search_query=search, limit=limit, offset=offset)
        return {"total": len(songs), "songs": songs}
    except Exception as e:
        logger.exception(f"Error fetching songs: {e}")
        raise HTTPException(status_code=500, detail="Error fetching songs")

@router.delete("/songs/{song_id}", status_code=204)
async def delete_song(song_id: int):
    """Delete a song by ID from the database."""
    try:
        deleted = delete_song_by_id(song_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Song not found")
    except Exception as e:
        logger.exception(f"Error deleting song ID {song_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting song")