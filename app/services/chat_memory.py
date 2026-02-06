import json
import uuid
from requests import session
import toons
from datetime import datetime, timezone
from typing import List, Dict, Optional

from app.database.redis_client import get_redis_client


class ChatMemoryService:
    def __init__(self) -> None:
        self.key_prefix = "chat_session"

    async def create_session(self) -> str:
        """Create a new chat session and return session id"""
        session_id = str(uuid.uuid4())
        return session_id

    async def store_message(
        self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None
    ) -> None:
        """Store a message in the chat session"""
        client = await get_redis_client()

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }

        key = f"{self.key_prefix}{session_id}"

        await client.lpush(key, json.dumps(message))

        await client.expire(key, 86400)  # Time to live for session (24 hours)

    async def get_chat_history_json(
        self, session_id: str, limit: int = 10
    ) -> List[Dict]:
        """Get recent messages as JSON objects"""
        client = await get_redis_client()
        key = f"{self.key_prefix}{session_id}"

        messages = await client.lrange(key, 0, limit - 1)

        return [json.loads(msg) for msg in messages]

    async def get_chat_history_toon(self, session_id: str, limit: int = 10) -> str:
        """Convert chat history to TOON format for LLM using toons"""
        messages = await self.get_chat_history_json(session_id)

        if not messages:
            return ""

        return toons.dumps({"messages": messages})

    async def session_exists(self, session_id: str) -> bool:
        """Check if session exists"""
        client = await get_redis_client()
        key = f"{self.key_prefix}{session_id}"
        return await client.exists(key) > 0
