import re
from abc import ABC, abstractmethod
from typing import List, Dict

class MaskingStrategy(ABC):
    """[Strategy Pattern] Interface for different masking algorithms."""
    @abstractmethod
    def apply(self, text: str) -> str: pass

class RegexMaskingStrategy(MaskingStrategy):
    def __init__(self, pattern: str, replacement: str, flags: int = 0):
        self.regex = re.compile(pattern, flags=flags)
        self.replacement = replacement
    def apply(self, text: str) -> str:
        return self.regex.sub(self.replacement, text)

class SecurityProtector:
    """[Chain of Responsibility] Manages a sequence of masking strategies."""
    def __init__(self):
        self.strategies: List[MaskingStrategy] = []
        self._mask_map: Dict[str, str] = {}
        self._unmask_map: Dict[str, str] = {}

    def add_strategy(self, strategy: MaskingStrategy):
        self.strategies.append(strategy)

    def mask(self, text: str, is_response: bool = False) -> str:
        # 응답 마스킹과 요청 마스킹을 전략에 따라 수행
        result = text
        for strategy in self.strategies:
            result = strategy.apply(result)
        return result

    def unmask(self, text: str) -> str:
        # 역마스킹 로직 (필요시)
        return text
