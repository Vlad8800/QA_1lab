"""
Centralized logging configuration setup.
"""
import logging
import sys
from typing import Optional

from app.privacy.filter import PIISanitizingFilter
from app.privacy.formatter import SafeTextFormatter, StructuredJsonFormatter


def setup_privacy_logging(
    log_level: int = logging.INFO,
    json_format: bool = True,
    handler: Optional[logging.Handler] = None
) -> logging.Logger:
    """
    Configures application-wide privacy-safe logging.
    Applies PIISanitizingFilter and StructuredJsonFormatter to the root logger.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicate logs
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)

    # Setup target stream handler
    target_handler = handler or logging.StreamHandler(sys.stdout)
    target_handler.setLevel(log_level)

    # Attach centralized sanitizing filter directly to loggers
    sanitizing_filter = PIISanitizingFilter()
    root_logger.addFilter(sanitizing_filter)

    # Attach to target stream handler
    target_handler.addFilter(sanitizing_filter)

    # Attach formatter
    if json_format:
        formatter = StructuredJsonFormatter()
    else:
        formatter = SafeTextFormatter()
    target_handler.setFormatter(formatter)

    root_logger.addHandler(target_handler)

    # Also apply to app namespace logger
    app_logger = logging.getLogger("app")
    app_logger.setLevel(log_level)
    app_logger.addFilter(sanitizing_filter)

    return root_logger
