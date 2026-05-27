import re
import yaml
import os
import logging
import uuid
import hashlib
import hmac
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable

# ==========================================
# [Strategy Pattern] Masking Algorithms
# ==========================================
class MaskingStrategy(ABC):
    @abstractmethod
    def generate_token(self, value: str, label: str) -> str:
        pass

class SHA256MaskingStrategy(MaskingStrategy):
    def generate_token(self, value: str, label: str) -> str:
        val_hash = hashlib.sha256(value.encode()).hexdigest()[:8]
        return f"[{label}_{val_hash}]"

class HMACMaskingStrategy(MaskingStrategy):
    def __init__(self, secret: str = "secure_ag_cli_secret"):
        self.secret = secret.encode()
    def generate_token(self, value: str, label: str) -> str:
        val_hash = hmac.new(self.secret, value.encode(), hashlib.sha256).hexdigest()[:8]
        return f"[{label}_{val_hash}]"

# ==========================================
# [Observer Pattern] Security Events
# ==========================================
class SecurityObserver(ABC):
    @abstractmethod
    def on_violation(self, event_type: str, details: str):
        pass

class AlertObserver(SecurityObserver):
    def on_violation(self, event_type: str, details: str):
        logger = logging.getLogger("SecurityAudit")
        logger.critical(f"🚨 SECURITY VIOLATION: [{event_type}] - Details: {details}")

# ==========================================
# [Chain of Responsibility] DLP Filter Chain
# ==========================================
class DLPFilter(ABC):
    def __init__(self):
        self._next: Optional[DLPFilter] = None

    def set_next(self, next_filter: 'DLPFilter') -> 'DLPFilter':
        self._next = next_filter
        return next_filter

    @abstractmethod
    def handle(self, text: str, context: Dict[str, Any]) -> str:
        if self._next:
            return self._next.handle(text, context)
        return text

class GuardrailFilter(DLPFilter):
    def handle(self, text: str, context: Dict[str, Any]) -> str:
        # 응답 모드에서는 가드레일 체크 건너뜀 (이미 AI가 생성한 것이므로)
        if context.get('is_response', False):
            return super().handle(text, context)

        guardrails = context.get('guardrails', [])
        text_lower = text.lower()
        for keyword in guardrails:
            if keyword in text_lower:
                for obs in context.get('observers', []):
                    obs.on_violation("GUARDRAIL_HIT", keyword)
                return f"Blocked: Safety Policy Violation (Guardrail: {keyword})"
        return super().handle(text, context)

class RegexMaskFilter(DLPFilter):
    def handle(self, text: str, context: Dict[str, Any]) -> str:
        protector = context.get('protector')
        if not protector or not protector.patterns:
            return super().handle(text, context)

        patterns = protector.patterns
        normalization_rules = protector.normalization_rules
        whitelist = protector.whitelist
        strategy = protector.masking_strategy
        
        combined_pattern = re.compile('|'.join(f'(?P<{label}>{pat})' for label, pat in patterns.items()), re.IGNORECASE)

        def replace_match(match):
            val = match.group(0)
            if val in whitelist: return val
            if val in protector._mask_map: return protector._mask_map[val]
            
            label = match.lastgroup
            norm_val = val
            if label in normalization_rules:
                norm_val = re.sub(r'[- ]', '', val)

            token = strategy.generate_token(norm_val, label)
            
            protector._mask_map[val] = token
            protector._unmask_map[token] = val
            return token

        masked_text = combined_pattern.sub(replace_match, text)
        return super().handle(masked_text, context)

# ==========================================
# [Enhanced SecurityProtector]
# ==========================================
class SecurityProtector:
    """
    Refactored DLP Engine using Design Patterns:
    - Strategy: Masking Algorithms
    - Chain of Responsibility: Filter Pipeline
    - Observer: Violation Notifications
    """

    def __init__(self, config_path: str = 'masking_config.yaml'):
        self.config_path = config_path
        self._last_config_mtime = 0
        self._mask_map: Dict[str, str] = {}
        self._unmask_map: Dict[str, str] = {}
        self.patterns: Dict[str, str] = {}
        self.normalization_rules: List[str] = []
        self.guardrails: List[str] = []
        self.whitelist: List[str] = []
        self.mask_cache: Dict[str, str] = {}
        self.logger = logging.getLogger("Protector")
        
        # Default Strategy and Observers
        self.masking_strategy: MaskingStrategy = SHA256MaskingStrategy()
        self.observers: List[SecurityObserver] = [AlertObserver()]
        
        self.load_config(config_path)
        self._build_filter_chain()

    def check_reload(self):
        """[Dynamic Reload] 설정 파일 변경 감지 및 즉시 반영"""
        if os.path.exists(self.config_path):
            mtime = os.path.getmtime(self.config_path)
            if mtime > self._last_config_mtime:
                self.logger.info("Config change detected. Reloading...")
                self.load_config(self.config_path)
                self._last_config_mtime = mtime
                self.mask_cache.clear() # 설정 변경 시 캐시 무효화

    def _build_filter_chain(self):
        self.filter_chain = GuardrailFilter()
        self.filter_chain.set_next(RegexMaskFilter())

    def load_config(self, config_path: str):
        if os.path.exists(config_path):
            try:
                self._last_config_mtime = os.path.getmtime(config_path)
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                    self.patterns = config.get('patterns', {})
                    self.normalization_rules = config.get('normalization_rules', [])
                    self.guardrails = config.get('guardrails', [])
                    self.whitelist = config.get('whitelist', [])
                    
                    # Strategy switching via config
                    strat_name = config.get('masking_algorithm', 'sha256').lower()
                    if strat_name == 'hmac':
                        self.masking_strategy = HMACMaskingStrategy(config.get('hmac_secret', 'ag_cli_default'))
                    else:
                        self.masking_strategy = SHA256MaskingStrategy()

                    self.logger.info(f"Loaded config: Algorithm={strat_name}, Patterns={len(self.patterns)}")
            except Exception as e:
                self.logger.error(f"Config load error: {e}")
        else:
            self.logger.warning("Masking config not found. Running with empty patterns.")

    def mask(self, text: str, is_response: bool = False) -> str:
        if not text: return text
        
        # 0. Check for Config Reload
        self.check_reload()
        
        # 1. Cache Check
        content_hash = hashlib.md5(text.encode()).hexdigest()
        if content_hash in self.mask_cache:
            return self.mask_cache[content_hash]

        # 2. Run through Filter Chain
        context = {
            'protector': self,
            'is_response': is_response,
            'guardrails': self.guardrails,
            'observers': self.observers
        }
        
        masked_text = self.filter_chain.handle(text, context)
        
        # Update Cache
        if len(self.mask_cache) > 200: self.mask_cache.clear()
        self.mask_cache[content_hash] = masked_text
        
        if is_response and masked_text != text:
            self.logger.warning("Response Firewall: Sensitive data masked in AI response.")
            
        return masked_text

    def unmask(self, text: str) -> str:
        if not text: return text
        unmasked_text = text
        # Match tokens [LABEL_hex8]
        tokens = re.findall(r'\[[A-Z0-9_]+_[a-f0-9]{8}\]', unmasked_text)
        sorted_tokens = sorted(list(set(tokens)), key=len, reverse=True)
        for token in sorted_tokens:
            if token in self._unmask_map:
                unmasked_text = unmasked_text.replace(token, self._unmask_map[token])
        return unmasked_text

    def clear(self):
        self._mask_map.clear()
        self._unmask_map.clear()
        self.mask_cache.clear()
