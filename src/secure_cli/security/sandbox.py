import subprocess
import asyncio
import os
import sys
import platform
import logging

class SandboxManager:
    """Manages OS-level command isolation for shell executions."""
    
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.os_type = platform.system().lower()
        self.logger = logging.getLogger("Sandbox")

    def wrap_command(self, cmd: str) -> str:
        """Wraps a shell command in an OS-native sandbox if enabled."""
        if not self.enabled:
            return cmd
            
        if self.os_type == 'darwin': # macOS
            # Strict Profile: Deny network, allow only process exec and limited file reads.
            # No write access outside of /tmp.
            profile = (
                "(version 1)"
                "(deny default)"
                "(allow process-exec)"
                "(allow file-read* (subpath \"/usr/lib\"))"
                "(allow file-read* (subpath \"/lib\"))"
                "(allow file-read* (subpath \"/System/Library\"))"
                "(allow file-read* (subpath \"/bin\"))"
                "(allow file-read* (subpath \"/usr/bin\"))"
                "(allow file-read* (subpath \".\"))"
                "(allow file-write* (subpath \"/tmp\"))"
                "(deny network*)"
            )
            return f"sandbox-exec -p '{profile}' {cmd}"
            
        elif self.os_type == 'linux': # Linux
            # Stricter nsjail: No network, limited filesystem.
            return f"nsjail -Mo --chroot / --user 9999 --group 9999 --proc_rw --R /bin --R /lib --R /usr --R /lib64 --B /tmp -- {cmd}"
            
        return cmd

    async def execute_sandboxed(self, cmd: str) -> subprocess.CompletedProcess:
        """Executes a command within the sandbox environment using async subprocess."""
        wrapped = self.wrap_command(cmd)
        self.logger.info(f"Executing sandboxed: {wrapped}")
        
        process = await asyncio.create_subprocess_shell(
            wrapped,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
        
        return subprocess.CompletedProcess(
            args=wrapped,
            returncode=process.returncode or 0,
            stdout=stdout.decode() if stdout else "",
            stderr=stderr.decode() if stderr else ""
        )
        
    def toggle(self, state: bool = None):
        if state is None: self.enabled = not self.enabled
        else: self.enabled = state
