import asyncio
from typing import List, Dict, Any, Optional
import uuid
from secure_cli.agent.backends.agent_backend import AgentBackend
from secure_cli.agent.backends.chat_backend import ChatBackend

class TaskNode:
    """Represents a single node in the task graph."""
    def __init__(self, task_id: str, description: str, dependencies: List[str] = None, status: str = "pending"):
        self.id = task_id
        self.description = description
        self.dependencies = dependencies or []
        self.status = status # pending, in-progress, completed, failed
        self.result: Any = None

class AgentOrchestrator:
    """
    멀티 에이전트 병렬 위임 및 태스크 그래프 관리 클래스.
    - Supervisor(관리자) 패턴 및 Producer-Reviewer 루프 지원.
    """
    
    def __init__(self, parent_cli: Any):
        self.parent = parent_cli
        self.goal: str = ""
        self.task_graph: Dict[str, TaskNode] = {}
        self.active_tasks: List[str] = []

    def set_goal(self, goal: str):
        self.goal = goal
        self.task_graph.clear()
        self.add_task(f"Primary Goal: {goal}")

    async def run_mission(self):
        """
        [Supervisor Pattern] 관리자 페르소나를 사용하여 목표를 하위 작업으로 자동 분해하고 실행합니다.
        """
        if not self.goal: return
        
        self.parent.ui.print_info("Supervisor: Breaking down goal into tasks...")
        # Supervisor용 임시 백엔드
        sup_backend = ChatBackend(self.parent.config, "You are a Project Supervisor. Break the user goal into logical sub-tasks.")
        await sup_backend.initialize()
        try:
            resp, _ = await sup_backend.chat(f"Goal: {self.goal}")
            content = resp.text if hasattr(resp, 'text') else str(resp)
            self.parent.ui.print_info(f"Supervisor Plan Analysis:\n{content}")
            self.add_task("Plan Analyzed", status="completed")
        finally:
            await sup_backend.close()

    def add_task(self, description: str, dependencies: List[str] = None, status: str = "pending") -> str:
        task_id = str(uuid.uuid4())[:8]
        node = TaskNode(task_id, description, dependencies, status)
        self.task_graph[task_id] = node
        return task_id

    async def delegate_task(self, agent_name: str, task_description: str) -> str:
        """Spawns a subagent to handle a specific task in parallel."""
        sub_backend = ChatBackend(self.parent.config, self.parent.personas.get(agent_name.lower(), self.parent.prompt))
        await sub_backend.initialize()
        try:
            response, _ = await sub_backend.chat(task_description)
            result = response.text if hasattr(response, 'text') else str(response)
            return f"[Subagent:{agent_name}] Result: {result[:100]}..."
        except Exception as e:
            return f"[Subagent:{agent_name}] Error: {e}"
        finally:
            await sub_backend.close()

    def get_graph_status(self) -> dict:
        return {tid: node.status for tid, node in self.task_graph.items()}

    def render_mission_control(self) -> str:
        """Returns a string/markdown representation of the current MAS state."""
        if not self.goal: return "No active mission goals set."
        status = f"### Mission Control\n**Target Goal**: {self.goal}\n\n"
        for tid, node in self.task_graph.items():
            status += f"- [{node.status.upper()}] {node.description} (ID: {tid})\n"
        return status
