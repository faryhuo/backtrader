"""
Logger Configuration Module.

Provides centralized logging configuration loaded from JSON config file.
Supports console/file handlers, per-module log levels, and sensitive field masking.

Usage:
    from src.utils.logger import setup_logging, get_logger
    
    # Configure logging at application startup
    setup_logging()
    
    # Get logger for a module
    logger = get_logger(__name__)
"""

import json
import logging
import logging.handlers
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# Default config path
CONFIG_DIR = Path(__file__).parent.parent.parent / "resources" / "config"
DEFAULT_CONFIG_FILE = CONFIG_DIR / "logger_config.json"
TEMPLATE_CONFIG_FILE = CONFIG_DIR / "logger_config.template.json"

# Default log format string
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Default configuration if no config file exists
DEFAULT_CONFIG = {
    "logging": {
        "level": "INFO",
        "format": DEFAULT_LOG_FORMAT,
        "date_format": "%Y-%m-%d %H:%M:%S",
        "handlers": {
            "console": {
                "enabled": True,
                "level": "INFO",
                "format": DEFAULT_LOG_FORMAT
            },
            "file": {
                "enabled": False,
                "level": "DEBUG",
                "filename": "logs/app.log",
                "max_bytes": 10485760,
                "backup_count": 5,
                "format": DEFAULT_LOG_FORMAT
            }
        }
    },
    "loggers": {},
    "sensitive_fields": {
        "mask_patterns": ["password", "api_key", "secret", "token", "credential"],
        "mask_char": "*",
        "visible_chars": 4
    }
}

# Module-level config cache
_config: Optional[Dict[str, Any]] = None
_is_configured: bool = False


def load_config() -> Dict[str, Any]:
    """
    Load logging configuration from JSON file.
    
    Priority:
    1. logger_config.json (user customized)
    2. logger_config.template.json (default template)
    3. Built-in DEFAULT_CONFIG
    
    Returns:
        Configuration dictionary
    """
    global _config
    
    if _config is not None:
        return _config
    
    config_file = None
    
    # Check for customized config first
    if DEFAULT_CONFIG_FILE.exists():
        config_file = DEFAULT_CONFIG_FILE
    elif TEMPLATE_CONFIG_FILE.exists():
        config_file = TEMPLATE_CONFIG_FILE
    
    if config_file:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                _config = json.load(f)
            return _config
        except (json.JSONDecodeError, IOError) as e:
            # Fall back to default if config file is invalid
            print(f"Warning: Failed to load logger config from {config_file}: {e}")
    
    _config = DEFAULT_CONFIG.copy()
    return _config


def get_log_level(level_str: str) -> int:
    """
    Convert log level string to logging constant.
    
    Args:
        level_str: Log level name (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Logging level constant
    """
    return getattr(logging, level_str.upper(), logging.INFO)


