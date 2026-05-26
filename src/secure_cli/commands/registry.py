from typing import Dict, Any, Callable, Awaitable, List, Set

class CommandRegistry:
    """Manages slash command registration and dispatching."""
    
    def __init__(self):
        self._handlers: Dict[str, Callable[..., Awaitable[None]]] = {}
        self._commands: List[str] = []
        self._descriptions: Dict[str, str] = {}
        self._aliases: Dict[str, str] = {} # alias -> canonical
        self._metadata: Dict[str, Set[str]] = {} # command -> tags (e.g. 'chat', 'agents')

    def register(self, cmd: str, handler: Callable[..., Awaitable[None]], description: str = "", tags: List[str] = None):
        cmd = cmd.lower()
        self._handlers[cmd] = handler
        if cmd not in self._commands:
            self._commands.append(cmd)
        self._descriptions[cmd] = description
        if tags:
            self._metadata[cmd] = set(tags)

    def alias(self, alias_name: str, target_cmd: str):
        alias_name = alias_name.lower()
        target_cmd = target_cmd.lower()
        self._aliases[alias_name] = target_cmd
        if alias_name not in self._commands:
            self._commands.append(alias_name)
        # Inherit description if not already set
        if alias_name not in self._descriptions and target_cmd in self._descriptions:
            self._descriptions[alias_name] = f"Alias for {target_cmd}"

    def get_commands(self, filter_tag: str = None) -> List[str]:
        if not filter_tag:
            return sorted(self._commands)
        
        filtered = []
        for cmd in self._commands:
            canonical = self._aliases.get(cmd, cmd)
            tags = self._metadata.get(canonical, set())
            if filter_tag in tags:
                filtered.append(cmd)
        return sorted(filtered)
    
    def get_description(self, cmd: str) -> str:
        return self._descriptions.get(cmd.lower(), "")

    async def handle(self, cmd_line: str, context: Any) -> bool:
        """Parses and dispatches a command line."""
        parts = cmd_line.split()
        if not parts: return False
        
        base_cmd = parts[0].lower()
        
        # Resolve alias
        canonical = self._aliases.get(base_cmd, base_cmd)
        
        if canonical in self._handlers:
            args = parts[1:]
            await self._handlers[canonical](context, *args)
            return True
        return False
