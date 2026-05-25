import logging
import json
import asyncio
import subprocess
from typing import Dict, Any, Callable, Awaitable, Optional

class MCPManager:
    """MCP(Model Context Protocol) 오케스트레이터 클래스."""
    def __init__(self, protector: Any):
        self.protector = protector
        self.logger = logging.getLogger("MCPManager")
        self.tools: Dict[str, Callable[..., Awaitable[Any]]] = {}
        self.external_servers: Dict[str, asyncio.subprocess.Process] = {}

    def register_tool(self, name: str, func: Callable[..., Awaitable[Any]]):
        self.tools[name] = func

    async def connect_external_stdio(self, name: str, command: str, args: list):
        """Stdio 기반 외부 MCP 서버에 연결합니다."""
        try:
            process = await asyncio.create_subprocess_exec(
                command, *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            self.external_servers[name] = process
            self.logger.info(f"Connected to external MCP server: {name}")
            return f"Connected to {name} MCP server."
        except Exception as e:
            return f"Failed to connect to MCP server {name}: {e}"

    async def execute_tool(self, name: str, **kwargs) -> Any:
        if name not in self.tools:
            # 외부 서버 도구 검색 로직 (생략, 현재는 등록된 도구만 지원)
            return f"Error: Tool '{name}' not found."
        try:
            result = await self.tools[name](**kwargs)
            if isinstance(result, str):
                return self.protector.mask(result)
            return result
        except Exception as e:
            self.logger.error(f"MCP Tool Execution Error ({name}): {e}")
            return f"Error executing tool '{name}': {str(e)}"
