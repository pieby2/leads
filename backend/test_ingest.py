import asyncio
from unittest.mock import MagicMock, AsyncMock
from app.routes.ingest import ingest_videos
from app.models import IngestRequest
from app.db.models import User
import traceback

async def main():
    req = IngestRequest(
        youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        instagram_url="https://www.instagram.com/reel/CwYt5zJpW0q/"
    )
    
    # Mock user
    user = User(id="test_user", usage_this_month=0, tier="free")
    
    # Mock db session
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    
    try:
        # Mock _check_cache to return None so it fetches
        import app.routes.ingest
        app.routes.ingest._check_cache = AsyncMock(return_value=None)
        
        response = await ingest_videos(req=req, db=db, current_user=user)
        print("Response:", response)
    except Exception as e:
        print("EXCEPTION OCCURRED:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
