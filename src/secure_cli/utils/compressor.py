import logging
from typing import List, Dict, Any

class ContextCompressor:
    """대화 히스토리를 요약하여 컨텍스트를 압축하는 유틸리티."""
    
    def __init__(self, backend: Any):
        self.backend = backend
        self.logger = logging.getLogger("Compressor")

    async def compress(self, history: List[Dict[str, str]], keep_last: int = 5) -> List[Dict[str, str]]:
        """
        히스토리의 앞부분을 요약하여 하나의 시스템 메시지로 압축합니다.
        pinned된 메시지는 보존됩니다.
        """
        if len(history) <= keep_last + 2:
            return history

        to_compress = history[:-keep_last]
        recent = history[-keep_last:]

        # pinned 메시지 분리 (turn에 'pinned' 속성이 있다고 가정)
        pinned = [h for h in to_compress if h.get('pinned')]
        not_pinned = [h for h in to_compress if not h.get('pinned')]

        if not not_pinned:
            return history

        self.logger.info(f"Compressing {len(not_pinned)} turns...")
        
        prompt = "다음은 이전 대화의 기록입니다. 중요한 맥락과 결정 사항을 유지하면서 간결하게 요약해 주세요:\n\n"
        for h in not_pinned:
            prompt += f"[{h['role']}]: {h['content']}\n"

        try:
            response, _ = await self.backend.chat(prompt)
            summary = response.text if hasattr(response, 'text') else str(response)
            
            compressed_history = [
                {"role": "system", "content": f"이전 대화 요약: {summary}"}
            ]
            compressed_history.extend(pinned)
            compressed_history.extend(recent)
            
            return compressed_history
        except Exception as e:
            self.logger.error(f"Compression error: {e}")
            return history
