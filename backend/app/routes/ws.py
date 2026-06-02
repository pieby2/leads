import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as redis
from app.config import get_settings
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["websocket"])
settings = get_settings()

@router.websocket("/ws/session/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    redis_client = redis.from_url(settings.redis_url)
    pubsub = redis_client.pubsub()
    channel = f"session_progress:{session_id}"
    
    try:
        await pubsub.subscribe(channel)
        logger.info("websocket connected to redis pubsub", session_id=session_id)
        
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                data = message["data"].decode("utf-8")
                await websocket.send_text(data)
                
                parsed = json.loads(data)
                if parsed.get("status") in ["ready", "error"]:
                    break
            else:
                await asyncio.sleep(0.1)
                
    except WebSocketDisconnect:
        logger.info("websocket disconnected", session_id=session_id)
    except Exception as e:
        logger.error("websocket error", error=str(e), session_id=session_id)
    finally:
        await pubsub.unsubscribe(channel)
        await redis_client.close()
