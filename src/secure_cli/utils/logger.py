import os
import json
import logging
from datetime import datetime

class PayloadLogger:
    """AI로 전송되는 최종 데이터(마스킹 완료본)를 기록하는 보안 감사 로그 모듈."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        self.logger = logging.getLogger("PayloadLogger")
        self.logger.setLevel(logging.INFO)
        
        # 파일 핸들러 설정
        log_file = os.path.join(self.log_dir, "security_audit.log")
        handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_payload(self, backend: str, payload: str):
        """AI로 전송되기 직전의 마스킹된 페이로드를 기록합니다."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "backend": backend,
            "masked_payload": payload
        }
        self.logger.info(f"Payload Outgoing ({backend}):\n{json.dumps(entry, ensure_ascii=False, indent=2)}")
        
        # 별도의 debug_payload.log 에도 기록 (MAINTENANCE.md 가이드 준수)
        with open("debug_payload.log", "a", encoding="utf-8") as f:
            f.write(f"\n--- [{datetime.now().isoformat()}] [{backend}] ---\n")
            f.write(payload)
            f.write("\n" + "="*50 + "\n")
