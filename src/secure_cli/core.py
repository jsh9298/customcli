import asyncio
import os
import sys
import yaml
import json
import fnmatch
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# UI & prompt-toolkit
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.patch_stdout import patch_stdout

# Modules
from secure_cli.security.protector import SecurityProtector, RegexMaskingStrategy
from secure_cli.security.sandbox import SandboxManager
from secure_cli.state.session import SessionManager
from secure_cli.state.telemetry import TelemetryManager
from secure_cli.ui.controller import UIController
from secure_cli.ui.keybindings import UIKeyBindings
from secure_cli.ui.completer import SmartCompleter
from secure_cli.commands.registry import CommandRegistry

# Modular Handlers
from secure_cli.commands.handlers.ai import AIHandlers
from secure_cli.commands.handlers.session import SessionHandlers
from secure_cli.commands.handlers.system import SystemHandlers
from secure_cli.commands.handlers.tools import ToolHandlers
from secure_cli.commands.handlers import CommandHandlers # Transitional

from secure_cli.agent.backends.factory import BackendFactory
from secure_cli.agent.orchestrator import AgentOrchestrator
from secure_cli.utils.mcp import MCPManager
from secure_cli.utils.git import GitUtility
from secure_cli.utils.terminal_adapter import LocalTerminalAdapter
from secure_cli.utils.rag import LocalRAGEngine
from secure_cli.utils.logger import PayloadLogger
from secure_cli.utils.skills import SkillManager

class ConfigResolver:
    GLOBAL_ROOT = os.path.expanduser('~/.gemini/antigravity-cli')
    PROJECT_ROOT = os.path.abspath('.antigravity')
    def __init__(self):
        for p in [self.GLOBAL_ROOT, self.PROJECT_ROOT]: os.makedirs(p, exist_ok=True)
    def resolve_settings(self):
        base = {"agent": {"model": "gemini-3.5-flash", "temperature": 0.7}, "exclude_paths": [".env", ".git", "*.log"]}
        for p in [os.path.join(self.PROJECT_ROOT, 'agent_config.yaml'), 'agent_config.yaml']:
            if os.path.exists(p):
                with open(p, 'r') as f: data = yaml.safe_load(f); self.deep_merge(base, data)
        return base
    def deep_merge(self, base, override):
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict): self.deep_merge(base[k], v)
            else: base[k] = v
    def discover_personas(self):
        return {"default": "You are a helpful unified secure assistant."}

