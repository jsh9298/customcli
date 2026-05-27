from typing import Any, Optional, Callable
from secure_cli.agent.backends.agent_backend import AgentBackend
from secure_cli.agent.backends.chat_backend import ChatBackend

class BackendFactory:
    """
    [Factory Pattern] 백엔드 생성을 전담하는 팩토리 클래스.
    - CLI 모드에 따라 적절한 백엔드 인스턴스를 생성 및 반환합니다.
    - 새로운 백엔드(예: Mock, External API 등) 추가 시 이 클래스만 수정하면 됩니다.
    """
    
    @staticmethod
    def create_backend(
        mode: str, 
        config: dict, 
        prompt: str, 
        ask_user_handler: Optional[Callable] = None
    ) -> Any:
        """
        요청된 모드에 최적화된 백엔드 인스턴스를 생성합니다.
        
        Args:
            mode: 'agents' (자율형) 또는 'chat' (대화형)
            config: 시스템 설정 데이터
            prompt: 에이전트 페르소나/지시문
            ask_user_handler: (Agents 전용) 터미널 실행 승인 핸들러
        """
        if mode == "agents":
            return AgentBackend(config, prompt, ask_user_handler=ask_user_handler)
        elif mode == "chat":
            return ChatBackend(config, prompt)
        else:
            raise ValueError(f"Unsupported backend mode: {mode}")
