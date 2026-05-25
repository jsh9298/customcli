import asyncio
import os
import sys
import yaml
import json
import argparse
import logging
import pyperclip
import subprocess
import re
import fnmatch
import inspect
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from dotenv import load_dotenv
from importlib import metadata

# UI & SDK imports
from rich.markdown import Markdown
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.patch_stdout import patch_stdout

# Tiered Package Components
from secure_cli.security.protector import SecurityProtector
from secure_cli.security.sandbox import SandboxManager
from secure_cli.state.session import SessionManager
from secure_cli.state.telemetry import TelemetryManager
from secure_cli.ui.controller import UIController
from secure_cli.ui.viewer import DiffViewer
from secure_cli.commands.registry import CommandRegistry
from secure_cli.commands.plugins import PluginManager
from secure_cli.agent.orchestrator import AgentOrchestrator
from secure_cli.agent.group import GroupChatManager
from secure_cli.utils.mcp import MCPManager
from secure_cli.utils.compressor import ContextCompressor
from secure_cli.utils.skills import SkillManager
from secure_cli.utils.git import GitUtility
from secure_cli.utils.scheduler import TaskScheduler

# Backends
from secure_cli.agent.backends.agent_backend import AgentBackend
from secure_cli.agent.backends.chat_backend import ChatBackend

# --- Global Config ---
logging.basicConfig(filename='unified_secure_cli.log', level=logging.DEBUG)

class SmartCompleter(Completer):
    def __init__(self, command_registry, plugin_manager):
        self.registry = command_registry
        self.plugins = plugin_manager
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith('/'):
            cmds = self.registry.get_commands() + self.plugins.get_plugin_commands()
            for cmd in sorted(set(cmds)):
                if cmd.startswith(text):
                    yield Completion(cmd, start_position=-len(text))
        elif '@' in text:
            match = re.search(r'@([^\s]*)$', text)
            if match:
                path_prefix = match.group(1)
                dirname = os.path.dirname(path_prefix) or "."
                basename = os.path.basename(path_prefix)
                try:
                    if os.path.isdir(dirname):
                        for f in os.listdir(dirname):
                            if f.startswith(basename):
                                yield Completion(f, start_position=-len(basename))
                except: pass

class ConfigResolver:
    GLOBAL_ROOT = os.path.expanduser('~/.gemini/antigravity-cli')
    PROJECT_ROOT = os.path.abspath('.antigravity')
    def __init__(self):
        for p in [self.GLOBAL_ROOT, os.path.join(self.GLOBAL_ROOT, 'skills'), self.PROJECT_ROOT]:
            os.makedirs(p, exist_ok=True)
    def resolve_settings(self):
        base = {"agent": {"model": "gemini-1.5-flash", "temperature": 0.7}, "enableTerminalSandbox": False, "exclude_paths": [".env", ".git", ".sessions", "*.log"]}
        for p in [os.path.join(self.GLOBAL_ROOT, 'settings.json'), os.path.join(self.PROJECT_ROOT, 'settings.json'), 'settings.json', 'agent_config.yaml']:
            if not os.path.exists(p): continue
            try:
                with open(p, 'r') as f:
                    data = json.load(f) if p.endswith('.json') else yaml.safe_load(f)
                    if isinstance(data, dict): self.deep_merge(base, data)
            except: pass
        return base
    def deep_merge(self, base, override):
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self.deep_merge(base[k], v)
            else: base[k] = v
    def discover_personas(self):
        p = {"default": "You are a helpful unified secure assistant."}
        paths = [os.path.join(self.GLOBAL_ROOT, 'agents.md'), os.path.join(self.PROJECT_ROOT, 'agents.md'), 'agents.md']
        for path in paths:
            if not os.path.exists(path): continue
            try:
                with open(path, 'r') as f:
                    sections = re.split(r'^#\s+', f.read(), flags=re.MULTILINE)
                    for s in sections:
                        if not s.strip(): continue
                        lines = s.split('\n')
                        p[lines[0].strip().lower()] = '\n'.join(lines[1:]).strip()
            except: pass
        return p

