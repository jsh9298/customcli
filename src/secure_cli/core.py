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
from prompt_toolkit.filters import Condition
from prompt_toolkit.application import get_app
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import run_in_terminal

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
    def __init__(self, cli):
        self.cli = cli

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        
        # 1. Slash Command & Argument Completion
        if text.startswith('/'):
            parts = text.split()
            if len(parts) <= 1 and not text.endswith(' '):
                # Completing the command itself
                cmds = self.cli.commands.get_commands()
                plugin_cmds = self.cli.plugins.get_plugin_commands()
                all_cmds = sorted(set(cmds + plugin_cmds))
                
                # Calculate padding for alignment (similar to screenshot 2)
                max_len = max([len(c) for c in all_cmds]) + 4 if all_cmds else 20
                
                for cmd in all_cmds:
                    if cmd.lower().startswith(text.lower()):
                        desc = self.cli.commands.get_description(cmd) if cmd in cmds else "플러그인 명령어"
                        # Use display for aligned columns in the menu
                        yield Completion(
                            cmd, 
                            display=f"{cmd:<{max_len}}", 
                            display_meta=desc, 
                            start_position=-len(text)
                        )
                return

            # Context-Aware Argument Completion
            cmd = parts[0].lower()
            arg_prefix = parts[-1] if not text.endswith(' ') else ""
            
            suggestions = []
            if cmd == '/config':
                if len(parts) == 2 and not text.endswith(' '):
                    suggestions = [
                        ("show", "현재 설정 보기"),
                        ("model", "AI 모델 변경"),
                        ("agent", "페르소나 변경"),
                        ("mode", "실행 모드 변경"),
                        ("autonomy", "자율성 레벨 설정"),
                        ("efficient", "압축 모드 토글"),
                        ("sandbox", "샌드박스 토글"),
                        ("refresh", "설정 새로고침")
                    ]
                elif len(parts) >= 2:
                    sub = parts[1].lower()
                    if sub == "model": suggestions = [(m, "모델 선택") for m in self.cli.available_models]
                    elif sub == "agent": suggestions = [(p, "페르소나 선택") for p in self.cli.personas.keys()]
                    elif sub == "mode": suggestions = [("agent", "에이전트 모드"), ("chat", "대화 모드")]
                    elif sub == "autonomy": suggestions = [("always", "항상 승인"), ("review", "매번 검토")]
                
            elif cmd == '/session':
                if len(parts) == 2 and not text.endswith(' '):
                    suggestions = [
                        ("save", "현재 세션 저장"),
                        ("load", "세션 불러오기"),
                        ("list", "저장된 세션 목록"),
                        ("resume", "최근 세션 재개"),
                        ("fork", "세션 복제")
                    ]
                elif len(parts) >= 2 and parts[1].lower() in ["load", "save"]:
                    suggestions = [(s, "세션 파일") for s in self.cli.session_manager.list_sessions()]

            elif cmd == '/history':
                if len(parts) == 2 and not text.endswith(' '):
                    suggestions = [
                        ("show", "대화 기록 출력"),
                        ("undo", "마지막 대화 취소"),
                        ("rewind", "특정 시점으로 롤백"),
                        ("compress", "대화 기록 압축"),
                        ("pin", "메시지 고정"),
                        ("unpin", "메시지 고정 해제")
                    ]

            elif cmd == '/usage':
                suggestions = [("session", "현재 세션 사용량"), ("total", "누적 사용량")]

            elif cmd == '/utility':
                suggestions = [
                    ("file", "파일 읽기/주입"),
                    ("export", "응답 내보내기"),
                    ("peek", "최근 셸 출력 보기"),
                    ("preview", "아티팩트 미리보기"),
                    ("copy", "응답 복사"),
                    ("clear", "화면 지우기")
                ]
            
            elif cmd == '/protect':
                suggestions = [("add", "보안 패턴 추가"), ("remove", "보안 패턴 제거")]
            
            elif cmd == '/goal':
                suggestions = [("set", "목표 설정"), ("status", "진행 상황 확인")]

            elif cmd == '/skills':
                if len(parts) == 2 and not text.endswith(' '):
                    suggestions = [("list", "스킬 목록"), ("load", "스킬 로드"), ("save", "현재 프롬프트를 스킬로 저장")]
                else:
                    suggestions = [(s, "스킬 이름") for s in self.cli.skill_manager.list_skills()]
            
            if suggestions:
                valid_suggestions = [s for s in suggestions if (s[0] if isinstance(s, tuple) else s).lower().startswith(arg_prefix.lower())]
                max_arg_len = max([len(s[0] if isinstance(s, tuple) else s) for s in valid_suggestions]) + 4 if valid_suggestions else 20
                
                for s in suggestions:
                    label, meta = s if isinstance(s, tuple) else (s, "")
                    if label.lower().startswith(arg_prefix.lower()):
                        yield Completion(
                            label, 
                            display=f"{label:<{max_arg_len}}", 
                            display_meta=meta, 
                            start_position=-len(arg_prefix)
                        )

        # 2. File Reference Completion (@path)
        elif '@' in text:
            match = re.search(r'@([^\s]*)$', text)
            if match:
                path_prefix = match.group(1)
                for c in self._get_file_completions(path_prefix):
                    yield c

    def _get_file_completions(self, path_prefix):
        dirname = os.path.dirname(path_prefix) or "."
        basename = os.path.basename(path_prefix)
        try:
            if os.path.isdir(dirname):
                files = os.listdir(dirname)
                valid_files = [f for f in files if f.startswith(basename)]
                max_f_len = max([len(f) for f in valid_files]) + 4 if valid_files else 20
                
                for f in valid_files:
                    full_f = os.path.join(dirname, f)
                    is_dir = os.path.isdir(full_f)
                    display_f = f + "/" if is_dir else f
                    meta = "Directory" if is_dir else f"{os.path.getsize(full_f):,} bytes"
                    yield Completion(
                        display_f, 
                        display=f"{display_f:<{max_f_len}}", 
                        display_meta=meta, 
                        start_position=-len(basename)
                    )
        except: pass

