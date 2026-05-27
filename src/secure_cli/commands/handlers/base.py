from typing import Any
from prompt_toolkit.application import run_in_terminal

class BaseHandler:
    """[Base Layer] Common utilities for all command handlers."""
    def __init__(self, cli: Any):
        self.cli = cli

    async def ask_selection(self, title: str, options: list):
        """Helper to get user selection via arrow-key menu."""
        # Note: prompt_toolkit dialogs handle their own terminal context
        return await self.cli.ui.prompt_choice(title, options)
