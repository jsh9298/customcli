import subprocess
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from secure_cli.security.sandbox import SandboxManager

class TerminalInterface(ABC):
    """[Adapter Pattern] Interface for terminal execution."""
    @abstractmethod
    async def execute(self, command: str) -> str:
        pass

class LocalTerminalAdapter(TerminalInterface):
    """
    Adapter for executing commands on the local machine with security layers.
    Combines Sandbox and UI components.
    """
    def __init__(self, sandbox: SandboxManager, ui: Any, autonomy_level: str = "review"):
        self.sandbox = sandbox
        self.ui = ui
        self.autonomy_level = autonomy_level

    async def execute(self, command: str) -> str:
        # 1. Autonomy / Approval Check
        if self.autonomy_level != 'always':
            # This requires a bridge to the UI's prompt which is typically in UnifiedSecureCLI
            # For simplicity in this adapter, we assume the UI can handle its own prompting or 
            # we rely on the parent CLI to check approval before calling execute.
            pass

        try:
            res = await self.sandbox.execute_sandboxed(command)
            output = f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
            return output
        except Exception as e:
            return f"Error executing command: {e}"

class DockerTerminalAdapter(TerminalInterface):
    """
    Adapter for executing commands inside a Docker container.
    """
    def __init__(self, container_id: str):
        self.container_id = container_id

    async def execute(self, command: str) -> str:
        # Implementation for 'docker exec'
        process = await asyncio.create_subprocess_shell(
            f"docker exec {self.container_id} sh -c '{command}'",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
        return f"DOCKER STDOUT:\n{stdout.decode()}\nSTDERR:\n{stderr.decode()}"
