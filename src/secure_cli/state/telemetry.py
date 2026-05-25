from typing import Any, Optional

class QuotaExceededError(Exception):
    """Exception raised when API usage exceeds the defined quota."""
    pass

class TelemetryManager:
    """
    사용량 추적, 토큰 메트릭 및 SDK 메타데이터 관리 클래스.
    - Quota Enforcement (하드 리밋) 기능 포함.
    """
    
    def __init__(self, hard_limit: int = 0):
        self.last_usage: Any = None
        self.total_prompt_tokens = 0
        self.total_candidates_tokens = 0
        self.total_tokens = 0
        self.hard_limit = hard_limit # 0 means unlimited

    def update_usage(self, usage_metadata: Any):
        if not usage_metadata: return
        
        new_tokens = getattr(usage_metadata, 'total_token_count', 0)
        
        if self.hard_limit > 0 and (self.total_tokens + new_tokens) > self.hard_limit:
            raise QuotaExceededError(f"API Quota Exceeded: {self.total_tokens + new_tokens} > {self.hard_limit}")

        self.last_usage = usage_metadata
        self.total_prompt_tokens += getattr(usage_metadata, 'prompt_token_count', 0)
        self.total_candidates_tokens += getattr(usage_metadata, 'candidates_token_count', 0)
        self.total_tokens += new_tokens

    def get_current_session_stats(self) -> dict:
        if not self.last_usage:
            return {}
        return {
            "prompt_tokens": getattr(self.last_usage, 'prompt_token_count', 0),
            "candidates_tokens": getattr(self.last_usage, 'candidates_token_count', 0),
            "total_tokens": getattr(self.last_usage, 'total_token_count', 0)
        }

    def get_cumulative_stats(self) -> dict:
        return {
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_candidates_tokens": self.total_candidates_tokens,
            "total_tokens": self.total_tokens
        }

    def format_quota_display(self) -> str:
        total = getattr(self.last_usage, 'total_token_count', 0) if self.last_usage else 0
        limit_str = f"/{self.hard_limit:,}" if self.hard_limit > 0 else ""
        return f"{total:,}{limit_str}"
