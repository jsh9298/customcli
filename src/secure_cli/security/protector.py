import re
import yaml
import os
import logging
import uuid
import hashlib
from typing import Dict, List, Optional, Any

class SecurityProtector:
    """
    DLP(Data Loss Prevention) 보안 엔진 클래스.
    - Truncated SHA-256 기반의 결정론적 마스킹 지원.
    - 가드레일(Hard Drop), 로컬 비식별화 캐시, 응답 방화벽 포함.
    """

    def __init__(self, config_path: str = 'masking_config.yaml'):
        self._mask_map: Dict[str, str] = {}
        self._unmask_map: Dict[str, str] = {}
        self.patterns: Dict[str, str] = {}
        self.guardrails: List[str] = []
        self.mask_cache: Dict[str, str] = {} # Content hash -> Masked text
        self.logger = logging.getLogger("Protector")
        self.session_id = str(uuid.uuid4())[:8]
        self.load_config(config_path)

    def load_config(self, config_path: str):
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    self.patterns = config.get('patterns', {})
                    self.guardrails = config.get('guardrails', [])
                    self.logger.info(f"Loaded {len(self.patterns)} patterns and {len(self.guardrails)} guardrails.")
            except Exception as e:
                self.logger.error(f"Config load error: {e}")
                self._set_default_patterns()
        else:
            self._set_default_patterns()

    def _set_default_patterns(self):
        self.patterns = {
            'EMAIL': r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
            'API_KEY': r'AIzaSy[A-Za-z0-9_-]{33}',
            'IPV4': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        }

    def mask(self, text: str, is_response: bool = False) -> str:
        """
        Truncated SHA-256 기반의 결정론적 마스킹을 수행합니다.
        """
        if not text: return text
        
        # 1. 가드레일 체크 (Hard Drop)
        if not is_response:
            text_lower = text.lower()
            for keyword in self.guardrails:
                if keyword in text_lower:
                    self.logger.critical(f"GUARDRAIL HIT: {keyword}")
                    return f"Blocked: Safety Policy Violation (Guardrail: {keyword})"

        # 2. 로컬 비식별화 캐시 체크
        content_hash = hashlib.md5(text.encode()).hexdigest()
        if content_hash in self.mask_cache:
            return self.mask_cache[content_hash]

        # 3. 마스킹 실행
        if not self.patterns: return text
        combined_pattern = re.compile('|'.join(f'(?P<{label}>{pat})' for label, pat in self.patterns.items()), re.IGNORECASE)

        def replace_match(match):
            val = match.group(0)
            if val in self._mask_map:
                return self._mask_map[val]
            
            label = match.lastgroup
            # [Truncated SHA-256] 데이터 기반 고유 8글자 해시 생성
            val_hash = hashlib.sha256(val.encode()).hexdigest()[:8]
            token = f"[{label}_{val_hash}]"
            
            self._mask_map[val] = token
            self._unmask_map[token] = val
            return token

        masked_text = combined_pattern.sub(replace_match, text)
        
        # 캐시 저장
        if len(self.mask_cache) > 100: self.mask_cache.clear()
        self.mask_cache[content_hash] = masked_text
        
        if is_response and masked_text != text:
            self.logger.warning("Response Firewall: Sensitive data detected and masked in AI response.")
            
        return masked_text

    def unmask(self, text: str) -> str:
        if not text: return text
        unmasked_text = text
        # 8글자 16진수 해시 포맷 매칭 ([LABEL_hex8])
        tokens = re.findall(r'\[[A-Z0-9_]+_[a-f0-9]{8}\]', unmasked_text)
        sorted_tokens = sorted(list(set(tokens)), key=len, reverse=True)
        for token in sorted_tokens:
            if token in self._unmask_map:
                unmasked_text = unmasked_text.replace(token, self._unmask_map[token])
        return unmasked_text

    def add_pattern(self, label: str, regex: str):
        self.patterns[label] = regex
        self.logger.info(f"Dynamic pattern added: {label}")

    def remove_pattern(self, label: str):
        if label in self.patterns:
            del self.patterns[label]
            self.logger.info(f"Dynamic pattern removed: {label}")
            return True
        return False

    def clear(self):
        self._mask_map.clear()
        self._unmask_map.clear()
        self.mask_cache.clear()
        self.session_id = str(uuid.uuid4())[:8]
