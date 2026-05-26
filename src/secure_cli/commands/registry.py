from typing import Dict, Any, Callable, Awaitable, List

class CommandRegistry:
    """Manages slash command registration and dispatching."""
    
    def __init__(self):
        self._handlers: Dict[str, Callable[..., Awaitable[None]]] = {}
        self._commands: List[str] = []
        self._descriptions: Dict[str, str] = {}

    def register(self, cmd: str, handler: Callable[..., Awaitable[None]], description: str = ""):
        self._handlers[cmd.lower()] = handler
        if cmd not in self._commands:
            self._commands.append(cmd)
        self._descriptions[cmd.lower()] = description

    def get_commands(self) -> List[str]:
        return sorted(self._commands)
    
    def get_description(self, cmd: str) -> str:
        return self._descriptions.get(cmd.lower(), "")

    async def handle(self, cmd_line: str, context: Any) -> bool:
        """Parses and dispatches a command line."""
        parts = cmd_line.split()
        if not parts: return False
        
        base_cmd = parts[0].lower()
        if base_cmd in self._handlers:
            args = parts[1:]
            await self._handlers[base_cmd](context, *args)
            return True
        return False
