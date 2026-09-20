"""
Redis PubSub Service for Real-time WebSocket Notifications
Broadcasts payment confirmation and blockchain confirmation events asynchronously.
"""

import json
import logging
from typing import Dict, Any, Optional
from razorpay.config import settings

logger = logging.getLogger("redis_service")


class RedisService:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self._async_client = None
        self._is_available: Optional[bool] = None

    async def get_client(self):
        """Returns the async Redis client instance, or None if connection fails."""
        if self._async_client is None and self._is_available is not False:
            try:
                import redis.asyncio as aioredis
                client = aioredis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2.0,
                    socket_timeout=2.0
                )
                await client.ping()
                self._async_client = client
                self._is_available = True
                logger.info("[Redis PubSub] Connected to async Redis.")
            except Exception as e:
                logger.warning(f"Redis connection not active ({e}). Events will be logged to console.")
                self._async_client = None
                self._is_available = False
        return self._async_client

    async def publish_event(self, channel: str, event_type: str, data: Dict[str, Any]):
        """Publish an event to a Redis channel for WebSocket broadcasting (non-blocking)."""
        message_payload = {
            "event": event_type,
            "data": data
        }
        client = await self.get_client()
        if client:
            try:
                await client.publish(channel, json.dumps(message_payload))
                logger.info(f"[Redis PubSub] Published '{event_type}' to channel '{channel}'")
            except Exception as e:
                logger.warning(f"Failed to publish event to Redis: {e}")
        else:
            logger.info(f"[Simulated WebSocket] Channel: '{channel}' | Event: '{event_type}' | Payload: {data}")

    async def notify_donor(self, user_id: str, event_type: str, data: Dict[str, Any]):
        """Send a real-time event to a specific donor channel."""
        await self.publish_event(f"user_{user_id}", event_type, data)

    async def broadcast_explorer(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to the public Transparency Explorer feed."""
        await self.publish_event("explorer_feed", event_type, data)

    async def get_idempotency_record(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached idempotency record from Redis."""
        client = await self.get_client()
        if client:
            try:
                val = await client.get(f"eleos:idempotency:{key}")
                if val:
                    return json.loads(val)
            except Exception as e:
                logger.warning(f"Failed to fetch idempotency key from Redis: {e}")
        return None

    async def set_idempotency_record(self, key: str, data: Dict[str, Any], ttl_seconds: int = 900):
        """Store cached idempotency record in Redis with 15-min default TTL."""
        client = await self.get_client()
        if client:
            try:
                await client.set(f"eleos:idempotency:{key}", json.dumps(data), ex=ttl_seconds)
            except Exception as e:
                logger.warning(f"Failed to save idempotency key to Redis: {e}")

    async def close(self):
        """Close connection cleanly."""
        if self._async_client:
            await self._async_client.close()
            self._async_client = None
            self._is_available = None


redis_service = RedisService()

