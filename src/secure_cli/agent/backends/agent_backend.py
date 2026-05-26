import logging
import asyncio
import time
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig
from google.antigravity.hooks import policy
from typing import Any, List, Optional, Callable, Dict

# [Bridge] Global reference to avoid deepcopy issues with bound methods
_ask_user_handler_bridge: Optional[Callable] = None

async def _ask_user_proxy(cmd: str) -> str:
    """Proxy function to call the actual handler without capturing 'self'."""
    if _ask_user_handler_bridge:
        return await _ask_user_handler_bridge(cmd)
    return "Error: Terminal handler bridge not initialized."

class AgentBackend:
    """Antigravity SDK를 사용하는 자율 에이전트 백엔드 (강화된 생명주기 관리)."""
    def __init__(self, config_data: dict, prompt: str, ask_user_handler: Optional[Callable] = None):
        self.config_data = config_data
        self.prompt = prompt
        self.ask_user_handler = ask_user_handler
        self.agent = None
        self.history: List[Dict[str, Any]] = []
        self._last_active = 0
        self._connection_timeout = 600  # 10분 (연결 유지 시간 확장)
        self._is_initialized = False

    async def initialize(self):
        """세션을 초기화하고 타임아웃 설정을 대폭 강화합니다."""
        global _ask_user_handler_bridge
        _ask_user_handler_bridge = self.ask_user_handler
        
        agent_params = self.config_data.get('agent', {})
        caps_data = self.config_data.get('capabilities', {})
        
        capabilities = CapabilitiesConfig(
            filesystem_read=caps_data.get('filesystem', {}).get('read', True),
            filesystem_write=caps_data.get('filesystem', {}).get('write', False),
            terminal_execute=caps_data.get('terminal', {}).get('execute', True),
            browser_enabled=caps_data.get('browser', {}).get('enabled', False)
        )

        policies = []
        for p in self.config_data.get('policies', []):
            if p['action'] == "allow": 
                policies.extend([policy.allow(t) for t in p['tools']])
            elif p['action'] == "deny": 
                policies.extend([policy.deny(t) for t in p['tools']])
            elif p['action'] == "ask_user": 
                policies.extend([policy.ask_user(t, handler=_ask_user_proxy) for t in p['tools']])

        # [Enhanced Cycle] 2026 표준에 맞춰 타임아웃 및 버퍼 설정을 최대로 확보
        config = LocalAgentConfig(
            model=agent_params.get('model', 'gemini-3.5-flash'),
            temperature=agent_params.get('temperature', 0.7),
            max_output_tokens=agent_params.get('max_output_tokens', 8192), # 버퍼 확장
            system_instructions=self.prompt,
            capabilities=capabilities,
            policies=policies,
            # SDK 내부 타임아웃 명시적 확장
            request_timeout=300, 
            stream_timeout=600
        )
        
        if self.agent: await self.close()
        
        self.agent = Agent(config)
        await self.agent.__aenter__()
        self._last_active = time.time()
        self._is_initialized = True
        logging.info("Antigravity SDK Session established with extended timeouts (600s).")

    async def ensure_connected(self):
        """대화 전 세션 생존 여부를 확인하고 필요시 능동적으로 갱신합니다."""
        now = time.time()
        # 마지막 활동으로부터 5분이 지났거나 초기화되지 않은 경우 재연결
        if not self._is_initialized or (now - self._last_active > 300):
            logging.info("Proactive session renewal triggered.")
            await self.initialize()

    async def chat(self, text):
        """능동적으로 관리되는 세션 내에서 chat 호출."""
        await self.ensure_connected()
        self._last_active = time.time()
        
        try:
            response = await self.agent.chat(text)
            self._last_active = time.time()
            return response, response.usage_metadata if hasattr(response, 'usage_metadata') else None
        except Exception as e:
            logging.error(f"Chat stream error: {e}. Force reconnecting...")
            await self.initialize()
            response = await self.agent.chat(text)
            self._last_active = time.time()
            return response, response.usage_metadata if hasattr(response, 'usage_metadata') else None

    async def close(self):
        if self.agent:
            try:
                await self.agent.__aexit__(None, None, None)
            except: pass
            self.agent = None
            self._is_initialized = False
