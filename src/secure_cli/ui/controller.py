import os
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from rich.theme import Theme
from typing import Optional, Any

class UIController:
    """Manages all Rich-based TUI rendering for the workstation."""
    
    def __init__(self):
        self.theme = Theme({
            "info": "cyan", 
            "warning": "yellow", 
            "error": "bold red",
            "user": "bold green", 
            "agent": "bold magenta", 
            "chat": "bold blue",
            "token": "bold yellow",
            "thought": "italic dim white"
        })
        self.console = Console(theme=self.theme)
        self.detail_mode = "full"

    def render_header(self, mode: str, backend: str):
        if self.detail_mode == "minimal": return
        status = f" BACKEND: {backend.upper()} | MODE: {mode.upper()} | ? for help"
        self.console.print(status, style="on #333333 white", justify="left")

    def render_dashboard(self, cwd: str, sandbox: str, model: str, usage: str):
        if self.detail_mode == "minimal": return
        grid = Table.grid(expand=True)
        [grid.add_column(ratio=1) for _ in range(4)]
        grid.add_row(
            f"[dim]W:[/dim] {cwd}", 
            f"[dim]S:[/dim] {sandbox}", 
            f"[dim]M:[/dim] {model}", 
            f"[dim]Q:[/dim] {usage}"
        )
        self.console.print(grid)

    def print_info(self, text: str):
        self.console.print(f"[info]{text}[/info]")

    def print_warning(self, text: str):
        self.console.print(f"[warning]{text}[/warning]")

    def print_error(self, text: str):
        self.console.print(f"[error]{text}[/error]")

    def render_markdown(self, text: str):
        self.console.print(Markdown(text))

    def create_live_display(self, initial_renderable: Any = Markdown("")) -> Live:
        return Live(initial_renderable, refresh_per_second=4, vertical_overflow="visible")

    def render_thought_panel(self, thought: str):
        return Panel(thought, title="Thinking", border_style="thought")

    def display_versions(self, versions: dict):
        t = Table(title="System Versions")
        t.add_column("Library"); t.add_column("Version")
        for k, v in versions.items():
            t.add_row(k, v)
        self.console.print(t)

    def display_tools(self, tools: list):
        t = Table(title="Available MCP Tools")
        t.add_column("Name")
        for n in tools:
            t.add_row(n)
        self.console.print(t)
