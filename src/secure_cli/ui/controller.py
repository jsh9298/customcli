from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.markdown import Markdown
from rich.theme import Theme
from rich.text import Text
import re
from typing import Optional, Dict

class UITheme:
    """[Strategy Pattern] Defines different color palettes for the CLI."""
    THEMES = {
        "neon": {
            "info": "bold cyan",
            "warning": "bold yellow",
            "error": "bold red",
            "success": "bold green",
            "ai_name": "bold magenta",
            "user_name": "bold blue",
            "masked": "italic reverse magenta",
            "path": "underline yellow",
            "code_block": "white on #222222"
        },
        "hacker": {
            "info": "green",
            "warning": "bold green",
            "error": "bold red",
            "success": "bright_green",
            "ai_name": "bold bright_green",
            "user_name": "dim green",
            "masked": "black on green",
            "path": "green",
            "code_block": "green"
        },
        "classic": {
            "info": "blue",
            "warning": "yellow",
            "error": "red",
            "success": "green",
            "ai_name": "bold white",
            "user_name": "dim white",
            "masked": "magenta",
            "path": "cyan",
            "code_block": "white"
        }
    }

class UIController:
    """[Facade] Orchestrates theming and high-resolution TUI rendering."""
    
    def __init__(self, theme_name: str = "neon"):
        self.current_theme_name = theme_name
        self._apply_theme(theme_name)
        self.detail_mode = "full"

    def _apply_theme(self, name: str):
        colors = UITheme.THEMES.get(name, UITheme.THEMES["neon"])
        self.console = Console(theme=Theme(colors))
        self.palette = colors

    def set_theme(self, name: str):
        if name in UITheme.THEMES:
            self.current_theme_name = name
            self._apply_theme(name)
            return True
        return False

    def colorize_text(self, text: str) -> Text:
        """[Word-level Coloring] Analyzes text and applies granular styles."""
        rich_text = Text()
        
        # Split text into tokens (words, spaces, special chars)
        # This is a simplified regex; a production one would be more robust
        tokens = re.split(r'(\s+|\[.*?\]|@[\w./-]+|`.*?`)', text)
        
        for token in tokens:
            if not token: continue
            
            # 1. Masked keywords like [EMAIL], [CREDIT_CARD]
            if token.startswith('[') and token.endswith(']'):
                rich_text.append(token, style=self.palette["masked"])
            
            # 2. Paths or file references like @src/core.py
            elif token.startswith('@'):
                rich_text.append(token, style=self.palette["path"])
            
            # 3. Inline code blocks like `config`
            elif token.startswith('`') and token.endswith('`'):
                rich_text.append(token, style=self.palette["code_block"])
            
            # 4. Standard text
            else:
                rich_text.append(token)
        
        return rich_text

    def print_info(self, msg: str): self.console.print(f"[info]ℹ [/info] {msg}")
    def print_warning(self, msg: str): self.console.print(f"[warning]⚠ [/warning] {msg}")
    def print_error(self, msg: str): self.console.print(f"[error]✘ [/error] {msg}")
    def print_success(self, msg: str): self.console.print(f"[success]✔ [/success] {msg}")

    def render_thought_panel(self, thought: str):
        """Renders AI's thinking process in a distinct style."""
        return Panel(thought, title="💭 Agent Thoughts", border_style="dim", padding=(0, 1))

    async def prompt_choice(self, title: str, options: list) -> Optional[str]:
        """[Interactive Selection] Real arrow-key navigation with Esc/q to exit."""
        from prompt_toolkit.shortcuts import radiolist_dialog
        from prompt_toolkit.styles import Style as PromptStyle

        # Prepare values for radiolist (value, label)
        values = [(str(i), opt) for i, opt in enumerate(options)]
        
        # Custom dialog style to match our theme
        style = PromptStyle.from_dict({
            'dialog': 'bg:#222222',
            'dialog frame.label': 'bg:#ffffff #000000',
            'radiolist.current': 'bg:#445544 #ffffff bold',
            'button': 'bg:#333333 #ffffff',
            'button.focused': 'bg:#green #ffffff',
        })

        # Launch the dialog (this blocks until selection or cancel)
        result = await radiolist_dialog(
            title=title,
            text="Use arrow keys to select. Enter to confirm, Esc to cancel.",
            values=values,
            style=style
        ).run_async()

        return result # Returns index string or None if cancelled

    def display_interactive_menu(self, title: str, options: list):
        """[Legacy/Display Only] Renders a beautiful static selection menu."""
        t = Table(title=f" {title} ", border_style="cyan", box=None)
        t.add_column("Index", style="bold yellow")
        t.add_column("Option", style="white")
        
        for i, opt in enumerate(options):
            t.add_row(str(i), opt)
        
        self.console.print(Panel(t, border_style="cyan", expand=False))

    def get_dashboard_toolbar(self, cwd, sandbox, model, quota, mode, work_mode):
        return f" {mode.upper()} | {work_mode.upper()} | {model} | {quota} | {sandbox} | {cwd} "

    def get_style(self):
        from prompt_toolkit.styles import Style
        return Style.from_dict({
            'completion-menu.completion': 'bg:#333333 #ffffff',
            'completion-menu.completion.current': 'bg:#445544 #ffffff',
            'bottom-toolbar': 'bg:#111111 #ffffff',
        })
