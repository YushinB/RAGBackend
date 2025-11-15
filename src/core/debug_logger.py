"""
Debug Logging System for PDF Processing Pipeline

This module provides specialized logging utilities for debugging the PDF processing
pipeline with detailed tracing, performance metrics, and visual debugging aids.

The module uses functools.lru_cache for efficient lazy singleton implementation,
providing thread-safe instance creation with automatic caching and optional cache
clearing for testing scenarios.
"""

import functools
import json
import logging
import os
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, TypeVar

from .logging import get_logger

F = TypeVar("F", bound=Callable[..., Any])


class PDFDebugLogger:
    """Enhanced logger for PDF processing debugging with automatic production detection."""

    def __init__(
        self,
        name: str = "pdf_debug",
        level: str = "DEBUG",
        auto_detect_production: bool = True,
    ):
        self.logger = get_logger(name)

        # Auto-detect production and adjust settings
        if auto_detect_production:
            config = DebugConfig()
            if not config.enabled:
                # In production, set to ERROR level and disable detailed logging
                level = "ERROR"
                self.production_mode = True
            else:
                self.production_mode = False
        else:
            self.production_mode = False

        self.logger.setLevel(getattr(logging, level.upper()))
        self._operation_stack: list[str] = []
        self._performance_data: dict[str, list[float]] = {}

        if auto_detect_production and self.production_mode:
            self.logger.info(
                "Production environment detected - debug logging minimized"
            )

    def debug_stage(self, stage_name: str, **kwargs: Any) -> None:
        """Log a processing stage with context."""
        # Skip detailed debug logging in production
        if hasattr(self, "production_mode") and self.production_mode:
            return

        indent = "  " * len(self._operation_stack)
        message = f"{indent}🔄 {stage_name}"

        if kwargs:
            context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            message += f" | {context_str}"

        self.logger.debug(message)

    def debug_success(self, stage_name: str, **kwargs: Any) -> None:
        """Log successful completion of a stage."""
        indent = "  " * max(0, len(self._operation_stack) - 1)
        message = f"{indent}✅ {stage_name} completed"

        if kwargs:
            context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            message += f" | {context_str}"

        self.logger.debug(message)

    def debug_error(self, stage_name: str, error: Exception, **kwargs: Any) -> None:
        """Log error in a processing stage."""
        indent = "  " * max(0, len(self._operation_stack) - 1)
        message = f"{indent}❌ {stage_name} failed: {error}"

        if kwargs:
            context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            message += f" | {context_str}"

        self.logger.error(message, exc_info=True)

    def debug_data(self, data_name: str, data: Any, preview_length: int = 100) -> None:
        """Log data with preview for debugging."""
        # Skip detailed data logging in production
        if hasattr(self, "production_mode") and self.production_mode:
            return

        indent = "  " * len(self._operation_stack)

        if isinstance(data, (str, bytes)):
            preview = str(data)[:preview_length]
            if len(str(data)) > preview_length:
                preview += "..."
            self.logger.debug(
                f"{indent}📊 {data_name}: {type(data).__name__}({len(data)}) = '{preview}'"
            )

        elif isinstance(data, (list, tuple)):
            self.logger.debug(
                f"{indent}📊 {data_name}: {type(data).__name__}({len(data)}) items"
            )
            for i, item in enumerate(data[:3]):  # Show first 3 items
                self.logger.debug(
                    f"{indent}   [{i}]: {type(item).__name__} = {str(item)[:50]}..."
                )
            if len(data) > 3:
                self.logger.debug(f"{indent}   ... and {len(data) - 3} more items")

        elif isinstance(data, dict):
            self.logger.debug(
                f"{indent}📊 {data_name}: {type(data).__name__}({len(data)}) keys"
            )
            for _i, (key, value) in enumerate(list(data.items())[:3]):
                self.logger.debug(
                    f"{indent}   {key}: {type(value).__name__} = {str(value)[:50]}..."
                )
            if len(data) > 3:
                self.logger.debug(f"{indent}   ... and {len(data) - 3} more keys")

        else:
            self.logger.debug(
                f"{indent}📊 {data_name}: {type(data).__name__} = {str(data)[:preview_length]}"
            )

    def debug_performance(
        self, operation_name: str, duration: float, **metrics: Any
    ) -> None:
        """Log performance metrics."""
        indent = "  " * len(self._operation_stack)

        # Store performance data
        if operation_name not in self._performance_data:
            self._performance_data[operation_name] = []
        self._performance_data[operation_name].append(duration)

        # Format duration
        if duration < 1:
            duration_str = f"{duration * 1000:.2f}ms"
        else:
            duration_str = f"{duration:.2f}s"

        message = f"{indent}⏱️  {operation_name}: {duration_str}"

        if metrics:
            metrics_str = " | ".join(f"{k}={v}" for k, v in metrics.items())
            message += f" | {metrics_str}"

        self.logger.debug(message)

    def debug_image_processing(
        self,
        image_index: int,
        xref: int,
        width: int,
        height: int,
        format_type: str,
        size_bytes: int,
    ) -> None:
        """Specialized logging for image processing."""
        indent = "  " * len(self._operation_stack)
        size_mb = size_bytes / (1024 * 1024)

        self.logger.debug(
            f"{indent}🖼️  Image {image_index}: xref={xref} | {width}x{height} | "
            f"{format_type} | {size_mb:.2f}MB"
        )

    def debug_table_processing(
        self,
        table_index: int,
        rows: int,
        cols: int,
        headers: list[str] | None = None,
    ) -> None:
        """Specialized logging for table processing."""
        indent = "  " * len(self._operation_stack)
        headers_preview = ""
        if headers:
            headers_preview = f" | headers: {', '.join(headers[:3])}"
            if len(headers) > 3:
                headers_preview += "..."

        self.logger.debug(
            f"{indent}📋 Table {table_index}: {rows}x{cols}{headers_preview}"
        )

    def debug_equation_processing(
        self, eq_index: int, eq_type: str, latex_code: str
    ) -> None:
        """Specialized logging for equation processing."""
        indent = "  " * len(self._operation_stack)
        latex_preview = latex_code[:50] + "..." if len(latex_code) > 50 else latex_code

        self.logger.debug(
            f"{indent}🔢 Equation {eq_index} ({eq_type}): {latex_preview}"
        )

    def debug_chunking(
        self, chunk_index: int, chunk_size: int, chunk_type: str, overlap_size: int = 0
    ) -> None:
        """Specialized logging for text chunking."""
        indent = "  " * len(self._operation_stack)

        self.logger.debug(
            f"{indent}📦 Chunk {chunk_index}: {chunk_size} chars | {chunk_type} | "
            f"overlap: {overlap_size}"
        )

    @contextmanager
    def debug_operation(self, operation_name: str, **context: Any) -> Generator[None]:
        """Context manager for debugging operations with automatic timing."""
        self._operation_stack.append(operation_name)

        # Log operation start
        context_str = ""
        if context:
            context_str = " | " + " | ".join(f"{k}={v}" for k, v in context.items())

        indent = "  " * (len(self._operation_stack) - 1)
        self.logger.debug(f"{indent}🚀 Starting {operation_name}{context_str}")

        start_time = time.time()

        try:
            yield
            duration = time.time() - start_time
            self.debug_success(operation_name, duration=f"{duration:.2f}s")
            self.debug_performance(operation_name, duration)

        except Exception as e:
            duration = time.time() - start_time
            self.debug_error(operation_name, e, duration=f"{duration:.2f}s")
            raise

        finally:
            self._operation_stack.pop()

    def save_performance_report(self, output_path: str | Path) -> None:
        """Save performance analysis report to file."""
        report: dict[str, Any] = {
            "performance_summary": {},
            "raw_data": self._performance_data,
        }

        for operation, durations in self._performance_data.items():
            if durations:
                report["performance_summary"][operation] = {
                    "count": len(durations),
                    "total_time": sum(durations),
                    "average_time": sum(durations) / len(durations),
                    "min_time": min(durations),
                    "max_time": max(durations),
                }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Performance report saved to: {output_path}")

    def print_performance_summary(self) -> None:
        """Print performance summary to console."""
        if not self._performance_data:
            self.logger.info("No performance data collected")
            return

        self.logger.info("=" * 60)
        self.logger.info("PERFORMANCE SUMMARY")
        self.logger.info("=" * 60)

        for operation, durations in self._performance_data.items():
            if durations:
                count = len(durations)
                total = sum(durations)
                avg = total / count
                min_time = min(durations)
                max_time = max(durations)

                self.logger.info(
                    f"{operation}:\n"
                    f"  Count: {count}\n"
                    f"  Total: {total:.2f}s\n"
                    f"  Average: {avg:.2f}s\n"
                    f"  Range: {min_time:.2f}s - {max_time:.2f}s"
                )


