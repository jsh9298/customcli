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
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition, HasFocus, IsReadOnly
from prompt_toolkit.application import get_app, run_in_terminal
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.styles import Style
from prompt_toolkit.enums import DEFAULT_BUFFER

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
from secure_cli.utils.logger import PayloadLogger

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
                mode_tag = self.cli.cli_mode
                cmds = self.cli.commands.get_commands(filter_tag=mode_tag)
                plugin_cmds = self.cli.plugins.get_plugin_commands()
                all_cmds = sorted(set(cmds + plugin_cmds))
                
                max_len = max([len(c) for c in all_cmds]) + 4 if all_cmds else 20
                
                for cmd in all_cmds:
                    if cmd.lower().startswith(text.lower()):
                        desc = self.cli.commands.get_description(cmd) if cmd in cmds else "플러그인 명령어"
                        yield Completion(
                            cmd, 
                            display=f"{cmd:<{max_len}}", 
                            display_meta=desc, 
                            start_position=-len(text)
                        )
                return

            cmd = parts[0].lower()
            arg_prefix = parts[-1] if not text.endswith(' ') else ""
            
            suggestions = []
            canonical = self.cli.commands._aliases.get(cmd, cmd)
            
            if canonical in ['/config', '/settings']:
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
                    elif sub == "mode": suggestions = [("agents", "에이전트 모드"), ("chat", "대화 모드")]
                    elif sub == "autonomy": suggestions = [("always", "항상 승인"), ("review", "매번 검토")]
                
            elif canonical in ['/chat', '/session', '/switch']:
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

            elif canonical in ['/history', '/rewind']:
                if len(parts) == 2 and not text.endswith(' '):
                    suggestions = [
                        ("show", "대화 기록 출력"),
                        ("undo", "마지막 대화 취소"),
                        ("rewind", "특정 시점으로 롤백"),
                        ("compress", "대화 기록 압축"),
                        ("pin", "메시지 고정"),
                        ("unpin", "메시지 고정 해제")
                    ]

            elif canonical in ['/usage', '/stats']:
                suggestions = [("session", "현재 세션 사용량"), ("total", "누적 사용량")]

            elif canonical == '/utility':
                suggestions = [
                    ("file", "파일 읽기/주입"),
                    ("export", "응답 내보내기"),
                    ("peek", "최근 셸 출력 보기"),
                    ("preview", "아티팩트 미리보기"),
                    ("copy", "응답 복사"),
                    ("clear", "화면 지우기")
                ]
            
            elif canonical == '/protect':
                suggestions = [("add", "보안 패턴 추가"), ("remove", "보안 패턴 제거")]
            
            elif canonical == '/goal':
                suggestions = [("set", "목표 설정"), ("status", "진행 상황 확인")]

            elif canonical == '/skills':
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
                return

        # 2. File Reference Completion (@path)
        if '@' in text:
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
    def __init__(self, initial_mode: str = "agents"):
        self.protector = SecurityProtector()
        self.resolver = ConfigResolver()
        self.config = self.resolver.resolve_settings()
        
        state_cfg = self.config.get('state', {})
        self.session_manager = SessionManager(expiry_days=state_cfg.get('expiry_days', 7))
        self.mcp_manager = MCPManager(self.protector)
        self.ui = UIController()
        self.payload_logger = PayloadLogger()
        
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
        
        # --- Mode-Aware KeyBindings ---
        self.kb = KeyBindings()
        
        is_chat = Condition(lambda: self.cli_mode == 'chat')
        is_agents = Condition(lambda: self.cli_mode == 'agents')

        # 1. Global / Shared Shortcuts
        @self.kb.add('s-tab')
        def _(e):
            """Work Mode Cycle (Default -> Auto-Edit -> Plan)"""
            self.current_mode_idx = (self.current_mode_idx + 1) % len(self.modes)
            self.ui.print_info(f"Work Mode: {self.modes[self.current_mode_idx].upper()}")
            
        @self.kb.add('tab', 'tab')
        def _(e):
            """UI Detail Toggle"""
            self.ui.detail_mode = "minimal" if self.ui.detail_mode == "full" else "full"
            self.ui.print_info(f"UI Detail: {self.ui.detail_mode.upper()}")
            
        @self.kb.add('escape')
        def _(e):
            """Abort current task / stream"""
            if self._current_task and not self._current_task.done():
                self._current_task.cancel()
                self.ui.print_warning("\n[Abort] 작업이 사용자 요청에 의해 중단되었습니다.")
            else:
                pass

        @self.kb.add('c-l')
        def _(e):
            """Clear Screen / Redraw"""
            self.ui.console.clear()
            self.ui.print_info("Screen redraw completed.")

        @self.kb.add('c-o')
        def _(e):
            """Debug Console Toggle"""
            self.debug_log_enabled = not self.debug_log_enabled
            self.ui.print_info(f"Debug Log: {'ON' if self.debug_log_enabled else 'OFF'}")

        @self.kb.add('c-i')
        def _(e):
            """Inline One-shot Command (Ctrl+I)"""
            asyncio.create_task(self.cmd_inline({}, None))

        @self.kb.add('?')
        def _(e):
            """Interactive Help Prefix"""
            if not e.app.current_buffer.text:
                asyncio.create_task(self.cmd_help({}, None))
            else:
                e.app.current_buffer.insert_text('?')

        @self.kb.add('c-g')
        def _(e):
            """Open External Editor"""
            asyncio.create_task(self.cmd_open_stub({}, None))

        # 2. Agents Mode (Antigravity) Specifics
        @self.kb.add('escape', 'escape', filter=is_agents)
        def _(e):
            """AG: Buffer Reset"""
            e.app.current_buffer.text = ""
            self.ui.print_info("Input buffer cleared (esc esc).")

        @self.kb.add('c-y', filter=is_agents)
        def _(e):
            """AG: Yank (Copy buffer)"""
            txt = e.app.current_buffer.text
            if txt:
                try: pyperclip.copy(txt); self.ui.print_info("Yanked to clipboard.")
                except: self.ui.print_warning("Yank failed.")

        @self.kb.add('c-j', filter=is_agents)
        def _(e):
            """AG: Mission Control Focus"""
            asyncio.create_task(self.cmd_mission({}, None))

        @self.kb.add('c-k', filter=is_agents)
        def _(e):
            """AG: Fast Approval"""
            self._immediate_approval = True
            self.ui.print_info("Subagent approval flag SET.")

        # 3. Chat Mode (Gemini) Specifics
        @self.kb.add('escape', 'escape', filter=is_chat)
        def _(e):
            """Gemini: Legacy Rewind Mapping"""
            asyncio.create_task(self.launch_rewind_ui())

        @self.kb.add('c-y', filter=is_chat)
        def _(e):
            """Gemini: YOLO Toggle"""
            self.autonomy_level = "always" if self.autonomy_level != "always" else "review"
            self.ui.print_info(f"YOLO Mode: {'ACTIVE' if self.autonomy_level == 'always' else 'OFF'}")

        @self.kb.add('\\', 'enter', filter=is_chat)
        def _(e):
            """Gemini: Backslash + Enter Multiline"""
            e.app.current_buffer.insert_text('\n')
            self.ui.print_info("Multiline continuation (\\+Enter).")

        # Custom TUI Style
        self.tui_style = Style.from_dict({
            'completion-menu.completion': 'bg:#333333 #ffffff',
            'completion-menu.completion.current': 'bg:#445544 #ffffff',
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
            style=self.tui_style,
            complete_while_typing=True
        )
        self.inline_session = PromptSession(style=self.tui_style)

    def register_core_commands(self):
        # Shared
        self.commands.register('/help', self.cmd_help, "도움말 출력", tags=['chat', 'agents'])
        self.commands.alias('/?', '/help')
        self.commands.register('/model', self.cmd_model, "추론 모델 변경", tags=['chat', 'agents'])
        self.commands.register('/permissions', self.cmd_autonomy, "권한/자율성 설정", tags=['chat', 'agents'])
        self.commands.register('/skills', self.cmd_skills, "에이전트 스킬 관리", tags=['chat', 'agents'])
        self.commands.register('/mcp', self.cmd_mcp, "MCP 서버 관리", tags=['chat', 'agents'])
        self.commands.register('/clear', self.cmd_clear, "화면 및 세션 초기화", tags=['chat', 'agents'])
        self.commands.register('/exit', self.cmd_exit, "종료", tags=['chat', 'agents'])
        self.commands.alias('/quit', '/exit')
        self.commands.register('/agents', self.cmd_agents, "페르소나 관리", tags=['chat', 'agents'])

        # Chat (Gemini)
        self.commands.register('/chat', self.cmd_session_unified, "세션 관리", tags=['chat'])
        self.commands.alias('/resume', '/chat')
        self.commands.register('/compress', self.cmd_compress, "컨텍스트 압축", tags=['chat'])
        self.commands.register('/copy', self.cmd_copy, "마지막 응답 복사", tags=['chat'])
        self.commands.register('/directory', self.cmd_directory_stub, "디렉토리 관리", tags=['chat'])
        self.commands.alias('/dir', '/directory')
        self.commands.register('/rewind', self.cmd_rewind, "이전 상태 복구", tags=['chat', 'agents'])
        self.commands.alias('/undo', '/rewind')
        self.commands.register('/settings', self.cmd_config_unified, "설정", tags=['chat'])
        self.commands.register('/plan', self.cmd_plan, "플랜 모드", tags=['chat'])
        self.commands.register('/stats', self.cmd_usage_unified, "통계", tags=['chat'])
        self.commands.register('/about', self.cmd_versions, "버전 정보", tags=['chat'])
        self.commands.register('/auth', self.cmd_auth_stub, "계정 전환", tags=['chat'])
        self.commands.register('/bug', self.cmd_bug_stub, "버그 리포트", tags=['chat'])
        self.commands.register('/docs', self.cmd_docs_stub, "문서 사이트", tags=['chat'])

        # Agents (Antigravity)
        self.commands.register('/switch', self.cmd_session_unified, "세션 전환", tags=['agents'])
        self.commands.register('/config', self.cmd_config_unified, "시스템 구성", tags=['agents'])
        self.commands.register('/goal', self.cmd_goal_unified, "목표 설정", tags=['agents'])
        self.commands.register('/schedule', self.cmd_schedule, "스케줄링", tags=['agents'])
        self.commands.register('/usage', self.cmd_usage_unified, "리소스 사용량", tags=['agents'])
        self.commands.register('/fork', self.cmd_fork, "세션 복제", tags=['agents'])
        self.commands.register('/tasks', self.cmd_mission, "태스크 감시", tags=['agents'])
        self.commands.register('/open', self.cmd_open_stub, "파일 열기", tags=['agents'])
        self.commands.register('/browser', self.cmd_browser_stub, "브라우저 도구", tags=['agents'])
        self.commands.register('/grill-me', self.cmd_grill_stub, "상세 역질문 모드", tags=['agents'])
        self.commands.register('/rename', self.cmd_rename_stub, "세션명 변경", tags=['agents'])
        self.commands.register('/version', self.cmd_versions, "바이너리 버전", tags=['agents'])
        self.commands.register('/logout', self.cmd_exit, "로그아웃", tags=['agents'])

        # System Utility
        self.commands.register('/utility', self.cmd_utility_unified, "유틸리티", tags=['chat', 'agents'])
        self.commands.register('/protect', self.cmd_protect_unified, "보안 관리", tags=['chat', 'agents'])
        self.commands.register('/inline', self.cmd_inline, "인라인 실행", tags=['chat', 'agents'])
        self.commands.register('/commit', self.cmd_commit, "Git 커밋", tags=['chat', 'agents'])
        self.commands.register('/group', self.cmd_group, "그룹 대화", tags=['chat', 'agents'])

    # --- Stubs & Helpers ---
    async def cmd_directory_stub(self, ctx, *args):
        self.ui.print_info(f"Project: {self.resolver.PROJECT_ROOT}\nGlobal: {self.resolver.GLOBAL_ROOT}")
    async def cmd_open_stub(self, ctx, *args):
        if not args: return
        try:
            if sys.platform == 'darwin': subprocess.run(['open', args[0]])
            elif sys.platform == 'win32': os.startfile(args[0])
            else: subprocess.run(['xdg-open', args[0]])
            self.ui.print_info(f"Opened {args[0]}")
        except: self.ui.print_error(f"Failed to open {args[0]}")
    async def cmd_browser_stub(self, ctx, *args): self.ui.print_info("[Browser Mode] Active.")
    async def cmd_grill_stub(self, ctx, *args): self.ui.print_info("[Grill-me] Active."); self.autonomy_level = "review"
    async def cmd_auth_stub(self, ctx, *args): self.ui.print_info("Checking Cloud Auth...")
    async def cmd_bug_stub(self, ctx, *args): self.ui.print_info("GitHub: https://github.com/google-gemini/gemini-cli/issues")
    async def cmd_docs_stub(self, ctx, *args): self.ui.print_info("Docs: https://antigravity.google/docs")
    async def cmd_rename_stub(self, ctx, *args):
        if args: self.ui.print_info(f"Session renamed to '{args[0]}'")

    # --- Unified Handlers ---
    async def cmd_session_unified(self, ctx, *args):
        sub = args[0].lower() if args else "list"
        if sub == "save": await self.cmd_save(ctx, *args[1:])
        elif sub == "load": await self.cmd_load(ctx, *args[1:])
        elif sub == "list": await self.cmd_sessions(ctx)
        elif sub in ["resume", "switch"]: await self.cmd_resume(ctx)
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

    # --- Core Command Implementations ---
    async def cmd_help(self, ctx, *args):
        title = "Gemini CLI (Chat) Commands" if self.cli_mode == 'chat' else "Antigravity CLI (Agents) Commands"
        t = Table(title=title)
        t.add_column("Command"); t.add_column("Description", style="dim"); t.add_column("Type")
        for cmd in self.commands.get_commands(filter_tag=self.cli_mode):
            desc = self.commands.get_description(cmd)
            t.add_row(cmd, desc, "Alias" if cmd in self.commands._aliases else "Core")
        self.ui.console.print(t)
        self.ui.print_info(f"Tip: /config mode {'agents' if self.cli_mode == 'chat' else 'chat'} to switch.")
    async def cmd_mode(self, ctx, *args):
        if args: 
            m = args[0].lower()
            if m in ["agent", "agents"]: self.cli_mode = "agents"
            elif m in ["chat", "gemini"]: self.cli_mode = "chat"
            ctx['should_reinit'] = True
    async def cmd_reset(self, ctx, *args):
        if self.backend: self.backend.history.clear()
        self.protector.clear(); self.ui.print_info("Reset.")
    async def cmd_history(self, ctx, *args):
        if not self.backend: return
        for i, turn in enumerate(self.backend.history): self.ui.console.print(f"[{i}] {turn}")
    async def cmd_undo(self, ctx, *args):
        if self.backend and len(self.backend.history) >= 2:
            self.backend.history.pop(); self.backend.history.pop()
            self.ui.print_info("Undo.")
    async def cmd_config(self, ctx, *args): self.ui.console.print_json(data=self.config)
    async def cmd_exit(self, ctx, *args): sys.exit(0)
    async def cmd_save(self, ctx, *args):
        name = args[0] if args else None
        saved = self.session_manager.save_session(self.backend.history, self.protector._mask_map, self.protector._unmask_map, name)
        self.ui.print_info(f"Saved: {saved}")
    async def cmd_load(self, ctx, *args):
        if not args: return
        data = self.session_manager.load_session(args[0])
        if data:
            self.backend.history, self.protector._mask_map, self.protector._unmask_map = data['history'], data['mask_map'], data['unmask_map']
            self.ui.print_info("Loaded.")
    async def cmd_sessions(self, ctx, *args): self.ui.print_info(f"Sessions: {self.session_manager.list_sessions()}")
    async def cmd_resume(self, ctx, *args):
        latest = self.session_manager.get_latest_session()
        if latest: await self.cmd_load(ctx, latest)
    async def cmd_rewind(self, ctx, *args): await self.launch_rewind_ui()
    async def cmd_copy(self, ctx, *args):
        try: pyperclip.copy(self.last_response); self.ui.print_info("Copied last response.")
        except: self.ui.print_warning("Copy failed.")
    async def cmd_model(self, ctx, *args):
        if args: self.config['agent']['model'] = args[0]; ctx['should_reinit'] = True
    async def cmd_plan(self, ctx, *args): self.current_mode_idx = 2; ctx['should_reinit'] = True
    async def cmd_agents(self, ctx, *args):
        if args: self.active_persona = args[0].lower(); self.re_initialize(); ctx['should_reinit'] = True
    async def cmd_autonomy(self, ctx, *args):
        if args: self.autonomy_level = args[0].lower(); self.ui.print_info(f"Autonomy: {self.autonomy_level.upper()}")
    async def cmd_versions(self, ctx, *args): self.ui.display_versions(self._versions)
    async def cmd_clear(self, ctx, *args): self.ui.console.clear()
    async def cmd_efficient(self, ctx, *args): self.efficient_mode = not self.efficient_mode; self.ui.print_info(f"Efficient: {self.efficient_mode}")
    async def cmd_usage(self, ctx, *args): self.ui.print_info(f"Session Tokens: {self.telemetry.get_detailed_stats()['session']:,}")
    async def cmd_stats(self, ctx, *args):
        s = self.telemetry.get_detailed_stats()
        self.ui.print_info(f"Daily Total: {s['daily']:,} / {s['hard_limit']:, if s['hard_limit'] > 0 else '∞'}")
    async def cmd_goal(self, ctx, *args):
        if args: self.orchestrator.set_goal(" ".join(args)); self.ui.print_info(f"Goal: {self.orchestrator.goal}")
    async def cmd_mission(self, ctx, *args): self.ui.render_markdown(self.orchestrator.render_mission_control())
    async def cmd_sandbox(self, ctx, *args): self.sandbox.toggle(); self.ui.print_info(f"Sandbox: {self.sandbox.enabled}")
    async def cmd_file(self, ctx, *args):
        if args:
            c = await self.read_file(args[0])
            if not c.startswith("Blocked"): self.prompt += f"\n\n--- File: {args[0]} ---\n{self.protector.mask(c)}"; self.ui.print_info("File injected.")
    async def cmd_export(self, ctx, *args):
        path = args[0] if args else "export.md"
        with open(path, 'w') as f: f.write(self.last_response); self.ui.print_info(f"Exported to {path}")
    async def cmd_refresh(self, ctx, *args): self.re_initialize(); self.ui.print_info("Refreshed.")
    async def cmd_fork(self, ctx, *args):
        name = f"fork_{datetime.now().strftime('%H%M%S')}"; await self.cmd_save(ctx, name); self.ui.print_info(f"Forked: {name}")
    async def cmd_peek(self, ctx, *args):
        if self.last_shell_output: self.ui.console.print(Panel(self.last_shell_output, title="Peek", border_style="cyan"))
    async def cmd_preview(self, ctx, *args): self.ui.console.print(Panel(self.last_response, title="Preview", border_style="green"))
    async def cmd_schedule(self, ctx, *args):
        if len(args) >= 3: self.ui.print_info(self.scheduler.schedule_once(args[0], int(args[1]), " ".join(args[2:])))
    async def cmd_compress(self, ctx, *args):
        self.backend.history = await ContextCompressor(self.backend).compress(self.backend.history); self.ui.print_info("Compressed.")
    async def cmd_skills(self, ctx, *args):
        sub = args[0] if args else "list"
        if sub == "list": self.ui.print_info(f"Skills: {self.skill_manager.list_skills()}")
        elif sub == "load" and len(args) > 1:
            sk = self.skill_manager.load_skill(args[1])
            if sk: self.prompt = sk.get('instruction', self.prompt); ctx['should_reinit'] = True; self.ui.print_info("Skill loaded.")
        elif sub == "save" and len(args) > 1: self.skill_manager.save_skill(args[1], {"instruction": self.prompt}); self.ui.print_info("Skill saved.")
    async def cmd_pin(self, ctx, *args):
        if args and args[0].isdigit(): self.backend.history[int(args[0])]['pinned'] = True
    async def cmd_unpin(self, ctx, *args):
        if args and args[0].isdigit(): self.backend.history[int(args[0])]['pinned'] = False
    async def cmd_commit(self, ctx, *args): self.ui.print_info(f"Git Commit: {self.git.commit_changes(' '.join(args) if args else 'Update')}")
    async def cmd_protect(self, ctx, *args):
        if len(args) >= 2: self.protector.add_pattern(args[0], args[1])
    async def cmd_unprotect(self, ctx, *args):
        if args: self.protector.remove_pattern(args[0])
    async def cmd_group(self, ctx, *args):
        if len(args) >= 2: self.last_response = await self.group_chat.run_group_discussion(args[0].split(','), " ".join(args[1:]))
    async def cmd_mcp(self, ctx, *args):
        if len(args) >= 3: self.ui.print_info(await self.mcp_manager.connect_external_stdio(args[1], args[2], args[3:]))
    async def cmd_inline(self, ctx, *args):
        def _in(): print("\n" + "="*20); return input("Inline: ")
        cmd = await run_in_terminal(_in)
        if cmd and cmd.strip():
            cmd = cmd.strip()
            if cmd.startswith('!'): await self.run_shell(cmd[1:].strip())
            elif cmd.startswith('/'): await self.commands.handle(cmd, ctx)
            else: await self.chat_cycle(cmd)

    async def switch_mode(self, new_mode: str):
        if self.backend: await self.backend.close()
        self.cli_mode = new_mode
        if self.cli_mode == "agents": self.backend = AgentBackend(self.config, self.prompt, ask_user_handler=self.run_shell)
        else: self.backend = ChatBackend(self.config, self.prompt)
        await self.backend.initialize(); self.ui.print_info(f"Switched to {self.cli_mode.upper()} backend.")

    def re_initialize(self):
        self.config = self.resolver.resolve_settings(); self.personas = self.resolver.discover_personas()
        self.active_persona = list(self.personas.keys())[0] if self.active_persona not in self.personas else self.active_persona
        self.prompt = self.personas.get(self.active_persona)
        self._cached_cwd = os.getcwd().replace(os.path.expanduser('~'), '~')
        self._cached_sandbox = "sandboxed" if self.config.get('enableTerminalSandbox') else "no sandbox"
        self._versions = {lib: metadata.version(lib) if metadata.version(lib) else "N/A" for lib in ['google-antigravity', 'google-genai', 'rich', 'prompt-toolkit', 'pyyaml', 'pyperclip', 'python-dotenv']}

    def is_path_ignored(self, path: str) -> bool:
        try:
            p = os.path.relpath(os.path.abspath(path), os.getcwd())
            for pattern in self.config.get("exclude_paths", []):
                if fnmatch.fnmatch(p, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern): return True
        except: pass
        return False

    async def read_file(self, path):
        if self.is_path_ignored(path): return "Blocked: Policy."
        try:
            with open(path, 'r', encoding='utf-8') as f: return f.read()
        except Exception as e: return f"Error: {e}"

    async def write_file(self, path, content):
        if self.modes[self.current_mode_idx] == 'plan' or self.is_path_ignored(path): return "Blocked."
        if self.modes[self.current_mode_idx] != 'auto-edit' and self.autonomy_level != 'always':
            old = ""; 
            if os.path.exists(path):
                with open(path, 'r') as f: old = f.read()
            self.diff_viewer.display_diff(old, content, path)
            with patch_stdout(): confirm = await self.session.prompt_async(HTML(f"<b>Apply to {path}?</b> (y/N): "))
            if confirm.lower() != 'y': return "Cancelled."
        with open(path, 'w', encoding='utf-8') as f: f.write(content)
        return "Success."

    async def run_shell(self, cmd):
        if self.modes[self.current_mode_idx] == 'plan': return "Blocked."
        if self.autonomy_level != 'always':
            with patch_stdout(): confirm = await self.session.prompt_async(HTML(f"<b>Run?</b> <style fg='red'>{cmd}</style> (y/N): "))
            if confirm.lower() != 'y': return "Cancelled."
        try:
            res = await self.sandbox.execute_sandboxed(cmd); self.last_shell_output = f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
            return self.last_shell_output
        except Exception as e: return f"Error: {e}"

    async def launch_rewind_ui(self):
        if not self.backend or not self.backend.history: return
        self.ui.console.print(Panel("REWIND", border_style="yellow"))
        for i, turn in enumerate(self.backend.history): self.ui.console.print(f" [{i}] {turn.get('content', '')[:60]}")
        with patch_stdout(): idx = await self.session.prompt_async("Index: ")
        if idx.isdigit(): self.backend.history = self.backend.history[:int(idx)+1]

    async def chat_cycle(self, user_input):
        file_refs = re.findall(r'@(?:\"([^\"]+)\"|([^\s\n]+))', user_input)
        injected = ""
        for q, u in file_refs:
            p = q if q else u; c = await self.read_file(p)
            if not c.startswith("Error") and not c.startswith("Blocked"): injected += f"\n\n--- File: {p} ---\n{c}\n"
        full_input = user_input + injected; masked_input = self.protector.mask(full_input); self.payload_logger.log_payload(self.cli_mode, masked_input)
        try:
            self.ui.console.print(f"\n[{self.cli_mode}]🤖:"); 
            with self.ui.create_live_display() as live:
                response, usage = await self.backend.chat(masked_input); self.telemetry.update_usage(usage)
                content = ""
                if hasattr(response, 'text'):
                    res_attr = response.text
                    if asyncio.iscoroutine(res_attr) or asyncio.iscoroutinefunction(res_attr):
                        content = await res_attr() if asyncio.iscoroutinefunction(res_attr) else await res_attr
                    elif callable(res_attr): content = res_attr()
                    else: content = res_attr
                elif hasattr(response, 'candidates'): content = response.candidates[0].content.parts[0].text
                else: content = str(response)
                full_text = self.protector.mask(content, is_response=True); live.update(Markdown(self.protector.unmask(full_text)))
            self.last_response = self.protector.unmask(full_text); self.backend.history.append({"role": "user", "content": user_input}); self.backend.history.append({"role": "assistant", "content": self.last_response})
        except Exception as e: self.ui.print_error(f"Error: {e}")

    async def run(self):
        load_dotenv()
        while True:
            await self.switch_mode(self.cli_mode)
            ctx = {'should_reinit': False}
            while not ctx['should_reinit']:
                try:
                    def get_toolbar(): return self.ui.get_dashboard_toolbar(self._cached_cwd, self._cached_sandbox, self.config['agent']['model'], self.telemetry.format_quota_display(), self.cli_mode, self.modes[self.current_mode_idx])
                    with patch_stdout():
                        user_input = await self.session.prompt_async("> ", bottom_toolbar=get_toolbar, rprompt=HTML('<style fg="ansigray">? for shortcuts</style>'), multiline=self.multiline, complete_while_typing=True)
                    user_input = user_input.strip()
                    if not user_input: continue
                    if user_input.startswith('/'):
                        if await self.commands.handle(user_input, ctx): continue
                    elif user_input.startswith('!'): await self.run_shell(user_input[1:].strip())
                    else: self._current_task = asyncio.create_task(self.chat_cycle(user_input)); await self._current_task
                except KeyboardInterrupt: continue
                except EOFError: return
        self.protector.clear()

def main(): asyncio.run(UnifiedSecureCLI().run())
if __name__ == "__main__": main()
