from google import genai
from google.genai import types
import os
import httpx
import json
import asyncio
from typing import List, Dict, Any, AsyncGenerator

class ChatBackend:
    """
    Standard GenAI SDK 및 OpenAI 호환 API를 지원하는 대화형 백엔드.
    - GCR(Gemini CLI Router) 사상을 벤치마킹하여 타사 모델 연동 지원.
    """
    def __init__(self, config_data, prompt):
        self.config_data = config_data
        self.prompt = prompt
        self.client = None
        self.chat_session = None
        self.provider = config_data.get('agent', {}).get('provider', 'google')
        # [Fix] Initialize history in constructor to prevent AttributeError
        self.history: List[Dict[str, Any]] = []

    async def initialize(self):
        if self.provider == 'google':
            api_key = os.getenv("GEMINI_API_KEY")
            # [Fix] Use stable v1 version for better model compatibility
            self.client = genai.Client(api_key=api_key)
            
            agent_params = self.config_data.get('agent', {})
            model_name = agent_params.get('model', 'gemini-3.5-flash')
            
            self.chat_session = self.client.aio.chats.create(
                model=model_name,
                config=types.GenerateContentConfig(
                    system_instruction=self.prompt,
                    temperature=agent_params.get('temperature', 0.7),
                    max_output_tokens=agent_params.get('max_output_tokens', 4096),
                )
            )
        else:
            # OpenAI 호환 백엔드 (Ollama, DeepSeek 등)
            self.api_key = os.getenv("EXTERNAL_API_KEY", "no-key")
            self.base_url = self.config_data.get('agent', {}).get('base_url', "http://localhost:11434/v1")
            # [Fix] Use model from config if available, fallback to llama3
            self.model = self.config_data.get('agent', {}).get('model', "llama3")
            self.history = []

    async def chat(self, text: str):
        """[Deprecated] Non-streaming chat for compatibility."""
        if self.provider == 'google':
            response = await self.chat_session.send_message(text)
            return response, response.usage_metadata if hasattr(response, 'usage_metadata') else None
        else:
            # Fallback to stream and collect
            full_text = ""
            async for chunk in self.chat_stream(text):
                full_text += chunk
            
            class MockResponse:
                def __init__(self, text): self.text = text
            return MockResponse(full_text), None

    async def chat_stream(self, text: str) -> AsyncGenerator[str, None]:
        """Streaming chat interface for better UX."""
        if self.provider == 'google':
            async for chunk in await self.chat_session.send_message_stream(text):
                if hasattr(chunk, 'text'):
                    yield chunk.text
                elif hasattr(chunk, 'candidates'):
                    yield chunk.candidates[0].content.parts[0].text
        else:
            # OpenAI 호환 API 스트리밍 호출
            async with httpx.AsyncClient() as client:
                messages = [{"role": "system", "content": self.prompt}] + self.history + [{"role": "user", "content": text}]
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": self.config_data.get('agent', {}).get('temperature', 0.7),
                        "stream": True
                    },
                    timeout=60.0
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]": break
                            try:
                                data = json.loads(data_str)
                                delta = data['choices'][0]['delta']
                                if 'content' in delta:
                                    yield delta['content']
                            except: continue

    async def close(self):
        self.client = None
        self.chat_session = None
