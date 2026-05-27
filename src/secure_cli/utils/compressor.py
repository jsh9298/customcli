import logging
import os
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

class ContextCompressor:
    """
    [Context Compression V2]
    - Automatically condenses conversation history into a semantic summary.
    - Default: Uses the current session's model for maximum context awareness.
    - Configurable: Can use a dedicated lightweight model (e.g., Gemini 1.5 Flash) for efficiency.
    - Hierarchy: Preserves pinned messages and recent context.
    """
    
    def __init__(self, backend: Any, config: Optional[Dict[str, Any]] = None):
        self.backend = backend
        self.config = config or {}
        self.logger = logging.getLogger("Compressor")
        
        # Determine the compression model
        agent_cfg = self.config.get('agent', {})
        self.compression_model = agent_cfg.get('compression_model') # May be None
        self.current_model = agent_cfg.get('model', 'gemini-1.5-flash')
        
        # Auto-trigger threshold (Default: 0 - manual only)
        self.auto_threshold = agent_cfg.get('compression_threshold', 0)

    async def _get_compression_client(self):
        """Returns an AI client for compression, favoring specialized model if configured."""
        model_to_use = self.compression_model if self.compression_model else self.current_model
        
        # If we are using the current backend's model, we can try to use its active session
        # but for clean compression (avoiding history pollution), a separate stateless call is better.
        if hasattr(self.backend, 'client') and self.backend.client:
            return self.backend.client, model_to_use
        
        # Fallback to creating a temporary client if backend is not Google
        api_key = os.getenv("GEMINI_API_KEY")
        return genai.Client(api_key=api_key), model_to_use

    async def compress(self, history: List[Dict[str, str]], keep_last: int = 5) -> List[Dict[str, str]]:
        """
        Condenses history while preserving semantic integrity and pinned items.
        """
        if len(history) <= keep_last + 2:
            return history

        to_compress = history[:-keep_last]
        recent = history[-keep_last:]

        # Separate pinned items (instructions, key decisions)
        pinned = [h for h in to_compress if h.get('pinned')]
        not_pinned = [h for h in to_compress if not h.get('pinned')]

        if not not_pinned:
            return history

        self.logger.info(f"Compressing {len(not_pinned)} turns using model: {self.compression_model or self.current_model} (Default: Current)")
        
        prompt = (
            "You are a context management expert. Summarize the following conversation history "
            "into a concise, high-density summary. Focus on key decisions, technical details, "
            "and user preferences. Use Markdown for clarity.\n\n"
            "--- CONVERSATION TO SUMMARIZE ---\n"
        )
        for h in not_pinned:
            role = h.get('role', 'user').upper()
            content = h.get('content', '')
            prompt += f"[{role}]: {content}\n"

        try:
            client, model_id = await self._get_compression_client()
            
            # Use stateless generate_content for compression to avoid affecting main session
            response = await client.aio.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3, # Lower temperature for stable summarization
                    system_instruction="You are a meticulous archiver. Extract and summarize facts precisely."
                )
            )
            
            summary = response.text if hasattr(response, 'text') else str(response)
            
            # Construct new history
            compressed_history = [
                {
                    "role": "system", 
                    "content": f"## PREVIOUS CONTEXT SUMMARY\n{summary}",
                    "compressed": True # Metadata flag
                }
            ]
            compressed_history.extend(pinned)
            compressed_history.extend(recent)
            
            self.logger.info("Context compression completed successfully.")
            return compressed_history
            
        except Exception as e:
            self.logger.error(f"Compression failure: {e}. Reverting to original history.")
            return history
