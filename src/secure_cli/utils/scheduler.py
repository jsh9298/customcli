import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, Awaitable

class TaskScheduler:
    """백그라운드에서 주기적 또는 지연된 작업을 실행하는 스케줄러."""
    
    def __init__(self, callback: Callable[[str], Awaitable[None]]):
        self.tasks: Dict[str, asyncio.Task] = {}
        self.callback = callback
        self.logger = logging.getLogger("Scheduler")

    def schedule_once(self, name: str, delay_seconds: int, command: str):
        if name in self.tasks:
            self.tasks[name].cancel()
        
        task = asyncio.create_task(self._run_delayed(name, delay_seconds, command))
        self.tasks[name] = task
        return f"Task '{name}' scheduled in {delay_seconds}s."

    async def _run_delayed(self, name: str, delay: int, command: str):
        try:
            await asyncio.sleep(delay)
            self.logger.info(f"Executing scheduled task: {name}")
            await self.callback(command)
            del self.tasks[name]
        except asyncio.CancelledError:
            self.logger.info(f"Task {name} cancelled.")

    def list_tasks(self):
        return list(self.tasks.keys())

    def cancel_task(self, name: str):
        if name in self.tasks:
            self.tasks[name].cancel()
            del self.tasks[name]
            return True
        return False
