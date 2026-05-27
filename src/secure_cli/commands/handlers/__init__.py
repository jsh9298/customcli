from .system import SystemHandlers
from .ai import AIHandlers
from .session import SessionHandlers
from .tools import ToolHandlers

# For backward compatibility during transition or consolidated access
class CommandHandlers:
    """[Adapter] Unified interface for legacy or grouped command access."""
    def __init__(self, cli):
        self.cli = cli
        self.system = SystemHandlers(cli)
        self.ai = AIHandlers(cli)
        self.session = SessionHandlers(cli)
        self.tool = ToolHandlers(cli)

    # Proxy methods for legacy support if needed
    async def help(self, ctx, *args): await self.system.help(ctx, *args)
    async def rag(self, ctx, *args): await self.tool.rag(ctx, *args)
    async def goal(self, ctx, *args): await self.tool.goal(ctx, *args)
    async def commit(self, ctx, *args): 
        from secure_cli.utils.git import GitUtility
        res = GitUtility().commit_changes(" ".join(args) if args else "Update")
        self.cli.ui.print_info(res)
    async def inline(self, ctx, *args):
        from prompt_toolkit.application import run_in_terminal
        cmd = await run_in_terminal(lambda: self.cli.session.prompt_async("Inline: "))
        if cmd: await self.cli.chat_cycle(cmd)
