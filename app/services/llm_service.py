import json
import toons
import aiohttp
from typing import Dict, Any, Optional, List
import logging
from app.config import config

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self) -> None:
        self.model_name = "llama3.2:1b"
        self.ollama_url = config.ollama_url
        self.timeout = 30

    async def _build_toon_prompt(
        self,
        query: str,
        context_chunks: Optional[List[Dict]] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Build TOON-optimized prompt for maximum token efficiency"""

        prompt_parts = []

        # System instruction (concise)
        prompt_parts.append(
            "Answer based on provided context and conversation history."
        )

        # TOON format for chat history
        if session_id:
            from app.services.chat_memory import ChatMemoryService

            chat_memory = ChatMemoryService()
            chat_toon = await chat_memory.get_chat_history_toon(session_id, limit=5)
            if chat_toon:
                prompt_parts.append(f"\n{chat_toon}")

        # TOON format for document context
        if context_chunks:
            context_toon = self._format_context_toon(context_chunks)
            prompt_parts.append(f"\n{context_toon}")

        # Current query
        prompt_parts.append(f"\nquery: {query}")
        prompt_parts.append("response:")

        return "\n".join(prompt_parts)

    def _format_context_toon(self, chunks: List[Dict]) -> str:
        """Convert context chunks to TOON format"""
        if not chunks:
            return ""

        context_data = {
            "context": [
                {
                    "doc_id": chunk.get("doc_id", "unknown"),  # Fixed typo
                    "content": chunk.get("content", "")[:200],  # Added missing comma
                    "score": round(chunk.get("score", 0.0), 3),
                }
                for chunk in chunks
            ]
        }

        return toons.dumps(
            context_data, indent=2, delimiter=",", key_folding="short", flatten_depth=1
        )

    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API with TOON-optimized prompt"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 512,  # Token limit for response
                },
            }

            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate", json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "No response generated")
                    else:
                        logger.error(f"Ollama API error: {response.status}")
                        return "Error generating response"

        except aiohttp.ClientError as e:
            logger.error(f"Ollama connection error: {e}")
            return "Unable to connect to AI service"
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama: {e}")
            return "Processing error occurred"

    async def health_check(self) -> bool:
        """Check if Ollama service is available"""
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    return response.status == 200
        except:
            return False

    async def generate_response(
        self,
        query: str,
        context_chunks: Optional[List[Dict]] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Generate response using Ollama with TOON-optimized prompts"""
        try:
            # Build TOON-optimized prompt
            prompt = await self._build_toon_prompt(query, context_chunks, session_id)

            # Log for debugging (optional)
            logger.debug(f"TOON prompt generated ({len(prompt)} chars)")

            # Call Ollama
            response = await self._call_ollama(prompt)
            return response

        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return "I apologize, but I'm having trouble processing your request."
