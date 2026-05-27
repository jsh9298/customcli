import yaml
import os
from .base import BaseHandler

class SystemHandlers(BaseHandler):
    """[Infrastructure Layer] System shells, diagnostic tools, and Persistent Config."""

    async def mode(self, ctx, *args):
        """Dedicated mode switcher with Hybrid CLI/UI support."""
        if args:
            m = args[0].lower()
            new_mode = "agents" if m in ["agent", "agents", "agy"] else "chat"
            if self.cli.cli_mode != new_mode:
                self.cli.cli_mode = new_mode
                ctx['should_reinit'] = True
                self.cli.ui.print_success(f"Mode: {new_mode.upper()}")
            return

        # Arrow-key selection
        modes = ["Chat (Gemini style)", "Agents (Antigravity style)"]
        idx = await self.ask_selection("Switch Workstation Mode", modes)
        if idx is not None:
            self.cli.cli_mode = "chat" if idx == '0' else "agents"
            ctx['should_reinit'] = True
            self.cli.ui.print_success(f"Mode: {self.cli.cli_mode.upper()}")

    async def config(self, ctx, *args):
        """[Interactive UI] Persistent settings editor."""
        options = [
            f"Model ({self.cli.config['agent']['model']})",
            f"Temperature ({self.cli.config['agent']['temperature']})",
            f"Sandbox ({'ON' if self.cli.sandbox.enabled else 'OFF'})",
            "Reload from File"
        ]
        
        idx = await self.ask_selection("Workstation Settings", options)
        if idx is None: return
        
        updated = False
        if idx == '0':
            models = self.cli.available_models
            m_idx = await self.ask_selection("Select New Model", models)
            if m_idx is not None:
                self.cli.config['agent']['model'] = models[int(m_idx)]
                updated = True
        
        elif idx == '1':
            from prompt_toolkit import prompt
            temp = await self.cli.session.prompt_async("New Temperature (0.0 - 1.0): ")
            try:
                self.cli.config['agent']['temperature'] = float(temp)
                updated = True
            except: self.cli.ui.print_error("Invalid input.")
            
        elif idx == '2':
            self.cli.sandbox.toggle()
            self.cli.config['enableTerminalSandbox'] = self.cli.sandbox.enabled
            updated = True
            
        elif idx == '3':
            self.cli.re_initialize()
            ctx['should_reinit'] = True

        if updated:
            self.save_config_to_file()
            self.cli.ui.print_success("Settings saved and applied.")
            ctx['should_reinit'] = True

        if updated:
            # Save to agent_config.yaml
            self.save_config_to_file()
            self.cli.ui.print_success("Settings saved to agent_config.yaml and applied.")
            ctx['should_reinit'] = True

    def save_config_to_file(self):
        """Writes current self.cli.config back to agent_config.yaml."""
        path = "agent_config.yaml"
        try:
            # We preserve existing formatting by just dumping the dict
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(self.cli.config, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            self.cli.ui.print_error(f"Failed to save config: {e}")

    async def exit(self, ctx, *args):
        import sys
        sys.exit(0)

    async def clear(self, ctx, *args):
        self.cli.ui.console.clear()

    async def shells(self, ctx, *args):
        """Hybrid: Process monitoring dashboard."""
        if args:
            pid = args[0]
            self.cli.ui.print_info(f"Inspecting PID {pid}... (Log streaming not yet in PTY)")
            return

        from rich.table import Table
        from rich.panel import Panel
        table = Table(title="Background Process Manager", border_style="cyan")
        table.add_column("PID", style="bold yellow"); table.add_column("Command"); table.add_column("Status")
        table.add_row("Main", "UnifiedSecureCLI", "RUNNING")
        
        self.cli.ui.console.print(Panel(table, border_style="cyan"))
        options = ["Refresh List", "Kill All Processes", "Back"]
        self.cli.ui.display_interactive_menu("Shell Controls", options)
        await self.ask_selection("Option Index: ")

    async def permissions(self, ctx, *args):
        """Hybrid: Fast toggle or interactive permission editor."""
        levels = ["review", "always", "strict"]
        if args and args[0].lower() in levels:
            self.cli.autonomy_level = args[0].lower()
            self.cli.ui.print_success(f"Autonomy: {self.cli.autonomy_level.upper()}")
            return

        options = [
            "[review] Ask for confirmation on all tools",
            "[always] Trust all AI tool executions (YOLO)",
            "[strict] Only allow read-only operations"
        ]
        self.cli.ui.display_interactive_menu("Permission Governance", options)
        idx = await self.ask_selection("Level Index: ")
        if idx and idx.isdigit() and int(idx) < len(levels):
            self.cli.autonomy_level = levels[int(idx)]
            self.cli.ui.print_success(f"Level set to {self.cli.autonomy_level.upper()}")
