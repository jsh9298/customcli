import logging
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig
from google.antigravity.hooks import policy

class AgentBackend:
    """Antigravity SDK를 사용하는 자율 에이전트 백엔드."""
    def __init__(self, config_data, prompt):
        self.config_data = config_data
        self.prompt = prompt
        self.agent = None
        self.context_manager = None

    async def initialize(self):
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
            if p['action'] == "allow": policies.extend([policy.allow(t) for t in p['tools']])
            elif p['action'] == "deny": policies.extend([policy.deny(t) for t in p['tools']])
            elif p['action'] == "ask_user": policies.extend([policy.ask_user(t) for t in p['tools']])

        config = LocalAgentConfig(
            model=agent_params.get('model', 'gemini-1.5-flash'),
            temperature=agent_params.get('temperature', 0.7),
            max_output_tokens=agent_params.get('max_output_tokens', 4096),
            system_instructions=self.prompt,
            capabilities=capabilities,
            policies=policies
        )
        
        self.agent = Agent(config)
        # 소켓 유지를 위해 __aenter__ 호출 상태 유지
        await self.agent.__aenter__()

    async def chat(self, text):
        # 지속 세션 내에서 chat 호출
        response = await self.agent.chat(text)
        return response, response.usage_metadata if hasattr(response, 'usage_metadata') else None

    async def close(self):
        if self.agent:
            await self.agent.__aexit__(None, None, None)