class ConfigResolver:
    GLOBAL_ROOT = os.path.expanduser('~/.gemini/antigravity-cli')
    PROJECT_ROOT = os.path.abspath('.antigravity')
    def __init__(self):
        for p in [self.GLOBAL_ROOT, os.path.join(self.GLOBAL_ROOT, 'skills'), self.PROJECT_ROOT]:
            os.makedirs(p, exist_ok=True)
    def resolve_settings(self):
        base = {"agent": {"model": "gemini-3.5-flash", "temperature": 0.7}, "enableTerminalSandbox": False, "exclude_paths": [".env", ".git", ".sessions", "*.log"]}
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
        
        # [Usage Clarity] Initialize Telemetry with model-specific limits
        agent_cfg = self.config.get('agent', {})
        self.telemetry = TelemetryManager(
            hard_limit=state_cfg.get('hard_limit', 0),
            model_limit=agent_cfg.get('max_output_tokens', 4096)
        )
        
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
        self._current_task: Optional[asyncio.Task] = None
        self.available_models: List[str] = ["gemini-3.5-flash", "gemini-3.5-pro", "antigravity-preview-05-2026"]
        
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
            
        @self.kb.add('escape')
        def _(e):
            if self._current_task and not self._current_task.done():
                self._current_task.cancel()
                self.ui.print_warning("\n[Abort] 사용자 요청에 의해 작업이 중단되었습니다 (ESC).")
            else:
                # [Rewind Shortcut] ESC-ESC pattern or just ESC when idle
                # To maintain old ESC-ESC behavior, we could check timing, but let's keep it simple.
                pass

        @self.kb.add('escape', 'escape')
        def _(e):
            if not (self._current_task and not self._current_task.done()):
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
            # Only trigger help if the buffer is empty to avoid interfering with normal typing
            if not e.app.current_buffer.text:
                asyncio.create_task(self.cmd_help({}, None))
            else:
                # If buffer is not empty, insert the '?' character normally
                e.app.current_buffer.insert_text('?')

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

        # Custom TUI Style (matching screenshot 2)
        self.tui_style = Style.from_dict({
            'completion-menu.completion': 'bg:#333333 #ffffff',
            'completion-menu.completion.current': 'bg:#445544 #ffffff', # Greenish dark highlight
            'completion-menu.meta.completion': 'bg:#333333 #888888',
            'completion-menu.meta.completion.current': 'bg:#445544 #aaaaaa',
            'scrollbar.background': 'bg:#222222',
            'scrollbar.button': 'bg:#444444',
            'rprompt': 'bg:#222222 #888888',
            'bottom-toolbar': 'bg:#111111 #ffffff',
            'bottom-toolbar.text': '#ffffff',
        })

        self.session = PromptSession(
            history=FileHistory(os.path.expanduser('~/.unified_secure_history')),
            completer=SmartCompleter(self),
            key_bindings=self.kb,
            style=self.tui_style
        )
        self.inline_session = PromptSession(style=self.tui_style)

    def register_core_commands(self):
        self.commands.register('/help', self.cmd_help, "도움말 출력")
        self.commands.register('/session', self.cmd_session_unified, "세션 관리 (save, load, list, resume, fork)")
        self.commands.register('/history', self.cmd_history_unified, "대화 기록 관리 (show, undo, rewind, compress, pin, unpin)")
        self.commands.register('/config', self.cmd_config_unified, "설정 관리 (show, model, agent, mode, autonomy, efficient, sandbox, refresh)")
        self.commands.register('/usage', self.cmd_usage_unified, "토큰 사용량 확인 (session, total)")
        self.commands.register('/utility', self.cmd_utility_unified, "유틸리티 기능 (file, export, peek, preview, copy, clear)")
        self.commands.register('/goal', self.cmd_goal_unified, "목표 및 태스크 관리 (set, status)")
        self.commands.register('/protect', self.cmd_protect_unified, "보안 패턴 관리 (add, remove)")
        self.commands.register('/skills', self.cmd_skills, "에이전트 스킬 관리")
        self.commands.register('/commit', self.cmd_commit, "변경 사항 Git 커밋")
        self.commands.register('/schedule', self.cmd_schedule, "작업 스케줄링")
        self.commands.register('/group', self.cmd_group, "그룹 대화 시작")
        self.commands.register('/mcp', self.cmd_mcp, "MCP 서버 연결")
        self.commands.register('/inline', self.cmd_inline, "원샷 인라인 명령 실행")
        self.commands.register('/exit', self.cmd_exit, "프로그램 종료")

    # --- Consolidated Command Handlers ---
    async def cmd_session_unified(self, ctx, *args):
        sub = args[0].lower() if args else "list"
        if sub == "save": await self.cmd_save(ctx, *args[1:])
        elif sub == "load": await self.cmd_load(ctx, *args[1:])
        elif sub == "list": await self.cmd_sessions(ctx)
        elif sub == "resume": await self.cmd_resume(ctx)
        elif sub == "fork": await self.cmd_fork(ctx)

    async def cmd_history_unified(self, ctx, *args):
        sub = args[0].lower() if args else "show"
        if sub == "show": await self.cmd_history(ctx)
        elif sub == "undo": await self.cmd_undo(ctx)
        elif sub == "rewind": await self.cmd_rewind(ctx)
        elif sub == "compress": await self.cmd_compress(ctx)
        elif sub == "pin": await self.cmd_pin(ctx, *args[1:])
        elif sub == "unpin": await self.cmd_unpin(ctx, *args[1:])

    async def cmd_config_unified(self, ctx, *args):
        sub = args[0].lower() if args else "show"
        if sub == "show": await self.cmd_config(ctx)
        elif sub == "model": await self.cmd_model(ctx, *args[1:])
        elif sub == "agent": await self.cmd_agents(ctx, *args[1:])
        elif sub == "mode": await self.cmd_mode(ctx, *args[1:])
        elif sub == "autonomy": await self.cmd_autonomy(ctx, *args[1:])
        elif sub == "efficient": await self.cmd_efficient(ctx)
        elif sub == "sandbox": await self.cmd_sandbox(ctx)
        elif sub == "refresh": await self.cmd_refresh(ctx)

    async def cmd_usage_unified(self, ctx, *args):
        sub = args[0].lower() if args else "session"
        if sub == "session": await self.cmd_usage(ctx)
        elif sub == "total": await self.cmd_stats(ctx)

    async def cmd_utility_unified(self, ctx, *args):
        sub = args[0].lower() if args else "help"
        if sub == "file": await self.cmd_file(ctx, *args[1:])
        elif sub == "export": await self.cmd_export(ctx, *args[1:])
        elif sub == "peek": await self.cmd_peek(ctx)
        elif sub == "preview": await self.cmd_preview(ctx)
        elif sub == "copy": await self.cmd_copy(ctx)
        elif sub == "clear": await self.cmd_clear(ctx)

    async def cmd_goal_unified(self, ctx, *args):
        sub = args[0].lower() if args else "status"
        if sub == "set": await self.cmd_goal(ctx, *args[1:])
        elif sub == "status": await self.cmd_mission(ctx)

    async def cmd_protect_unified(self, ctx, *args):
        sub = args[0].lower() if args else "list"
        if sub == "add": await self.cmd_protect(ctx, *args[1:])
        elif sub == "remove": await self.cmd_unprotect(ctx, *args[1:])

    # --- Command Handlers ---
    async def cmd_help(self, ctx, *args):
        t = Table(title="Unified Workstation Commands")
        t.add_column("Command"); t.add_column("Description", style="dim"); t.add_column("Source")
        for cmd in self.commands.get_commands():
            desc = self.commands.get_description(cmd)
            t.add_row(cmd, desc, "Core")
        for cmd in self.plugins.get_plugin_commands(): t.add_row(cmd, "플러그인 명령어", "Plugin")
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
    async def cmd_copy(self, ctx, *args):
        try:
            pyperclip.copy(self.last_response)
            self.ui.print_info("Copied last response to clipboard.")
        except Exception as e:
            self.ui.print_warning(f"Clipboard copy failed (Expected in Docker/Headless): {e}")
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
        stats = self.telemetry.get_detailed_stats()
        self.ui.print_info(f"Current Session Tokens: {stats['session']:,}")
    async def cmd_stats(self, ctx, *args):
        stats = self.telemetry.get_detailed_stats()
        quota_str = f" / {stats['hard_limit']:,}" if stats['hard_limit'] > 0 else " / ∞"
        self.ui.print_info(f"Daily Total Usage: {stats['daily']:,}{quota_str}")
        self.ui.print_info(f"Model Token Limit: {stats['model_limit']:,}")
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

    async def cmd_inline(self, ctx, *args):
        """Execute a one-shot command without breaking conversation flow (Ctrl+I)."""
        async def _get_input():
            return await self.inline_session.prompt_async("Inline Command: ")
            
        # [Critical Fix] Use run_in_terminal to avoid "Application is already running" crash
        # when triggered from a keybinding while the main app is active.
        cmd = await run_in_terminal(_get_input)
        
        if cmd and cmd.strip():
            cmd = cmd.strip()
            if cmd.startswith('!'): await self.run_shell(cmd[1:].strip())
            elif cmd.startswith('/'): await self.commands.handle(cmd, ctx)
            else: await self.chat_cycle(cmd)

    async def cmd_models(self, ctx, *args):
        """List available models from the Gemini API (if applicable)."""
        if self.cli_mode == "chat" and hasattr(self.backend, 'provider') and self.backend.provider == "google":
            try:
                models = self.backend.client.models.list()
                t = Table(title="Available Google Models")
                t.add_column("Model ID"); t.add_column("Capabilities")
                # Populate dynamic models for autocompletion
                self.available_models = []
                for m in models:
                    self.available_models.append(m.name)
                    t.add_row(m.name, ", ".join(m.supported_generation_methods))
                self.ui.console.print(t)
            except Exception as e:
                self.ui.print_error(f"Failed to fetch models: {e}")
        else:
            self.ui.print_info("Dynamic model listing currently only supported for Google Chat backend.")

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
        
        # [Smart Autocomplete] Background fetch available models
        if self.cli_mode == "chat" and hasattr(self.backend, 'provider') and self.backend.provider == "google":
            asyncio.create_task(self._fetch_models_silent())

    async def _fetch_models_silent(self):
        """Silently update available_models for autocompletion."""
        try:
            # We use a synchronous generator from the SDK, so we run it in a thread or just call it
            # if it's not blocking for too long.
            models = self.backend.client.models.list()
            self.available_models = [m.name for m in models]
        except: pass

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
        # [Feature] Automatic @file reference parsing
        # find @path/to/file in input and inject content
        file_refs = re.findall(r'@([^\s]+)', user_input)
        injected_content = ""
        for path in file_refs:
            content = await self.read_file(path)
            if not content.startswith("Error") and not content.startswith("Blocked"):
                masked_file_content = self.protector.mask(content)
                injected_content += f"\n\n--- Reference File: {path} ---\n{masked_file_content}\n"
        
        full_input = user_input + injected_content
        masked_input = self.protector.mask(full_input)
        
        try:
            self.ui.console.print(f"\n[{self.cli_mode}]🤖 {self.cli_mode.upper()}:[/{self.cli_mode}]")
            full_text = ""
            with self.ui.create_live_display() as live:
                response, usage = await self.backend.chat(masked_input)
                self.telemetry.update_usage(usage)
                
                if hasattr(response, 'thoughts'):
                    async for thought in response.thoughts:
                        # Check for cancellation within async iterations
                        if asyncio.current_task().cancelled(): raise asyncio.CancelledError()
                        live.update(self.ui.render_thought_panel(thought))
                
                # Robust response text extraction
                content = ""
                if hasattr(response, 'text'):
                    res_attr = response.text
                    if asyncio.iscoroutine(res_attr) or asyncio.iscoroutinefunction(res_attr):
                        content = await res_attr() if asyncio.iscoroutinefunction(res_attr) else await res_attr
                    elif callable(res_attr):
                        content = res_attr()
                    else:
                        content = res_attr
                elif hasattr(response, 'candidates') and len(response.candidates) > 0:
                    # Fallback for raw candidates (GenAI SDK style)
                    content = response.candidates[0].content.parts[0].text
                else:
                    content = str(response)
                
                if asyncio.current_task().cancelled(): raise asyncio.CancelledError()
                if "[ENTER_PLAN_MODE]" in content: self.current_mode_idx = 2
                
                # [Response Firewall] AI 응답 내용도 전송 직후 마스킹 검사 수행
                masked_content = self.protector.mask(content, is_response=True)
                full_text = masked_content
                
                live.update(Markdown(self.protector.unmask(full_text)))
                
            self.last_response = self.protector.unmask(full_text)
            
            # Update unified history interface
            self.backend.history.append({"role": "user", "content": user_input})
            self.backend.history.append({"role": "assistant", "content": self.last_response})

            # Auto-compression logic
            max_h = self.config.get('state', {}).get('max_history', 15)
            if self.efficient_mode and len(self.backend.history) > max_h:
                compressor = ContextCompressor(self.backend)
                self.backend.history = await compressor.compress(self.backend.history, keep_last=5)
                self.ui.print_info("[Auto-Compression] History optimized.")
        except asyncio.CancelledError:
            # Task was aborted via ESC
            self.ui.print_warning("\n[System] 작업이 사용자에 의해 중단되었습니다.")
        except Exception as e: self.ui.print_error(f"Interaction Error: {e}")
        finally:
            self._current_task = None

    def _get_ui_stats(self):
        """Returns the count of GEMINI.md files and loaded skills for the UI."""
        gemini_files = set()
        for p in [self.resolver.GLOBAL_ROOT, self.resolver.PROJECT_ROOT, '.']:
            for f in ['GEMINI.md', 'GEMINI.MD', 'gemini.md']:
                path = os.path.join(p, f)
                if os.path.exists(path):
                    gemini_files.add(os.path.abspath(path))
        return len(gemini_files), len(self.skill_manager.list_skills())

    async def run(self):
        load_dotenv()
        while True:
            await self.switch_mode(self.cli_mode)
            ctx = {'should_reinit': False}
            while not ctx['should_reinit']:
                try:
                    # [UI Update] Render status line before prompt
                    g_files, s_count = self._get_ui_stats()
                    self.ui.render_status_line(
                        self.autonomy_level, 
                        self.modes[self.current_mode_idx],
                        g_files,
                        s_count
                    )
                    
                    # Dashboard toolbar function for prompt-toolkit
                    def get_toolbar():
                        return self.ui.get_dashboard_toolbar(
                            self._cached_cwd,
                            self._cached_sandbox,
                            self.config['agent']['model'],
                            self.telemetry.format_quota_display(),
                            self.cli_mode,
                            self.modes[self.current_mode_idx]
                        )

                    with patch_stdout():
                        user_input = await self.session.prompt_async(
                            "> ", 
                            placeholder="Type your message or @path/to/file",
                            bottom_toolbar=get_toolbar,
                            rprompt=HTML('<style fg="ansigray">? for shortcuts</style>'),
                            multiline=self.multiline,
                            complete_while_typing=True
                        )
                    
                    user_input = user_input.strip()
                    if not user_input: continue
                    
                    # Track current task for ESC-abort
                    if user_input.startswith('/'):
                        if await self.commands.handle(user_input, ctx): continue
                        instr = self.plugins.execute_plugin_command(user_input.split()[0].lower())
                        if instr: 
                            self.ui.print_info(f"Executing Plugin: {user_input}")
                            self._current_task = asyncio.create_task(self.chat_cycle(instr))
                            await self._current_task
                            continue
                    elif user_input.startswith('!'):
                        await self.run_shell(user_input[1:].strip())
                        continue
                    else:
                        self._current_task = asyncio.create_task(self.chat_cycle(user_input))
                        await self._current_task
                except KeyboardInterrupt: continue
                except EOFError: return
        self.protector.clear()

def main():
    asyncio.run(UnifiedSecureCLI().run())
if __name__ == "__main__": main()
