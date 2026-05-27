import asyncio
import pyperclip
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.formatted_text import HTML

class UIKeyBindings:
    """[Observer Pattern] Manages all TUI keyboard shortcuts."""
    
    def __init__(self, cli):
        self.cli = cli
        self.kb = KeyBindings()
        self._setup_bindings()

    def _setup_bindings(self):
        is_chat = Condition(lambda: self.cli.cli_mode == 'chat')
        is_agents = Condition(lambda: self.cli.cli_mode == 'agents')

        # --- Global Shortcuts ---
        @self.kb.add('s-tab')
        def _(e):
            """Work Mode Cycle (Default -> Auto-Edit -> Plan)"""
            self.cli.current_mode_idx = (self.cli.current_mode_idx + 1) % len(self.cli.modes)
            self.cli.ui.print_info(f"Work Mode: {self.cli.modes[self.cli.current_mode_idx].upper()}")
            
        @self.kb.add('tab', 'tab')
        def _(e):
            """UI Detail Toggle"""
            self.cli.ui.detail_mode = "minimal" if self.cli.ui.detail_mode == "full" else "full"
            self.cli.ui.print_info(f"UI Detail: {self.cli.ui.detail_mode.upper()}")
            
        @self.kb.add('escape')
        def _(e):
            """Abort current task / stream"""
            if self.cli._current_task and not self.cli._current_task.done():
                self.cli._current_task.cancel()
                self.cli.ui.print_warning("\n[Abort] 작업이 중단되었습니다.")

        @self.kb.add('c-l')
        def _(e):
            """Clear Screen"""
            self.cli.ui.console.clear()

        @self.kb.add('c-o')
        def _(e):
            """Debug Console Toggle"""
            self.cli.debug_log_enabled = not self.cli.debug_log_enabled
            self.cli.ui.print_info(f"Debug Log: {'ON' if self.cli.debug_log_enabled else 'OFF'}")

        # --- Agents Mode Specifics ---
        @self.kb.add('escape', 'escape', filter=is_agents)
        def _(e):
            e.app.current_buffer.text = ""
            self.cli.ui.print_info("Input buffer cleared.")

        @self.kb.add('c-y', filter=is_agents)
        def _(e):
            txt = e.app.current_buffer.text
            if txt:
                try: pyperclip.copy(txt); self.cli.ui.print_info("Yanked to clipboard.")
                except: self.cli.ui.print_warning("Yank failed.")

        @self.kb.add('c-k', filter=is_agents)
        def _(e):
            self.cli._immediate_approval = True
            self.cli.ui.print_info("Subagent approval flag SET.")

        # --- Chat Mode Specifics ---
        @self.kb.add('escape', 'escape', filter=is_chat)
        def _(e):
            asyncio.create_task(self.cli.launch_rewind_ui())

        @self.kb.add('c-y', filter=is_chat)
        def _(e):
            self.cli.autonomy_level = "always" if self.cli.autonomy_level != "always" else "review"
            self.cli.ui.print_info(f"YOLO Mode: {'ACTIVE' if self.cli.autonomy_level == 'always' else 'OFF'}")

        @self.kb.add('\\', 'enter', filter=is_chat)
        def _(e):
            e.app.current_buffer.insert_text('\n')

    def get_bindings(self):
        return self.kb
