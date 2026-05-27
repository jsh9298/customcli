import os
import sys
import subprocess
import pyperclip
import re
from datetime import datetime
from rich.table import Table
from rich.panel import Panel
from prompt_toolkit.application import run_in_terminal
from typing import Any, List

class CommandHandlers:
    """[Command Pattern] Implementation of all CLI slash commands."""
    
    def __init__(self, cli: Any):
        self.cli = cli

    # --- Utility Helpers ---
    async def _get_inline_input(self):
        return await self.cli.session.prompt_async("Inline Command: ")

    # --- Shared Commands ---
    async def help(self, ctx, *args):
        title = "Gemini CLI (Chat) Commands" if self.cli.cli_mode == 'chat' else "Antigravity CLI (Agents) Commands"
        t = Table(title=title, header_style="bold magenta")
        t.add_column("Command", style="cyan"); t.add_column("Description", style="dim"); t.add_column("Type")
        for cmd in self.cli.commands.get_commands(filter_tag=self.cli.cli_mode):
            desc = self.cli.commands.get_description(cmd)
            t.add_row(cmd, desc, "Alias" if cmd in self.cli.commands._aliases else "Core")
        self.cli.ui.console.print(t)

    async def model(self, ctx, *args):
        if args: 
            self.cli.config['agent']['model'] = args[0]
            ctx['should_reinit'] = True
            self.cli.ui.print_info(f"Model: {args[0]}")

    async def theme(self, ctx, *args):
        if args:
            if self.cli.ui.set_theme(args[0].lower()):
                self.cli.ui.print_success(f"Theme: {args[0]}")
            else:
                self.cli.ui.print_error(f"Available: neon, hacker, classic")
        else:
            self.cli.ui.print_info(f"Current: {self.cli.ui.current_theme_name}")

    async def autonomy(self, ctx, *args):
        if args: 
            self.cli.autonomy_level = args[0].lower()
            if hasattr(self.cli, 'terminal_adapter'):
                self.cli.terminal_adapter.autonomy_level = self.cli.autonomy_level
            self.cli.ui.print_info(f"Autonomy: {self.cli.autonomy_level.upper()}")

    async def inline(self, ctx, *args):
        cmd = await run_in_terminal(self._get_inline_input)
        if cmd and cmd.strip():
            cmd = cmd.strip()
            if cmd.startswith('!'): await self.cli.terminal_adapter.execute(cmd[1:])
            elif cmd.startswith('/'): await self.cli.commands.handle(cmd, ctx)
            else: await self.cli.chat_cycle(cmd)

    async def clear(self, ctx, *args):
        self.cli.ui.console.clear()

    async def exit(self, ctx, *args):
        sys.exit(0)

    # --- Unified Handlers ---
    async def session_unified(self, ctx, *args):
        sub = args[0].lower() if args else "list"
        if sub == "save": await self.save(ctx, *args[1:])
        elif sub == "load": await self.load(ctx, *args[1:])
        elif sub == "list": await self.sessions(ctx)
        elif sub in ["resume", "switch"]: await self.resume(ctx)
        elif sub == "fork": await self.fork(ctx)

    async def config_unified(self, ctx, *args):
        sub = args[0].lower() if args else "show"
        if sub == "show": self.cli.ui.console.print_json(data=self.cli.config)
        elif sub == "model": await self.model(ctx, *args[1:])
        elif sub == "agent": await self.cli.handlers.agents(ctx, *args[1:])
        elif sub == "mode": 
            if len(args) > 1:
                m = args[1].lower()
                self.cli.cli_mode = "agents" if m in ["agent", "agents"] else "chat"
                ctx['should_reinit'] = True
        elif sub == "refresh": self.cli.re_initialize(); self.cli.ui.print_info("Refreshed.")

    async def usage_unified(self, ctx, *args):
        sub = args[0].lower() if args else "session"
        s = self.cli.telemetry.get_detailed_stats()
        if sub == "session": self.cli.ui.print_info(f"Session Tokens: {s['session']:,}")
        elif sub == "total": self.cli.ui.print_info(f"Daily: {s['daily']:,} / {s.get('hard_limit', '∞')}")

    # --- Feature Handlers ---
    async def rag(self, ctx, *args):
        sub = args[0] if args else "status"
        if sub == "scan":
            self.cli.ui.print_info("RAG Scanning...")
            await self.cli.rag_engine.scan_and_index()
            self.cli.ui.print_info("Done.")
        elif sub == "status":
            s = self.cli.rag_engine.index_data
            self.cli.ui.print_info(f"RAG: {len(s['files'])} files. Last: {s['last_scan']}")

    async def commit(self, ctx, *args):
        msg = ' '.join(args) if args else 'Update'
        res = self.cli.git.commit_changes(msg)
        self.cli.ui.print_info(f"Git: {res}")

    async def mcp(self, ctx, *args):
        if len(args) >= 3:
            res = await self.cli.mcp_manager.connect_external_stdio(args[1], args[2], args[3:])
            self.cli.ui.print_info(res)

    async def save(self, ctx, *args):
        name = args[0] if args else None
        saved = self.cli.session_manager.save_session(self.cli.backend.history, self.cli.protector._mask_map, self.cli.protector._unmask_map, name)
        self.cli.ui.print_info(f"Saved: {saved}")

    async def load(self, ctx, *args):
        if not args: return
        data = self.cli.session_manager.load_session(args[0])
        if data:
            self.cli.backend.history, self.cli.protector._mask_map, self.cli.protector._unmask_map = data['history'], data['mask_map'], data['unmask_map']
            self.cli.ui.print_info(f"Loaded: {args[0]}")

    async def sessions(self, ctx, *args):
        self.cli.ui.print_info(f"Sessions: {self.cli.session_manager.list_sessions()}")

    async def resume(self, ctx, *args):
        latest = self.cli.session_manager.get_latest_session()
        if latest: await self.load(ctx, latest)

    async def fork(self, ctx, *args):
        name = f"fork_{datetime.now().strftime('%H%M%S')}"
        await self.save(ctx, name)

    async def agents(self, ctx, *args):
        if args:
            self.cli.active_persona = args[0].lower()
            self.cli.re_initialize()
            ctx['should_reinit'] = True
        else:
            # Interactive Menu for Agents
            personas = list(self.cli.personas.keys())
            self.cli.ui.display_interactive_menu("Persona Selection", personas)
            
            async def _get_selection():
                return await self.cli.session.prompt_async("Select Persona Index (or name): ")
            
            selection = await run_in_terminal(_get_selection)
            if selection:
                if selection.isdigit() and int(selection) < len(personas):
                    self.cli.active_persona = personas[int(selection)]
                else:
                    self.cli.active_persona = selection.lower()
                
                if self.cli.active_persona in self.cli.personas:
                    self.cli.re_initialize()
                    ctx['should_reinit'] = True
                    self.cli.ui.print_success(f"Persona switched to '{self.cli.active_persona}'")

    async def rewind(self, ctx, *args):
        if not self.cli.backend or not self.cli.backend.history:
            self.cli.ui.print_warning("No history to rewind.")
            return

        # Interactive Menu for Rewind
        history_previews = [f"[{h['role'].upper()}] {h['content'][:50]}..." for h in self.cli.backend.history]
        self.cli.ui.display_interactive_menu("Conversation Rewind", history_previews)
        
        async def _get_index():
            return await self.cli.session.prompt_async("Select index to roll back to: ")
        
        idx_str = await run_in_terminal(_get_index)
        if idx_str and idx_str.isdigit():
            idx = int(idx_str)
            if idx < len(self.cli.backend.history):
                self.cli.backend.history = self.cli.backend.history[:idx+1]
                self.cli.ui.print_success(f"History rewound to step {idx}.")
