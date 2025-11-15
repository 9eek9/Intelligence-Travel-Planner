from fastapi import APIRouter, HTTPException
from services.places_service import _get_place_photos

router = APIRouter()

@router.get("/photos/{place_id}")
def get_place_photos(place_id: str):
    try:
        photos = _get_place_photos(place_id, max_photos=5)
        return {
            "place_id": place_id,
            "photo_urls": photos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
