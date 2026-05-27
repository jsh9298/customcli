from .base import BaseHandler
from rich.panel import Panel

class SessionHandlers(BaseHandler):
    """[Domain Layer] Handles session persistence and history manipulation."""

    async def save(self, ctx, *args):
        name = args[0] if args else None
        saved = self.cli.session_manager.save_session(self.cli.backend.history, self.cli.protector._mask_map, self.cli.protector._unmask_map, name)
        self.cli.ui.print_success(f"Session saved as: {saved}")

    async def load(self, ctx, *args):
        sessions = self.cli.session_manager.list_sessions()
        if args and args[0] in sessions:
            name = args[0]
        elif args and args[0].isdigit() and int(args[0]) < len(sessions):
            name = sessions[int(args[0])]
        else:
            if not sessions:
                self.cli.ui.print_warning("No saved sessions.")
                return
            idx = await self.ask_selection("Load Session", sessions)
            if idx is not None:
                name = sessions[int(idx)]
            else: return

        data = self.cli.session_manager.load_session(name)
        if data:
            self.cli.backend.history, self.cli.protector._mask_map, self.cli.protector._unmask_map = data['history'], data['mask_map'], data['unmask_map']
            self.cli.ui.print_success(f"Session '{name}' restored.")

    async def rewind(self, ctx, *args):
        if not self.cli.backend or not self.cli.backend.history: return
        
        previews = [f"[{h['role'].upper()}] {h['content'][:60]}..." for h in self.cli.backend.history]
        idx = await self.ask_selection("Rewind to Step", previews)
        
        if idx is not None:
            self.cli.backend.history = self.cli.backend.history[:int(idx)+1]
            self.cli.ui.print_success("Rewound.")
