import os
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from rich.theme import Theme
from typing import Optional, Any
from prompt_toolkit.formatted_text import HTML

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
        # Deprecated in favor of integrated prompt UI, but kept for compatibility
        pass

    def get_dashboard_toolbar(self, cwd: str, sandbox: str, model: str, usage: str, backend: str, mode: str):
        if self.detail_mode == "minimal": return ""
        width = self.console.width
        col_width = width // 6  # 6 columns now
        
        # Dashboard labels (Top row of toolbar)
        labels = [
            f"{'workspace (/directory)':<{col_width}}",
            f"{'sandbox':<{col_width}}",
            f"{'backend':<{col_width}}",
            f"{'work mode':<{col_width}}",
            f"{'/model':<{col_width}}",
            f"{'quota':>{width - (col_width * 5)}}"
        ]
        
        # Values (Bottom row of toolbar)
        values = [
            f"{cwd:<{col_width}}",
            f"{sandbox:<{col_width}}",
            f"{backend.upper():<{col_width}}",
            f"{mode.upper():<{col_width}}",
            f"{model:<{col_width}}",
            f"{usage:>{width - (col_width * 5)}}"
        ]
        
        return HTML(
            f'<style fg="ansigray">{"".join(labels)}</style>\n'
            f'{"".join(values)}'
        )

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
