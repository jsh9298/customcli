from .base import BaseHandler
from rich.panel import Panel
from rich.table import Table
import os
from datetime import datetime

class ToolHandlers(BaseHandler):
    """[Domain Layer] Handles external tools, RAG, and MCP with standardized arrow-key UI."""

    async def rag(self, ctx, *args):
        """Hybrid: RAG Knowledge Base Browser."""
        sub = args[0].lower() if args else "menu"
        if sub == "scan":
            self.cli.ui.print_info("🚀 Scanning workspace for RAG...")
            await self.cli.rag_engine.scan_and_index()
            self.cli.ui.print_success("Indexing complete.")
        elif sub == "clear":
            self.cli.rag_engine.index_data["files"] = {}
            self.cli.rag_engine.save_index()
            self.cli.ui.print_warning("RAG Index cleared.")
        elif sub == "menu":
            files = list(self.cli.rag_engine.index_data.get("files", {}).keys())
            options = ["Full Workspace Scan", "Browse Indexed Files", "Clear All Index"]
            idx = await self.ask_selection("RAG Engine Dashboard", options)
            
            if idx == '0': await self.rag(ctx, "scan")
            elif idx == '1':
                if not files: self.cli.ui.print_warning("No files indexed.")
                else:
                    f_names = [os.path.basename(f) for f in files]
                    f_idx = await self.ask_selection("Select File to Inspect", f_names)
                    if f_idx is not None:
                        path = files[int(f_idx)]
                        info = self.cli.rag_engine.index_data["files"][path]
                        self.cli.ui.print_info(f"Path: {path}\nChunks: {len(info['chunks'])}\nModified: {datetime.fromtimestamp(info['mtime'])}")
            elif idx == '2': await self.rag(ctx, "clear")

    async def goal(self, ctx, *args):
        """Hybrid: Set goal or show dashboard."""
        if args:
            goal_text = " ".join(args)
            self.cli.orchestrator.set_goal(goal_text)
            self.cli.ui.print_success(f"New Objective: {goal_text}")
        else:
            self.cli.ui.print_info("📊 Mission Control Dashboard")
            self.cli.ui.render_markdown(self.cli.orchestrator.render_mission_control())

    async def mcp(self, ctx, *args):
        """Hybrid: Direct manage or interactive menu."""
        if args:
            action = args[0].lower()
            if action == "list": self.cli.ui.print_info(f"Servers: {self.cli.mcp_manager.list_servers()}")
            return

        options = ["Connect New MCP Server", "List Active Servers", "Disconnect All"]
        idx = await self.ask_selection("MCP Management", options)
        
        if idx == '0':
            # Simplified input for connection
            cmd = await self.cli.session.prompt_async("Launch Command (e.g. npx ...): ")
            if cmd:
                res = await self.cli.mcp_manager.connect_external_stdio("new_server", cmd.split()[0], cmd.split()[1:])
                self.cli.ui.print_info(res)
        elif idx == '1':
            servers = self.cli.mcp_manager.list_servers() if hasattr(self.cli.mcp_manager, 'list_servers') else []
            self.cli.ui.print_info(f"Active: {servers}")

    async def grill_me(self, ctx, *args):
        """[Action] Activates intensive questioning mode."""
        self.cli.autonomy_level = "review"
        self.cli.prompt += "\n\nIMPORTANT: Ask at least 3 clarifying questions before execution."
        self.cli.ui.print_success("🔥 Grill-me mode active. Agent judgment enhanced.")
