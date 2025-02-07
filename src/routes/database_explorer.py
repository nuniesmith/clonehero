from fastapi import APIRouter, HTTPException
from src.services.database_explorer import get_all_songs, delete_song_by_id

router = APIRouter()

@router.get("/songs/")
async def fetch_songs():
    """Fetch all songs from the database."""
    try:
        return get_all_songs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/songs/{song_id}")
async def delete_song(song_id: int):
    """Delete a song by ID from the database."""
    try:
        result = delete_song_by_id(song_id)
        if result:
            return {"message": "Song deleted successfully."}
        else:
            raise HTTPException(status_code=404, detail="Song not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))