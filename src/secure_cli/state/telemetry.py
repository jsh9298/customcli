from typing import Any, Optional

class QuotaExceededError(Exception):
    """Exception raised when API usage exceeds the defined quota."""
    pass

class TelemetryManager:
    """
    사용량 추적, 토큰 메트릭 및 SDK 메타데이터 관리 클래스.
    - 세션별, 일일별, 모델별 제한 수치를 명확히 구분합니다.
    """
    
    def __init__(self, hard_limit: int = 0, model_limit: int = 4096):
        self.last_usage: Any = None
        self.session_tokens = 0
        self.daily_tokens = 0  # 실제 운영시 파일/DB 연동 필요
        self.model_limit = model_limit  # 모델의 최대 출력 토큰 (또는 컨텍스트 범위)
        self.hard_limit = hard_limit   # 일일 또는 계정별 하드 리밋 (0은 무제한)

    def update_usage(self, usage_metadata: Any):
        if not usage_metadata: return
        
        new_tokens = getattr(usage_metadata, 'total_token_count', 0)
        
        if self.hard_limit > 0 and (self.daily_tokens + new_tokens) > self.hard_limit:
            raise QuotaExceededError(f"일일 할당량 초과 (Daily Quota Exceeded): {self.daily_tokens + new_tokens} > {self.hard_limit}")

        self.last_usage = usage_metadata
        self.session_tokens += new_tokens
        self.daily_tokens += new_tokens

    def get_detailed_stats(self) -> dict:
        return {
            "session": self.session_tokens,
            "daily": self.daily_tokens,
            "hard_limit": self.hard_limit,
            "model_limit": self.model_limit,
            "last_request": getattr(self.last_usage, 'total_token_count', 0) if self.last_usage else 0
        }

    def format_quota_display(self) -> str:
        """대시보드용 간략 표시: [세션]/[일일 할당량]"""
        daily_str = f"/{self.hard_limit:,}" if self.hard_limit > 0 else "/∞"
        return f"S:{self.session_tokens:,} D:{self.daily_tokens:,}{daily_str}"