class UnifiedSecureCLI:
    def __init__(self, initial_mode: str = "agent"):
        self.protector = SecurityProtector()
        self.resolver = ConfigResolver()
        self.config = self.resolver.resolve_settings()
        
        # Wire state config
        state_cfg = self.config.get('state', {})
        self.session_manager = SessionManager(expiry_days=state_cfg.get('expiry_days', 7))
        self.mcp_manager = MCPManager(self.protector)
        self.ui = UIController()
        self.telemetry = TelemetryManager(hard_limit=state_cfg.get('hard_limit', 0))
        self.orchestrator = AgentOrchestrator(self)
        self.sandbox = SandboxManager()
        self.plugins = PluginManager(os.path.join(self.resolver.GLOBAL_ROOT, 'plugins'))
        self.diff_viewer = DiffViewer(self.ui.console)
        self.commands = CommandRegistry()
        self.skill_manager = SkillManager(os.path.join(self.resolver.GLOBAL_ROOT, 'skills'))
        self.git = GitUtility()
        self.scheduler = TaskScheduler(self.chat_cycle)
        self.group_chat = GroupChatManager(self)
        
        self.cli_mode = initial_mode
        self.backend = None
        self.modes = ['default', 'auto-edit', 'plan']
        self.current_mode_idx = 0
        self.autonomy_level = "review"
        self.last_response = ""
        self.last_shell_output = ""
        self.efficient_mode = False
        self.multiline = False
        self.debug_log_enabled = False
        self.active_persona = "default"
        self._immediate_approval = False
        
        self.re_initialize()
        self.register_core_commands()
        self.plugins.load_plugins()
        
        # Keyboard Bindings
        self.kb = KeyBindings()
        @self.kb.add('s-tab')
        def _(e):
            self.current_mode_idx = (self.current_mode_idx + 1) % len(self.modes)
            self.ui.print_info(f"Mode: {self.modes[self.current_mode_idx].upper()}")
            
        @self.kb.add('tab', 'tab')
        def _(e):
            self.ui.detail_mode = "minimal" if self.ui.detail_mode == "full" else "full"
            self.ui.print_info(f"UI Detail: {self.ui.detail_mode.upper()}")
            
        @self.kb.add('escape', 'escape')
        def _(e):
            asyncio.create_task(self.launch_rewind_ui())
            
        @self.kb.add('c-y')
        def _(e):
            self.autonomy_level = "always" if self.autonomy_level != "always" else "review"
            self.ui.print_info(f"Autonomy: {self.autonomy_level.upper()}")

        @self.kb.add('c-o')
        def _(e):
            self.debug_log_enabled = not self.debug_log_enabled
            self.ui.print_info(f"Debug Log: {'ON' if self.debug_log_enabled else 'OFF'}")

        @self.kb.add('?')
        def _(e):
            if not e.app.current_buffer.text:
                asyncio.create_task(self.cmd_help({}, None))

        @self.kb.add('c-k')
        def _(e):
            # Immediate approval logic (simulation for now, but can be used to set a flag)
            self.ui.print_info("Ctrl+K: Immediate Approval triggered (Flag set).")
            self._immediate_approval = True

        @self.kb.add('c-j')
        def _(e):
            self.ui.print_info("Ctrl+J: Jump to Subagent View (Mission Control).")
            asyncio.create_task(self.cmd_mission({}, None))

        @self.kb.add('c-i')
        def _(e):
            asyncio.create_task(self.cmd_inline({}, None))

        self.session = PromptSession(
            history=FileHistory(os.path.expanduser('~/.unified_secure_history')),
            completer=SmartCompleter(self.commands, self.plugins),
            key_bindings=self.kb
        )

    def register_core_commands(self):
        self.commands.register('/help', self.cmd_help)
        self.commands.register('/mode', self.cmd_mode)
        self.commands.register('/reset', self.cmd_reset)
        self.commands.register('/history', self.cmd_history)
        self.commands.register('/undo', self.cmd_undo)
        self.commands.register('/config', self.cmd_config)
        self.commands.register('/verbose', self.cmd_verbose)
        self.commands.register('/exit', self.cmd_exit)
        self.commands.register('/quit', self.cmd_exit)
        self.commands.register('/save', self.cmd_save)
        self.commands.register('/load', self.cmd_load)
        self.commands.register('/sessions', self.cmd_sessions)
        self.commands.register('/resume', self.cmd_resume)
        self.commands.register('/rewind', self.cmd_rewind)
        self.commands.register('/copy', self.cmd_copy)
        self.commands.register('/multiline', self.cmd_multiline)
        self.commands.register('/model', self.cmd_model)
        self.commands.register('/plan', self.cmd_plan)
        self.commands.register('/agents', self.cmd_agents)
        self.commands.register('/autonomy', self.cmd_autonomy)
        self.commands.register('/versions', self.cmd_versions)
        self.commands.register('/clear', self.cmd_clear)
        self.commands.register('/efficient', self.cmd_efficient)
        self.commands.register('/tools', self.cmd_tools)
        self.commands.register('/usage', self.cmd_usage)
        self.commands.register('/stats', self.cmd_stats)
        self.commands.register('/token', self.cmd_usage)
        self.commands.register('/goal', self.cmd_goal)
        self.commands.register('/mission', self.cmd_mission)
        self.commands.register('/sandbox', self.cmd_sandbox)
        self.commands.register('/file', self.cmd_file)
        self.commands.register('/export', self.cmd_export)
        self.commands.register('/refresh', self.cmd_refresh)
        self.commands.register('/fork', self.cmd_fork)
        self.commands.register('/peek', self.cmd_peek)
        self.commands.register('/compress', self.cmd_compress)
        self.commands.register('/skills', self.cmd_skills)
        self.commands.register('/pin', self.cmd_pin)
        self.commands.register('/unpin', self.cmd_unpin)
        self.commands.register('/commit', self.cmd_commit)
        self.commands.register('/protect', self.cmd_protect)
        self.commands.register('/unprotect', self.cmd_unprotect)
        self.commands.register('/schedule', self.cmd_schedule)
        self.commands.register('/group', self.cmd_group)
        self.commands.register('/mcp', self.cmd_mcp)

    # --- Command Handlers ---
    async def cmd_help(self, ctx, *args):
        t = Table(title="Unified Workstation Commands")
        t.add_column("Command"); t.add_column("Source")
        for cmd in self.commands.get_commands(): t.add_row(cmd, "Core")
        for cmd in self.plugins.get_plugin_commands(): t.add_row(cmd, "Plugin")
        self.ui.console.print(t)
    async def cmd_mode(self, ctx, *args):
        if args: self.cli_mode = args[0].lower(); ctx['should_reinit'] = True
    async def cmd_reset(self, ctx, *args):
        if self.backend: self.backend.history.clear()
        self.protector.clear(); self.ui.print_info("Session and security mappings cleared.")
    async def cmd_history(self, ctx, *args):
        if not self.backend: return
        for i, turn in enumerate(self.backend.history): self.ui.console.print(f"[{i}] {turn}")
    async def cmd_undo(self, ctx, *args):
        if self.backend and len(self.backend.history) >= 2:
            self.backend.history.pop(); self.backend.history.pop()
            self.ui.print_info("Last interaction removed from history.")
    async def cmd_config(self, ctx, *args): self.ui.console.print_json(data=self.config)
    async def cmd_verbose(self, ctx, *args):
        self.ui.print_info("Verbose mode is implicitly active via [Verbose] logs.")
    async def cmd_exit(self, ctx, *args): sys.exit(0)
    async def cmd_save(self, ctx, *args):
        name = args[0] if args else None
        saved = self.session_manager.save_session(self.backend.history, self.protector._mask_map, self.protector._unmask_map, name)
        self.ui.print_info(f"Session saved to disk: {saved}")
    async def cmd_load(self, ctx, *args):
        if not args: return
        data = self.session_manager.load_session(args[0])
        if data:
            self.backend.history = data['history']
            self.protector._mask_map = data['mask_map']
            self.protector._unmask_map = data['unmask_map']
            self.ui.print_info("Session state restored.")
    async def cmd_sessions(self, ctx, *args): self.ui.print_info(f"Stored Sessions: {self.session_manager.list_sessions()}")
    async def cmd_resume(self, ctx, *args):
        latest = self.session_manager.get_latest_session()
        if latest: await self.cmd_load(ctx, latest)
    async def cmd_rewind(self, ctx, *args): await self.launch_rewind_ui()
    async def cmd_copy(self, ctx, *args): pyperclip.copy(self.last_response); self.ui.print_info("Copied last response to clipboard.")
    async def cmd_multiline(self, ctx, *args): self.multiline = not self.multiline; self.ui.print_info(f"Multiline Mode: {'ON' if self.multiline else 'OFF'}")
    async def cmd_model(self, ctx, *args):
        if args: self.config['agent']['model'] = args[0]; ctx['should_reinit'] = True
    async def cmd_plan(self, ctx, *args): self.current_mode_idx = 2; ctx['should_reinit'] = True
    async def cmd_agents(self, ctx, *args):
        if args: self.active_persona = args[0].lower(); self.re_initialize(); ctx['should_reinit'] = True
    async def cmd_autonomy(self, ctx, *args):
        if args: self.autonomy_level = args[0].lower(); self.ui.print_info(f"Autonomy Level: {self.autonomy_level.upper()}")
    async def cmd_versions(self, ctx, *args): self.ui.display_versions(self._versions)
    async def cmd_clear(self, ctx, *args): self.ui.console.clear()
    async def cmd_efficient(self, ctx, *args):
        self.efficient_mode = not self.efficient_mode
        self.ui.print_info(f"Efficient Mode (Sliding Window): {'ON' if self.efficient_mode else 'OFF'}")
    async def cmd_tools(self, ctx, *args): self.ui.display_tools(list(self.mcp_manager.tools.keys()))
    async def cmd_usage(self, ctx, *args):
        stats = self.telemetry.get_current_session_stats()
        self.ui.print_info(f"Current Session Tokens: {stats}")
    async def cmd_stats(self, ctx, *args):
        stats = self.telemetry.get_cumulative_stats()
        self.ui.print_info(f"Cumulative Token Usage: {stats}")
    async def cmd_goal(self, ctx, *args):
        if args: self.orchestrator.set_goal(" ".join(args)); self.ui.print_info(f"Mission Goal Set: {self.orchestrator.goal}")
    async def cmd_mission(self, ctx, *args): self.ui.render_markdown(self.orchestrator.render_mission_control())
    async def cmd_sandbox(self, ctx, *args):
        self.sandbox.toggle()
        self.ui.print_info(f"Native Sandbox: {'ENABLED' if self.sandbox.enabled else 'DISABLED'}")
    async def cmd_file(self, ctx, *args):
        if not args: return
        content = await self.read_file(args[0])
        if not content.startswith("Blocked:"):
            # [Strict DLP] 주입되는 파일 내용도 반드시 마스킹을 거쳐야 함
            masked_content = self.protector.mask(content)
            self.prompt += f"\n\n--- Reference File: {args[0]} ---\n{masked_content}"
            self.ui.print_info(f"File '{args[0]}' (Masked) injected into current knowledge base.")
    async def cmd_export(self, ctx, *args):
        path = args[0] if args else "export.md"
        with open(path, 'w') as f: f.write(self.last_response)
        self.ui.print_info(f"Exported last response to {path}")
    async def cmd_refresh(self, ctx, *args):
        self.re_initialize()
        self.ui.print_info("Instructions and configurations refreshed.")
    async def cmd_fork(self, ctx, *args):
        name = f"fork_{datetime.now().strftime('%H%M%S')}"
        await self.cmd_save(ctx, name)
        self.ui.print_info(f"Session forked to: {name}")
    async def cmd_peek(self, ctx, *args):
        if self.last_shell_output:
            self.ui.console.print(Panel(self.last_shell_output, title="Terminal Peek", border_style="cyan"))
        else:
            self.ui.print_warning("No recent shell output to peek.")
    async def cmd_preview(self, ctx, *args):
        self.ui.console.print(Panel(self.last_response, title="Artifact Preview", border_style="green"))
    async def cmd_schedule(self, ctx, *args):
        if len(args) < 3:
            self.ui.print_warning("Usage: /schedule <name> <delay_s> <command>")
            return
        name, delay, cmd = args[0], args[1], " ".join(args[2:])
        if not delay.isdigit(): return
        msg = self.scheduler.schedule_once(name, int(delay), cmd)
        self.ui.print_info(msg)

    async def cmd_compress(self, ctx, *args):
        compressor = ContextCompressor(self.backend)
        self.backend.history = await compressor.compress(self.backend.history)
        self.ui.print_info("Context compression completed.")

    async def cmd_skills(self, ctx, *args):
        sub = args[0] if args else "list"
        if sub == "list":
            skills = self.skill_manager.list_skills()
            self.ui.print_info(f"Available Skills: {skills}")
        elif sub == "load" and len(args) > 1:
            skill = self.skill_manager.load_skill(args[1])
            if skill:
                self.prompt = skill.get('instruction', self.prompt)
                self.ui.print_info(f"Skill '{args[1]}' loaded.")
                ctx['should_reinit'] = True
        elif sub == "save" and len(args) > 1:
            data = {"instruction": self.prompt}
            self.skill_manager.save_skill(args[1], data)
            self.ui.print_info(f"Current prompt saved as skill '{args[1]}'.")

    async def cmd_pin(self, ctx, *args):
        if not args or not args[0].isdigit(): return
        idx = int(args[0])
        if 0 <= idx < len(self.backend.history):
            self.backend.history[idx]['pinned'] = True
            self.ui.print_info(f"Turn {idx} pinned.")

    async def cmd_unpin(self, ctx, *args):
        if not args or not args[0].isdigit(): return
        idx = int(args[0])
        if 0 <= idx < len(self.backend.history):
            self.backend.history[idx]['pinned'] = False
            self.ui.print_info(f"Turn {idx} unpinned.")

    async def cmd_commit(self, ctx, *args):
        msg = " ".join(args) if args else "Agent incremental update"
        res = self.git.commit_changes(msg)
        self.ui.print_info(f"Git Commit: {res}")

    async def cmd_protect(self, ctx, *args):
        if len(args) < 2: return
        self.protector.add_pattern(args[0], args[1])
        self.ui.print_info(f"Protection pattern '{args[0]}' added.")

    async def cmd_unprotect(self, ctx, *args):
        if not args: return
        if self.protector.remove_pattern(args[0]):
            self.ui.print_info(f"Protection pattern '{args[0]}' removed.")

    async def cmd_group(self, ctx, *args):
        if len(args) < 2:
            self.ui.print_warning("Usage: /group <persona1,persona2,...> <topic>")
            return
        personas = args[0].split(',')
        topic = " ".join(args[1:])
        res = await self.group_chat.run_group_discussion(personas, topic)
        self.last_response = res

    async def cmd_mcp(self, ctx, *args):
        if len(args) < 2:
            self.ui.print_warning("Usage: /mcp connect <name> <command> [args...]")
            return
        sub = args[0]
        if sub == "connect":
            name = args[1]
            cmd = args[2]
            cmd_args = args[3:] if len(args) > 3 else []
            res = await self.mcp_manager.connect_external_stdio(name, cmd, cmd_args)
            self.ui.print_info(res)

    async def switch_mode(self, new_mode: str):
        if self.backend: await self.backend.close()
        self.cli_mode = new_mode
        if self.cli_mode == "agent":
            # Pass terminal approval handler to Antigravity SDK policy
            self.backend = AgentBackend(self.config, self.prompt, ask_user_handler=self.run_shell)
        else:
            self.backend = ChatBackend(self.config, self.prompt)
        await self.backend.initialize()
        self.ui.print_info(f"Switched to {self.cli_mode.upper()} backend.")

    def re_initialize(self):
        self.config = self.resolver.resolve_settings()
        self.personas = self.resolver.discover_personas()
        self.active_persona = list(self.personas.keys())[0] if self.active_persona not in self.personas else self.active_persona
        self.prompt = self.personas.get(self.active_persona)
        self._cached_cwd = os.getcwd().replace(os.path.expanduser('~'), '~')
        self._cached_sandbox = "sandboxed" if self.config.get('enableTerminalSandbox') else "no sandbox"
        self._versions = {}
        for lib in ['google-antigravity', 'google-genai', 'rich', 'prompt-toolkit', 'pyyaml', 'pyperclip', 'python-dotenv']:
            try: self._versions[lib] = metadata.version(lib)
            except: self._versions[lib] = "N/A"

    def is_path_ignored(self, path: str) -> bool:
        try:
            full_path = os.path.abspath(path)
            rel_path = os.path.relpath(full_path, os.getcwd())
            for pattern in self.config.get("exclude_paths", []):
                if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern):
                    return True
        except: pass
        return False

    async def read_file(self, path):
        if self.is_path_ignored(path): return "Blocked: Security Policy (Ignore Rule)."
        try:
            path = self.plugins.apply_hooks("pre_tool", path)
            with open(path, 'r', encoding='utf-8') as f: 
                content = f.read()
                return self.plugins.apply_hooks("post_tool", content)
        except Exception as e: return f"Error reading file: {e}"

    async def write_file(self, path, content):
        if self.modes[self.current_mode_idx] == 'plan': return "Blocked: Plan Mode (Read-only)."
        if self.is_path_ignored(path): return "Blocked: Security Policy (Ignore Rule)."
        
        content = self.plugins.apply_hooks("pre_tool", content)
        
        if self.modes[self.current_mode_idx] != 'auto-edit' and self.autonomy_level != 'always':
            old = ""
            if os.path.exists(path):
                with open(path, 'r') as f: old = f.read()
            self.diff_viewer.display_diff(old, content, path)
            with patch_stdout():
                confirm = await self.session.prompt_async(HTML(f"<b>Apply changes to {path}?</b> (y/N): "))
            if confirm.lower() != 'y': return "Changes cancelled by user."
            
        with open(path, 'w', encoding='utf-8') as f: f.write(content)
        return self.plugins.apply_hooks("post_tool", "File updated successfully.")

    async def run_shell(self, cmd):
        if self.modes[self.current_mode_idx] == 'plan': return "Blocked: Plan Mode (Read-only)."
        for p in self.config.get("exclude_paths", []):
            if p.replace('*','') in cmd: return f"Blocked: Security Policy (Restricted path '{p}' detected)."
            
        cmd = self.plugins.apply_hooks("pre_tool", cmd)

        if self.autonomy_level != 'always':
            with patch_stdout():
                confirm = await self.session.prompt_async(HTML(f"<b>Run shell command?</b> <style fg='red'>{cmd}</style> (y/N): "))
            if confirm.lower() != 'y': return "Execution cancelled by user."
            
        try:
            res = await self.sandbox.execute_sandboxed(cmd)
            self.last_shell_output = f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
            return self.plugins.apply_hooks("post_tool", self.last_shell_output)
        except Exception as e: return f"Shell Error: {e}"

    async def launch_rewind_ui(self):
        if not self.backend or not self.backend.history:
            self.ui.print_warning("No conversation history available for rewind."); return
        self.ui.console.print(Panel("REWIND INTERFACE (Select step to roll back to)", border_style="yellow"))
        for i, turn in enumerate(self.backend.history):
            role = turn.get('role', 'unknown')
            txt = turn.get('content', '')[:60].replace('\n', ' ')
            self.ui.console.print(f" [{i}] [bold]{role.upper()}[/bold]: {txt}...")
        with patch_stdout():
            idx = await self.session.prompt_async("Rewind to index (Enter to cancel): ")
        if idx.isdigit():
            self.backend.history = self.backend.history[:int(idx)+1]
            self.ui.print_info(f"Conversation history rewound to step {idx}.")

    async def chat_cycle(self, user_input):
        masked_input = self.protector.mask(user_input)
        try:
            self.ui.console.print(f"\n[{self.cli_mode}]🤖 {self.cli_mode.upper()}:[/{self.cli_mode}]")
            full_text = ""
            with self.ui.create_live_display() as live:
                response, usage = await self.backend.chat(masked_input)
                self.telemetry.update_usage(usage)
                
                if hasattr(response, 'thoughts'):
                    async for thought in response.thoughts:
                        live.update(self.ui.render_thought_panel(thought))
                
                # Robust response text extraction
                if hasattr(response, 'text'):
                    res_attr = response.text
                    if asyncio.iscoroutine(res_attr) or asyncio.iscoroutinefunction(res_attr):
                        content = await res_attr() if asyncio.iscoroutinefunction(res_attr) else await res_attr
                    elif callable(res_attr):
                        content = res_attr()
                    else:
                        content = res_attr
                else:
                    content = str(response)
                if "[ENTER_PLAN_MODE]" in content: self.current_mode_idx = 2
                
                # [Response Firewall] AI 응답 내용도 전송 직후 마스킹 검사 수행
                masked_content = self.protector.mask(content, is_response=True)
                full_text = masked_content
                
                live.update(Markdown(self.protector.unmask(full_text)))
                
            self.last_response = self.protector.unmask(full_text)
            
            # Auto-compression when history is long and efficient_mode is ON
            max_h = self.config.get('state', {}).get('max_history', 15)
            if self.efficient_mode and len(self.backend.history) > max_h:
                compressor = ContextCompressor(self.backend)
                self.backend.history = await compressor.compress(self.backend.history, keep_last=5)
                self.ui.print_info("[Auto-Compression] History optimized.")
            elif self.efficient_mode and len(self.backend.history) > 10:
                # Fallback to simple slicing if no compression
                pinned = [h for h in self.backend.history[:-10] if h.get('pinned')]
                self.backend.history = pinned + self.backend.history[-10:]
        except Exception as e: self.ui.print_error(f"Interaction Error: {e}")

    async def run(self):
        load_dotenv()
        while True:
            await self.switch_mode(self.cli_mode)
            ctx = {'should_reinit': False}
            while not ctx['should_reinit']:
                self.ui.render_header(self.modes[self.current_mode_idx], self.cli_mode)
                try:
                    with patch_stdout():
                        user_input = await self.session.prompt_async("> ", multiline=self.multiline)
                    self.ui.render_dashboard(self._cached_cwd, self._cached_sandbox, self.config['agent']['model'], self.telemetry.format_quota_display())
                    user_input = user_input.strip()
                    if not user_input: continue
                    if user_input.startswith('/'):
                        if await self.commands.handle(user_input, ctx): continue
                        instr = self.plugins.execute_plugin_command(user_input.split()[0].lower())
                        if instr: 
                            self.ui.print_info(f"Executing Plugin: {user_input}")
                            await self.chat_cycle(instr); continue
                    if user_input.startswith('!'): await self.run_shell(user_input[1:].strip()); continue
                    await self.chat_cycle(user_input)
                except KeyboardInterrupt: continue
                except EOFError: return
        self.protector.clear()

def main():
    asyncio.run(UnifiedSecureCLI().run())
if __name__ == "__main__": main()
