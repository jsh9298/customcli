from typing import Dict, Any, Callable
from secure_cli.agent.backends.chat_backend import ChatBackend
from secure_cli.agent.backends.agent_backend import AgentBackend

class BackendFactory:
    """[Factory Method] Standardizes AI backend instantiation."""
    
    @staticmethod
    def create_backend(mode: str, config: Dict[str, Any], prompt: str, terminal_handler: Callable):
        if mode == "chat":
            return ChatBackend(config, prompt)
        elif mode == "agents":
            return AgentBackend(config, prompt, ask_user_handler=terminal_handler)
        else:
            raise ValueError(f"Unknown backend mode: {mode}")
