import difflib
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel

class DiffViewer:
    """코드 수정을 시각적으로 비교 분석합니다."""
    def __init__(self, console: Console):
        self.console = console

    def display_diff(self, old_text: str, new_text: str, filename: str):
        diff = list(difflib.unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}"
        ))
        if not diff:
            self.console.print(f"[info]No changes detected in {filename}.[/info]")
            return
        diff_text = "".join(diff)
        syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, title=f"🔍 Proposed Changes: {filename}", border_style="yellow"))
