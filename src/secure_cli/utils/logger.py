import os
import json
import logging
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from queue import Queue
from logging.handlers import QueueHandler, QueueListener
from typing import Optional, List, Dict, Any
from contextvars import ContextVar

# Trace ID context variable for propagation across async/threads
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="N/A")

class LogStrategy(ABC):
    """[Strategy Pattern] Interface for different logging backends."""
    @abstractmethod
    def emit(self, record: logging.LogRecord):
        pass

class FileLogStrategy(LogStrategy):
    """Strategy for logging to a local file."""
    def __init__(self, log_dir: str, filename: str):
        self.log_path = os.path.join(log_dir, filename)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
    def emit(self, record: logging.LogRecord):
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        trace_id = getattr(record, "trace_id", "N/A")
        log_entry = f"{timestamp} - [{record.levelname}] - [Trace:{trace_id}] - {record.getMessage()}\n"
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(log_entry)

class JSONLogStrategy(LogStrategy):
    """Strategy for logging in JSON format (Audit friendly)."""
    def __init__(self, log_dir: str, filename: str):
        self.log_path = os.path.join(log_dir, filename)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def emit(self, record: logging.LogRecord):
        entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "trace_id": getattr(record, "trace_id", "N/A"),
            "module": record.module,
            "message": record.getMessage(),
            "extra": getattr(record, "extra", {})
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

class StrategyHandler(logging.Handler):
    """Custom logging handler that dispatches to LogStrategies."""
    def __init__(self, strategies: List[LogStrategy]):
        super().__init__()
        self.strategies = strategies

    def emit(self, record: logging.LogRecord):
        # Attach Trace ID from ContextVar to the record
        record.trace_id = trace_id_var.get()
        for strategy in self.strategies:
            strategy.emit(record)

class SecureLogger:
    """
    [Enriched Logger] 
    Supports Hierarchical levels, Strategy Pattern, and Asynchronous logging.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SecureLogger, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        if self._initialized:
            # Allow dynamic level change even if already initialized
            self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
            return
        
        self.log_dir = log_dir
        self.logger = logging.getLogger("SecureCLI")
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # Define strategies
        self.strategies = [
            FileLogStrategy(log_dir, "unified_secure_cli.log"),
            JSONLogStrategy(log_dir, "security_audit.log")
        ]
        
        # [Asynchronous Logging] Setup Queue
        self.log_queue = Queue(-1)
        queue_handler = QueueHandler(self.log_queue)
        self.logger.addHandler(queue_handler)
        
        # Setup Listener with StrategyHandler
        strategy_handler = StrategyHandler(self.strategies)
        self.listener = QueueListener(self.log_queue, strategy_handler)
        self.listener.start()
        
        self._initialized = True

    def set_trace_id(self, trace_id: str):
        """Sets the Trace ID for the current context."""
        trace_id_var.set(trace_id)

    def debug(self, msg: str, **kwargs): self.logger.debug(msg, extra={"extra": kwargs})
    def info(self, msg: str, **kwargs): self.logger.info(msg, extra={"extra": kwargs})
    def warning(self, msg: str, **kwargs): self.logger.warning(msg, extra={"extra": kwargs})
    def error(self, msg: str, **kwargs): self.logger.error(msg, extra={"extra": kwargs})
    def critical(self, msg: str, **kwargs): self.logger.critical(msg, extra={"extra": kwargs})

    # Legacy Compatibility
    def log_payload(self, backend: str, payload: str):
        """AI로 전송되기 직전의 마스킹된 페이로드를 기록합니다 (Legacy PayloadLogger compatibility)."""
        entry = {
            "backend": backend,
            "masked_payload": payload
        }
        # Audit log via JSONStrategy
        self.info(f"Payload Outgoing ({backend})", **entry)
        
        # Also write to debug_payload.log (raw text for convenience)
        debug_log = os.path.join(self.log_dir, "debug_payload.log")
        with open(debug_log, "a", encoding="utf-8") as f:
            f.write(f"\n--- [{datetime.now().isoformat()}] [{backend}] [Trace:{trace_id_var.get()}] ---\n")
            f.write(payload)
            f.write("\n" + "="*50 + "\n")

    def stop(self):
        """Gracefully shuts down the logging listener."""
        if hasattr(self, 'listener'):
            self.listener.stop()
        self._initialized = False

# Simple mapping for PayloadLogger replacement
class PayloadLogger(SecureLogger):
    """Maintain backward compatibility for existing imports."""
    pass
