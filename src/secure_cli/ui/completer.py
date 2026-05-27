import os
import re
from prompt_toolkit.completion import Completer, Completion
from typing import Any

class SmartCompleter(Completer):
    """[Strategy Pattern] Intelligent completion for commands and file paths."""
    
    def __init__(self, cli: Any):
        self.cli = cli

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        
        # 1. Slash Command Completion
        if text.startswith('/'):
            # Get current available commands from registry
            mode_tag = self.cli.cli_mode
            all_cmds = self.cli.commands.get_commands(filter_tag=mode_tag)
            
            parts = text.split()
            if len(parts) <= 1 and not text.endswith(' '):
                for cmd in all_cmds:
                    if cmd.startswith(text):
                        desc = self.cli.commands.get_description(cmd)
                        yield Completion(cmd, start_position=-len(text), display_meta=desc)
                return

            # 2. Sub-command / Argument Completion (e.g., /theme [tab])
            cmd = parts[0].lower()
            arg_prefix = parts[-1] if not text.endswith(' ') else ""
            
            if cmd == '/theme':
                themes = ["neon", "hacker", "classic"]
                for t in themes:
                    if t.startswith(arg_prefix):
                        yield Completion(t, start_position=-len(arg_prefix))
            
            elif cmd == '/model':
                for m in self.cli.available_models:
                    if m.startswith(arg_prefix):
                        yield Completion(m, start_position=-len(arg_prefix))

        # 3. File Reference Completion (@path)
        if '@' in text:
            match = re.search(r'@([^\s]*)$', text)
            if match:
                path_prefix = match.group(1)
                dirname = os.path.dirname(path_prefix) or "."
                basename = os.path.basename(path_prefix)
                try:
                    if os.path.isdir(dirname):
                        for f in os.listdir(dirname):
                            if f.startswith(basename):
                                is_dir = os.path.isdir(os.path.join(dirname, f))
                                display_f = f + "/" if is_dir else f
                                yield Completion(display_f, start_position=-len(basename))
                except: pass