class UnifiedSecureCLI:
    def __init__(self, initial_mode: str = "agents"):
        self.resolver = ConfigResolver()
        self.config = self.resolver.resolve_settings()
        self.protector = SecurityProtector()
        self._setup_security_strategies()
        self.ui = UIController(theme_name=self.config.get('ui', {}).get('theme', 'neon'))
        
        self.payload_logger = PayloadLogger()
        self.session_manager = SessionManager()
        self.telemetry = TelemetryManager()
        
        self.sandbox = SandboxManager()
        self.terminal_adapter = LocalTerminalAdapter(self.sandbox, self.ui, "review")
        self.rag_engine = LocalRAGEngine(self)
        self.mcp_manager = MCPManager(self.protector)
        self.git = GitUtility()
        self.orchestrator = AgentOrchestrator(self)
        self.skill_dir = os.path.join(self.resolver.PROJECT_ROOT, 'skills')
        self.skill_manager = SkillManager(self.skill_dir)
        
        self.commands = CommandRegistry()
        self.ai_h = AIHandlers(self)
        self.session_h = SessionHandlers(self)
        self.system_h = SystemHandlers(self)
        self.tool_h = ToolHandlers(self)
        self.legacy_h = CommandHandlers(self)
        
        self.register_commands()
        
        self.ui_bindings = UIKeyBindings(self)
        self.session = PromptSession(
            history=FileHistory(os.path.expanduser('~/.unified_secure_history')),
            key_bindings=self.ui_bindings.get_bindings(),
            style=self.ui.get_style(),
            completer=SmartCompleter(self),
            complete_while_typing=True
        )

        self.cli_mode = initial_mode
        self.backend = None
        self.modes = ['default', 'auto-edit', 'plan']
        self.current_mode_idx = 0
        self.autonomy_level = "review"
        self.active_persona = "default"
        self.available_models = ["gemini-3.5-flash", "gemini-3.5-pro", "antigravity-preview-05-2026"]
        self._current_task = None

        self.re_initialize()

    def _setup_security_strategies(self):
        self.protector.add_strategy(RegexMaskingStrategy(r'\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b', '[EMAIL]'))

    def register_commands(self):
        """[Strict Mode Separation] Define identity for AGY and Gemini-CLI."""
        h_ai = self.ai_h
        h_sess = self.session_h
        h_sys = self.system_h
        h_tool = self.tool_h
        h_leg = self.legacy_h

        # --- 1. SHARED COMMANDS ---
        shared = ['chat', 'agents']
        self.commands.register('/help', h_leg.help, "전체 명령어 도움말", tags=shared)
        self.commands.register('/model', h_ai.model, "AI 모델 변경 (Hybrid)", tags=shared)
        self.commands.register('/theme', h_ai.theme, "UI 테마 변경 (Hybrid)", tags=shared)
        self.commands.register('/mode', h_sys.mode, "워크스테이션 모드 전환", tags=shared)
        self.commands.register('/rag', h_tool.rag, "RAG 지식베이스 브라우저", tags=shared)
        self.commands.register('/skills', h_ai.skills, "에이전트 스킬 관리", tags=shared)
        self.commands.register('/clear', h_sys.clear, "화면 및 히스토리 초기화", tags=shared)
        self.commands.register('/exit', h_sys.exit, "종료", tags=shared)

        # --- 2. AGENTS MODE (agy) IDENTITY ---
        self.commands.register('/config', h_sys.config, "시스템 영구 설정 (UI)", tags=['agents'])
        self.commands.register('/goal', h_tool.goal, "미션 목표 관리 (Hybrid)", tags=['agents'])
        self.commands.register('/mcp', h_tool.mcp, "MCP 서버 관리 (Hybrid)", tags=['agents'])
        self.commands.register('/shells', h_sys.shells, "프로세스 대시보드 (Hybrid)", tags=['agents'])
        self.commands.register('/permissions', h_sys.permissions, "자율성 권한 설정 (Hybrid)", tags=['agents'])
        
        # --- 3. CHAT MODE (gemini-cli) IDENTITY ---
        self.commands.register('/settings', h_sys.config, "영구 설정 변경 (UI)", tags=['chat'])
        self.commands.register('/undo', h_sess.rewind, "이전 대화 취소", tags=['chat'])
        self.commands.register('/save', h_sess.save, "세션 저장", tags=['chat'])
        self.commands.register('/load', h_sess.load, "세션 불러오기 (Hybrid)", tags=['chat'])
        self.commands.register('/usage', h_leg.usage_unified, "토큰 리소스 통계", tags=['chat'])

        self.commands.alias('/undo', '/rewind')
        self.commands.alias('/switch', '/mode')

    def re_initialize(self):
        self.config = self.resolver.resolve_settings()
        self.personas = self.resolver.discover_personas()
        self.prompt = self.personas.get(self.active_persona, "Helpful assistant.")
        self._cached_cwd = os.getcwd().replace(os.path.expanduser('~'), '~')

    def is_path_ignored(self, path: str) -> bool:
        exclude_patterns = self.config.get('exclude_paths', [])
        normalized_path = os.path.normpath(path)
        parts = normalized_path.split(os.sep)
        for pattern in exclude_patterns:
            if any(fnmatch.fnmatch(part, pattern) for part in parts):
                return True
            if fnmatch.fnmatch(normalized_path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern):
                return True
        return False

    async def chat_cycle(self, user_input: str):
        import uuid
        self.payload_logger.set_trace_id(str(uuid.uuid4())[:8])
        masked_input = self.protector.mask(user_input)
        
        try:
            self.ui.console.print(self.ui.colorize_text(f"[{self.cli_mode}]🤖:"))
            full_response = ""
            with self.ui.create_live_display() as live:
                async for chunk in self.backend.chat_stream(masked_input):
                    full_response += chunk
                    live.update(self.ui.colorize_text(self.protector.unmask(self.protector.mask(full_response, is_response=True))))
            
            self.last_response = self.protector.unmask(self.protector.mask(full_response, is_response=True))
            self.backend.history.append({"role": "user", "content": user_input})
            self.backend.history.append({"role": "assistant", "content": self.last_response})
            self.telemetry.update_usage({"total_tokens": len(full_response)//4})

            # Auto-trigger Context Compression
            from secure_cli.utils.compressor import ContextCompressor
            compressor = ContextCompressor(self.backend, self.config)
            threshold = compressor.auto_threshold
            if threshold > 0 and len(self.backend.history) >= threshold:
                self.ui.print_info("⚡ Context threshold reached. Compressing conversation history...")
                self.backend.history = await compressor.compress(self.backend.history)
                self.ui.print_success("Context compressed successfully.")
        except Exception as e: self.ui.print_error(f"Error: {e}")

    async def run(self):
        load_dotenv()
        while True:
            self.backend = BackendFactory.create_backend(self.cli_mode, self.config, self.prompt, self.terminal_adapter.execute)
            await self.backend.initialize()
            ctx = {'should_reinit': False}
            while not ctx['should_reinit']:
                try:
                    toolbar = lambda: self.ui.get_dashboard_toolbar(self._cached_cwd, "sandbox", self.config['agent']['model'], self.telemetry.format_quota_display(), self.cli_mode, self.modes[self.current_mode_idx])
                    with patch_stdout():
                        user_input = await self.session.prompt_async("> ", bottom_toolbar=toolbar)
                    if not user_input.strip(): continue
                    if user_input.startswith('/'): await self.commands.handle(user_input, ctx)
                    elif user_input.startswith('!'): await self.terminal_adapter.execute(user_input[1:])
                    else: await self.chat_cycle(user_input)
                except (KeyboardInterrupt, EOFError): return

def main():
    try:
        asyncio.run(UnifiedSecureCLI().run())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
