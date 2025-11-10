"""Logging Configuration.

This module sets up logging for the RAG Backend application with support for
structured logging, multiple output formats, and environment-specific configurations.
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Any

try:
    from pythonjsonlogger import jsonlogger

    JSON_LOGGER_AVAILABLE = True
except ImportError:
    JSON_LOGGER_AVAILABLE = False


def setup_logging(
    level: str = "INFO",
    format_type: str = "standard",
    output: str = "stdout",
    file_path: str | None = None,
) -> logging.Logger:
    """Set up logging configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type ("standard", "json", "detailed")
        output: Output destination ("stdout", "stderr", "file")
        file_path: File path for file output

    Returns:
        Configured logger instance
    """
    # Define log formats
    formats = {
        "standard": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s",
        "json": "%(asctime)s %(name)s %(levelname)s %(message)s",
    }

    # Create formatter
    if format_type == "json" and JSON_LOGGER_AVAILABLE:
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        formatter = logging.Formatter(
            fmt=formats.get(format_type, formats["standard"]),
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Create handler based on output type
    handler: logging.FileHandler | logging.StreamHandler[Any]
    if output == "file" and file_path:
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(file_path)
    elif output == "stderr":
        handler = logging.StreamHandler(sys.stderr)
    else:  # stdout (default)
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(formatter)
    handler.setLevel(getattr(logging, level.upper()))

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    # Add our handler
    logger.addHandler(handler)

    return logger


def get_logging_config(
    level: str = "INFO",
    format_type: str = "standard",
    output: str = "stdout",
    file_path: str | None = None,
) -> dict[str, Any]:
    """Get logging configuration dictionary for logging.config.dictConfig().

    Args:
        level: Log level
        format_type: Format type
        output: Output destination
        file_path: File path for file output

    Returns:
        Logging configuration dictionary
    """
    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": format_type,
                "stream": "ext://sys.stdout",
            }
        },
        "root": {"level": level, "handlers": ["console"]},
        "loggers": {
            "rag_backend": {
                "level": level,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "fastapi": {"level": "INFO", "handlers": ["console"], "propagate": False},
        },
    }

    # Add JSON formatter if available
    if JSON_LOGGER_AVAILABLE and format_type == "json":
        config["formatters"]["json"] = {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }

    # Add file handler if needed
    if output == "file" and file_path:
        config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "level": level,
            "formatter": format_type,
            "filename": file_path,
            "mode": "a",
        }

        # Update handlers to include file
        config["root"]["handlers"].append("file")
        for logger_config in config["loggers"].values():
            logger_config["handlers"].append("file")

    return config


def configure_uvicorn_logging() -> None:
    """Configure uvicorn logging to integrate with our logging setup."""
    # Disable uvicorn access logger to prevent duplicate logs
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.disabled = True

    # Configure uvicorn error logger
    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"rag_backend.{name}")


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return get_logger(self.__class__.__module__)


# Example usage functions for different components
def log_document_processing(document_id: str, status: str, **kwargs: Any) -> None:
    """Log document processing events."""
    logger = get_logger("processors")
    logger.info(
        "Document processing update",
        extra={"document_id": document_id, "status": status, **kwargs},
    )


def log_query_processing(query_id: str, processing_time: float, **kwargs: Any) -> None:
    """Log query processing events."""
    logger = get_logger("query")
    logger.info(
        "Query processed",
        extra={"query_id": query_id, "processing_time": processing_time, **kwargs},
    )


def log_error(error: Exception, context: dict[str, Any] | None = None) -> None:
    """Log error with context information."""
    logger = get_logger("error")
    logger.error(
        f"Error occurred: {error!s}",
        extra={"error_type": type(error).__name__, "context": context or {}},
        exc_info=True,
    )