def debug_operation(operation_name: str, **context: Any) -> Callable[[F], F]:
    """Decorator for debugging operations."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Try to get debug logger from self if it's a method
            debug_logger = None
            if args and hasattr(args[0], "debug_logger"):
                debug_logger = args[0].debug_logger
            else:
                debug_logger = PDFDebugLogger()

            with debug_logger.debug_operation(operation_name, **context):
                return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


def timed_operation(operation_name: str) -> Callable[[F], F]:
    """Decorator for timing operations."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Try to get debug logger from self if it's a method
                debug_logger = None
                if args and hasattr(args[0], "debug_logger"):
                    debug_logger = args[0].debug_logger
                else:
                    debug_logger = PDFDebugLogger()

                debug_logger.debug_performance(operation_name, duration)
                return result

            except Exception as e:
                duration = time.time() - start_time
                logger = get_logger("debug")
                logger.error(f"{operation_name} failed after {duration:.2f}s: {e}")
                raise

        return wrapper  # type: ignore

    return decorator


class DebugConfig:
    """Configuration for debug logging with automatic production detection."""

    def __init__(
        self,
        enabled: bool | None = None,
        level: str = "DEBUG",
        log_images: bool = True,
        log_tables: bool = True,
        log_equations: bool = True,
        log_chunking: bool = True,
        log_performance: bool = True,
        save_reports: bool = False,
        reports_dir: str | Path | None = None,
        auto_detect_production: bool = True,
    ):
        # Auto-detect production environment if enabled not explicitly set
        if enabled is None and auto_detect_production:
            self.enabled = not self._is_production_environment()
        else:
            self.enabled = enabled if enabled is not None else True

        # Adjust settings for production if detected
        if auto_detect_production and self._is_production_environment():
            self.level = "ERROR"  # Only log errors in production
            self.log_images = False
            self.log_tables = False
            self.log_equations = False
            self.log_chunking = False
            self.log_performance = False
            self.save_reports = False
        else:
            self.level = level
            self.log_images = log_images
            self.log_tables = log_tables
            self.log_equations = log_equations
            self.log_chunking = log_chunking
            self.log_performance = log_performance
            self.save_reports = save_reports

        self.reports_dir = Path(reports_dir) if reports_dir else Path("logs/debug")

        if self.save_reports:
            self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _is_production_environment(self) -> bool:
        """Detect if running in production environment."""
        # Check common production environment indicators
        env_indicators = [
            # Common environment variables
            os.getenv("ENVIRONMENT", "").lower() in ["prod", "production"],
            os.getenv("ENV", "").lower() in ["prod", "production"],
            os.getenv("NODE_ENV", "").lower() == "production",
            os.getenv("FLASK_ENV", "").lower() == "production",
            os.getenv("DJANGO_ENV", "").lower() == "production",
            os.getenv("PYTHON_ENV", "").lower() == "production",
            # Debug flags (if present and False, likely production)
            os.getenv("DEBUG", "").lower() in ["false", "0", "no"],
            os.getenv("DEBUG_MODE", "").lower() in ["false", "0", "no"],
            # Container/deployment indicators
            os.getenv("CONTAINER_ENV") == "production",
            os.getenv("DEPLOYMENT_ENV") == "production",
            # Cloud platform indicators
            "KUBERNETES_SERVICE_HOST" in os.environ,  # Kubernetes
            "AWS_EXECUTION_ENV" in os.environ,  # AWS Lambda
            "GOOGLE_CLOUD_PROJECT" in os.environ,  # Google Cloud
            "AZURE_FUNCTIONS_ENVIRONMENT" in os.environ,  # Azure Functions
            # Server indicators
            "SERVER_SOFTWARE" in os.environ
            and "production" in os.environ.get("SERVER_SOFTWARE", "").lower(),
        ]

        return any(env_indicators)

    def get_environment_info(self) -> dict[str, Any]:
        """Get information about the detected environment."""
        is_production = self._is_production_environment()
        return {
            "is_production": is_production,
            "environment_type": "production" if is_production else "development",
            "debug_enabled": self.enabled,
            "relevant_env_vars": {
                key: value
                for key, value in os.environ.items()
                if any(
                    indicator in key.lower()
                    for indicator in [
                        "env",
                        "debug",
                        "production",
                        "container",
                        "deployment",
                    ]
                )
            },
        }


@functools.lru_cache(maxsize=1)
def get_debug_logger() -> PDFDebugLogger:
    """Get global debug logger instance using lazy singleton pattern."""
    return PDFDebugLogger()


@functools.lru_cache(maxsize=1)
def init_debug_logging(config: DebugConfig | None = None) -> PDFDebugLogger:
    """Initialize debug logging with configuration using lazy singleton pattern."""
    if config is None:
        config = DebugConfig()

    if config.enabled:
        debug_logger = PDFDebugLogger(level=config.level)
        debug_logger.logger.info("Debug logging initialized")
    else:
        # Create a no-op logger
        debug_logger = PDFDebugLogger(level="CRITICAL")

    return debug_logger


@functools.lru_cache(maxsize=1)
def is_production() -> bool:
    """Quick utility to check if running in production environment."""
    config = DebugConfig()
    return not config.enabled


@functools.lru_cache(maxsize=1)
def get_production_safe_debug_logger() -> PDFDebugLogger:
    """Get a debug logger that automatically adjusts for production."""
    return PDFDebugLogger(auto_detect_production=True)
