import json
import os
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional, Any

class SessionManager:
    """
    대화 히스토리 및 보안 매핑 상태의 영속성을 관리하는 클래스.
    자동 만료(Auto-expiry) 로직이 포함되어 있습니다.
    """

    def __init__(self, session_dir: str = "sessions", expiry_days: int = 7):
        self.session_dir = session_dir
        self.expiry_days = expiry_days
        self.logger = logging.getLogger("SessionManager")
        
        # 세션 저장 디렉토리 자동 생성
        if not os.path.exists(self.session_dir):
            os.makedirs(self.session_dir)
        
        # 초기화 시 오래된 세션 자동 정리
        self.cleanup_expired_sessions()

    def cleanup_expired_sessions(self):
        """설정된 기간보다 오래된 세션 파일을 자동 삭제합니다."""
        now = time.time()
        expiry_seconds = self.expiry_days * 24 * 60 * 60
        
        try:
            if not os.path.exists(self.session_dir): return
            for f in os.listdir(self.session_dir):
                file_path = os.path.join(self.session_dir, f)
                if os.path.isfile(file_path) and f.endswith(".json"):
                    if now - os.path.getmtime(file_path) > expiry_seconds:
                        os.remove(file_path)
                        self.logger.info(f"Deleted expired session: {f}")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

    def save_session(self, history: List[Any], mask_map: Dict[str, str], unmask_map: Dict[str, str], name: Optional[str] = None) -> Optional[str]:
        """현재 대화 히스토리와 보안 맵을 JSON 파일로 저장합니다."""
        if not name:
            name = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        file_path = os.path.join(self.session_dir, f"{name}.json")
        data = {
            "timestamp": datetime.now().isoformat(),
            "history": history,
            "mask_map": mask_map,
            "unmask_map": unmask_map
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return name
        except Exception as e:
            self.logger.error(f"Failed to save session: {e}")
            return None

    def load_session(self, name: str) -> Optional[Dict[str, Any]]:
        """특정 이름의 세션 파일을 로드합니다."""
        file_path = os.path.join(self.session_dir, f"{name}.json")
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            self.logger.error(f"Failed to load session: {e}")
            return None

    def list_sessions(self) -> List[str]:
        """저장된 모든 세션의 목록을 반환합니다."""
        if not os.path.exists(self.session_dir):
            return []
        return [f.replace(".json", "") for f in os.listdir(self.session_dir) if f.endswith(".json")]

    def get_latest_session(self) -> Optional[str]:
        """수정 시간 기준으로 가장 최근에 생성/수정된 세션의 이름을 반환합니다."""
        if not os.path.exists(self.session_dir): return None
        sessions = [f for f in os.listdir(self.session_dir) if f.endswith(".json")]
        if not sessions:
            return None
        
        sessions.sort(key=lambda x: os.path.getmtime(os.path.join(self.session_dir, x)), reverse=True)
        return sessions[0].replace(".json", "")