class SensitiveDataFilter(logging.Filter):
    """
    Filter to mask sensitive data in log messages.
    
    Patterns defined in config's sensitive_fields.mask_patterns will be masked.
    """
    
    def __init__(self, patterns: List[str], mask_char: str = "*", visible_chars: int = 4):
        super().__init__()
        self.patterns = patterns
        self.mask_char = mask_char
        self.visible_chars = visible_chars
        # Build regex pattern: key=value or "key": "value"
        self._compiled_patterns = [
            re.compile(
                rf'({pattern}["\']?\s*[:=]\s*["\']?)([^\s"\']+)',
                re.IGNORECASE
            )
            for pattern in patterns
        ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Apply masking to log record message."""
        if record.msg:
            msg = str(record.msg)
            for pattern in self._compiled_patterns:
                msg = pattern.sub(self._mask_match, msg)
            record.msg = msg
        return True
    
    def _mask_match(self, match: re.Match) -> str:
        """Mask the value portion of a key-value pair."""
        prefix = match.group(1)
        value = match.group(2)
        
        if len(value) <= self.visible_chars:
            masked = self.mask_char * len(value)
        else:
            masked = value[:self.visible_chars] + self.mask_char * (len(value) - self.visible_chars)
        
        return prefix + masked


def setup_logging(config_override: Optional[Dict[str, Any]] = None) -> None:
    """
    Configure logging based on config file or provided configuration.
    
    Config format: handlers are enabled via loggers.root.handlers array.
    
    Args:
        config_override: Optional config dict to override file-based config
    """
    global _is_configured
    
    if _is_configured:
        return
    
    config = config_override or load_config()
    log_config = config.get("logging", DEFAULT_CONFIG["logging"])
    loggers_config = config.get("loggers", {})
    sensitive_config = config.get("sensitive_fields", DEFAULT_CONFIG["sensitive_fields"])
    
    # Get root logger config
    root_logger_config = loggers_config.get("root", {})
    
    # Get enabled handlers from loggers.root.handlers array
    enabled_handlers = set(root_logger_config.get("handlers", ["console"]))
    
    # Get root level: priority is ENV > loggers.root.level > logging.level > default
    root_level_str = os.getenv(
        "LOG_LEVEL",
        root_logger_config.get("level", log_config.get("level", "INFO"))
    )
    root_level = get_log_level(root_level_str)
    
    # Create formatters
    default_format = log_config.get("format", DEFAULT_CONFIG["logging"]["format"])
    date_format = log_config.get("date_format", "%Y-%m-%d %H:%M:%S")
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(root_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Setup handlers based on config
    handlers_config = log_config.get("handlers", {})
    
    # Console handler
    if "console" in enabled_handlers:
        console_config = handlers_config.get("console", {})
        console_handler = logging.StreamHandler()
        console_level = get_log_level(console_config.get("level", root_level_str))
        console_handler.setLevel(console_level)
        
        console_format = console_config.get("format", default_format)
        console_handler.setFormatter(logging.Formatter(console_format, datefmt=date_format))
        
        root_logger.addHandler(console_handler)
    
    # File handler
    if "file" in enabled_handlers:
        file_config = handlers_config.get("file", {})
        log_file = Path(file_config.get("filename", "logs/app.log"))
        
        # Create log directory if needed
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file),
            maxBytes=file_config.get("max_bytes", 10485760),
            backupCount=file_config.get("backup_count", 5),
            encoding='utf-8'
        )
        file_level = get_log_level(file_config.get("level", "DEBUG"))
        file_handler.setLevel(file_level)
        
        file_format = file_config.get("format", default_format)
        file_handler.setFormatter(logging.Formatter(file_format, datefmt=date_format))
        
        root_logger.addHandler(file_handler)
    
    # Configure per-module loggers
    for logger_name, logger_config in loggers_config.items():
        if logger_name == "root":
            continue
        
        module_logger = logging.getLogger(logger_name)
        
        if "level" in logger_config:
            module_logger.setLevel(get_log_level(logger_config["level"]))
        
        if "propagate" in logger_config:
            module_logger.propagate = logger_config["propagate"]
    
    # Add sensitive data filter to all handlers
    if sensitive_config.get("mask_patterns"):
        sensitive_filter = SensitiveDataFilter(
            patterns=sensitive_config["mask_patterns"],
            mask_char=sensitive_config.get("mask_char", "*"),
            visible_chars=sensitive_config.get("visible_chars", 4)
        )
        for handler in root_logger.handlers:
            handler.addFilter(sensitive_filter)
    
    _is_configured = True
    
    # Log startup info
    logging.info(f"Logging configured with level: {root_level_str}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.
    
    Ensures logging is configured before returning logger.
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    if not _is_configured:
        setup_logging()
    
    return logging.getLogger(name)


def setup_worker_logging(config_override: Optional[Dict[str, Any]] = None) -> None:
    """
    Configure logging for worker processes.
    
    Uses worker_logging section from config for isolated worker process logging.
    
    Args:
        config_override: Optional config dict to override file-based config
    """
    config = config_override or load_config()
    worker_config = config.get("worker_logging", {})
    
    level_str = worker_config.get("level", "INFO")
    format_str = worker_config.get("format", "[Worker] %(levelname)s - %(message)s")
    
    logging.basicConfig(
        level=get_log_level(level_str),
        format=format_str,
        force=True  # Override any existing configuration
    )
