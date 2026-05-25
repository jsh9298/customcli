import logging
import asyncio
from typing import List, Dict, Any, Optional

class GroupChatManager:
    """다중 페르소나가 참여하는 협업 대화(Group Chat)를 관리하는 클래스."""
    
    def __init__(self, cli: Any):
        self.cli = cli
        self.logger = logging.getLogger("GroupChat")

    async def run_group_discussion(self, personas: List[str], topic: str, rounds: int = 1) -> str:
        """지정된 페르소나들이 주제에환대해 토의를 진행합니다."""
        discussion_log = f"### 👥 Group Discussion: {topic}\n\n"
        context = topic

        for r in range(rounds):
            for p_name in personas:
                if p_name not in self.cli.personas:
                    continue
                
                self.cli.ui.print_info(f"[{p_name.upper()}] Thinking...")
                
                # 페르소나별 시스템 프롬프트 설정
                persona_prompt = self.cli.personas[p_name]
                full_prompt = f"{persona_prompt}\n\n현재 토의 주제와 진행 상황:\n{discussion_log}\n\n당신의 의견을 말해 주세요."
                
                # 백엔드 호출 (임시 페르소나 적용을 위해 백엔드 재초기화 없이 컨텍스트만 주입)
                # 실제 구현 시에는 ChatBackend의 system_instruction을 동적으로 바꿀 수 있어야 함
                response, _ = await self.cli.backend.chat(full_prompt)
                content = response.text if hasattr(response, 'text') else str(response)
                
                msg = f"**{p_name.upper()}**: {content}\n\n"
                discussion_log += msg
                self.cli.ui.render_markdown(msg)
                
        return discussion_log
