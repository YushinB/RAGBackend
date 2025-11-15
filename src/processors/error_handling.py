"""
Error handling and validation for document processors.

This module provides comprehensive error handling, validation,
and security features for the document processing pipeline.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

# Configure logger
logger = logging.getLogger(__name__)


class ProcessingErrorType(Enum):
    """Types of processing errors."""

    FILE_NOT_FOUND = "file_not_found"
    FILE_TOO_LARGE = "file_too_large"
    FILE_CORRUPTED = "file_corrupted"
    UNSUPPORTED_FORMAT = "unsupported_format"
    PERMISSION_DENIED = "permission_denied"
    MEMORY_ERROR = "memory_error"
    TIMEOUT_ERROR = "timeout_error"
    VALIDATION_ERROR = "validation_error"
    SECURITY_ERROR = "security_error"
    PROCESSING_ERROR = "processing_error"


class ProcessingError(Exception):
    """
    Base exception for processing errors.

    Attributes:
        error_type: Type of processing error
        message: Error message
        file_path: Path to the file that caused the error
        details: Additional error details
    """

    def __init__(
        self,
        error_type: ProcessingErrorType,
        message: str,
        file_path: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.error_type = error_type
        self.message = message
        self.file_path = file_path
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """String representation of error."""
        parts = [f"[{self.error_type.value}]", self.message]
        if self.file_path:
            parts.append(f"File: {self.file_path}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


class FileValidationError(ProcessingError):
    """Exception raised for file validation errors."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            ProcessingErrorType.VALIDATION_ERROR, message, file_path, details
        )


class SecurityError(ProcessingError):
    """Exception raised for security-related errors."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            ProcessingErrorType.SECURITY_ERROR, message, file_path, details
        )


@dataclass
class ValidationConfig:
    """
    Configuration for file validation.

    Attributes:
        max_file_size: Maximum file size in bytes (default: 100 MB)
        min_file_size: Minimum file size in bytes (default: 0 bytes)
        allowed_extensions: Set of allowed file extensions
        blocked_extensions: Set of blocked file extensions
        scan_for_malware: Whether to scan for malware patterns
        check_path_traversal: Whether to check for path traversal attacks
        max_path_length: Maximum allowed path length
        require_ascii_names: Whether to require ASCII-only filenames
    """

    max_file_size: int = 100 * 1024 * 1024  # 100 MB
    min_file_size: int = 0
    allowed_extensions: set[str] | None = None
    blocked_extensions: set[str] | None = None
    scan_for_malware: bool = True
    check_path_traversal: bool = True
    max_path_length: int = 4096
    require_ascii_names: bool = False

    def __post_init__(self) -> None:
        """Initialize default values."""
        if self.blocked_extensions is None:
            # Potentially dangerous extensions
            self.blocked_extensions = {
                ".exe",
                ".dll",
                ".so",
                ".dylib",
                ".bat",
                ".cmd",
                ".sh",
                ".ps1",
                ".vbs",
                ".js",
                ".jar",
                ".app",
                ".deb",
                ".rpm",
            }


class FileValidator:
    """
    Validates files before processing.

    Provides comprehensive validation including size checks,
    extension validation, security scanning, and path validation.
    """

    def __init__(self, config: ValidationConfig | None = None):
        """
        Initialize validator.

        Args:
            config: Validation configuration
        """
        self.config = config or ValidationConfig()

    def validate_file(self, file_path: str | Path) -> None:
        """
        Validate a file before processing.

        Args:
            file_path: Path to the file to validate

        Raises:
            FileValidationError: If validation fails
            SecurityError: If security checks fail

        Example:
            >>> validator = FileValidator()
            >>> validator.validate_file("document.pdf")  # OK
            >>> validator.validate_file("virus.exe")  # Raises SecurityError
        """
        file_path = Path(file_path)
        file_path_str = str(file_path)

        # Check if file exists
        if not file_path.exists():
            raise FileValidationError(
                f"File does not exist: {file_path_str}",
                file_path_str,
                {"exists": False},
            )

        # Check if it's a file (not a directory)
        if not file_path.is_file():
            raise FileValidationError(
                f"Path is not a file: {file_path_str}",
                file_path_str,
                {"is_file": False},
            )

        # Check file size
        self._validate_file_size(file_path)

        # Check file extension
        self._validate_extension(file_path)

        # Check for path traversal
        if self.config.check_path_traversal:
            self._check_path_traversal(file_path)

        # Check path length
        self._validate_path_length(file_path)

        # Check filename characters
        if self.config.require_ascii_names:
            self._validate_filename_chars(file_path)

        # Scan for malware patterns
        if self.config.scan_for_malware:
            self._scan_for_malware(file_path)

        logger.debug(f"File validation passed: {file_path_str}")

    def _validate_file_size(self, file_path: Path) -> None:
        """
        Validate file size.

        Args:
            file_path: Path to the file

        Raises:
            FileValidationError: If file size is invalid
        """
        file_size = file_path.stat().st_size

        if file_size < self.config.min_file_size:
            raise FileValidationError(
                f"File too small: {file_size} bytes "
                f"(minimum: {self.config.min_file_size} bytes)",
                str(file_path),
                {"size": file_size, "min_size": self.config.min_file_size},
            )

        if file_size > self.config.max_file_size:
            raise FileValidationError(
                f"File too large: {file_size} bytes "
                f"(maximum: {self.config.max_file_size} bytes)",
                str(file_path),
                {"size": file_size, "max_size": self.config.max_file_size},
            )

    def _validate_extension(self, file_path: Path) -> None:
        """
        Validate file extension.

        Args:
            file_path: Path to the file

        Raises:
            SecurityError: If extension is blocked
            FileValidationError: If extension is not allowed
        """
        extension = file_path.suffix.lower()

        # Check blocked extensions (security)
        if (
            self.config.blocked_extensions
            and extension in self.config.blocked_extensions
        ):
            raise SecurityError(
                f"Blocked file extension: {extension}",
                str(file_path),
                {"extension": extension, "reason": "security_risk"},
            )

        # Check allowed extensions (if specified)
        if (
            self.config.allowed_extensions is not None
            and extension not in self.config.allowed_extensions
        ):
            raise FileValidationError(
                f"File extension not allowed: {extension}",
                str(file_path),
                {
                    "extension": extension,
                    "allowed": list(self.config.allowed_extensions),
                },
            )

    def _check_path_traversal(self, file_path: Path) -> None:
        """
        Check for path traversal attacks.

        Args:
            file_path: Path to check

        Raises:
            SecurityError: If path traversal detected
        """
        # Resolve to absolute path
        try:
            file_path.resolve()
        except (OSError, RuntimeError) as e:
            raise SecurityError(
                f"Failed to resolve path: {e}",
                str(file_path),
                {"error": str(e)},
            ) from e

        # Check for suspicious patterns
        path_str = str(file_path)
        suspicious_patterns = ["../", "..\\", "..", "%2e%2e", "%252e%252e"]

        for pattern in suspicious_patterns:
            if pattern in path_str:
                raise SecurityError(
                    f"Path traversal attempt detected: {pattern}",
                    str(file_path),
                    {"pattern": pattern, "path": path_str},
                )

    def _validate_path_length(self, file_path: Path) -> None:
        """
        Validate path length.

        Args:
            file_path: Path to validate

        Raises:
            FileValidationError: If path is too long
        """
        path_str = str(file_path.resolve())
        if len(path_str) > self.config.max_path_length:
            raise FileValidationError(
                f"Path too long: {len(path_str)} characters "
                f"(maximum: {self.config.max_path_length})",
                path_str,
                {"length": len(path_str), "max_length": self.config.max_path_length},
            )

    def _validate_filename_chars(self, file_path: Path) -> None:
        """
        Validate filename contains only ASCII characters.

        Args:
            file_path: Path to validate

        Raises:
            FileValidationError: If filename contains non-ASCII chars
        """
        filename = file_path.name
        if not filename.isascii():
            raise FileValidationError(
                f"Filename contains non-ASCII characters: {filename}",
                str(file_path),
                {"filename": filename},
            )

    def _scan_for_malware(self, file_path: Path) -> None:
        """
        Scan file for malware patterns.

        This is a basic check - for production, integrate with
        actual antivirus/malware scanning tools.

        Args:
            file_path: Path to scan

        Raises:
            SecurityError: If malware patterns detected
        """
        # Check file signature (magic bytes)
        try:
            with open(file_path, "rb") as f:
                header = f.read(512)  # Read first 512 bytes

            # Check for executable signatures
            executable_signatures = [
                b"MZ",  # DOS/Windows executable
                b"\x7fELF",  # Linux executable
                b"\xca\xfe\xba\xbe",  # macOS Mach-O
                b"\xfe\xed\xfa",  # macOS Mach-O
            ]

            for sig in executable_signatures:
                if header.startswith(sig):
                    raise SecurityError(
                        f"Executable file detected: {file_path.suffix}",
                        str(file_path),
                        {"signature": sig.hex(), "reason": "executable_content"},
                    )

        except (OSError, PermissionError) as e:
            logger.warning(f"Could not scan file for malware: {e}")


class ErrorHandler:
    """
    Centralized error handling for processors.

    Provides context-aware error handling, logging,
    and error recovery strategies.
    """

    def __init__(self, log_errors: bool = True, raise_on_error: bool = True):
        """
        Initialize error handler.

        Args:
            log_errors: Whether to log errors
            raise_on_error: Whether to raise exceptions or return None
        """
        self.log_errors = log_errors
        self.raise_on_error = raise_on_error
        self.error_count = 0
        self.last_error: ProcessingError | None = None

    def handle_error(
        self,
        error: Exception,
        file_path: str | None = None,
        error_type: ProcessingErrorType | None = None,
    ) -> None:
        """
        Handle an error during processing.

        Args:
            error: The exception that occurred
            file_path: Path to the file being processed
            error_type: Type of processing error

        Raises:
            ProcessingError: If raise_on_error is True
        """
        self.error_count += 1

        # Convert to ProcessingError if needed
        if isinstance(error, ProcessingError):
            proc_error = error
        else:
            # Determine error type from exception
            if error_type is None:
                error_type = self._classify_error(error)

            proc_error = ProcessingError(
                error_type=error_type,
                message=str(error),
                file_path=file_path,
                details={"original_error": type(error).__name__},
            )

        self.last_error = proc_error

        # Log error
        if self.log_errors:
            logger.error(f"Processing error: {proc_error}")

        # Raise or return
        if self.raise_on_error:
            raise proc_error

    def _classify_error(self, error: Exception) -> ProcessingErrorType:
        """
        Classify an exception into a ProcessingErrorType.

        Args:
            error: The exception to classify

        Returns:
            Appropriate ProcessingErrorType
        """
        if isinstance(error, FileNotFoundError):
            return ProcessingErrorType.FILE_NOT_FOUND
        elif isinstance(error, PermissionError):
            return ProcessingErrorType.PERMISSION_DENIED
        elif isinstance(error, MemoryError):
            return ProcessingErrorType.MEMORY_ERROR
        elif isinstance(error, TimeoutError):
            return ProcessingErrorType.TIMEOUT_ERROR
        elif "corrupt" in str(error).lower() or "invalid" in str(error).lower():
            return ProcessingErrorType.FILE_CORRUPTED
        else:
            return ProcessingErrorType.PROCESSING_ERROR

    def reset(self) -> None:
        """Reset error statistics."""
        self.error_count = 0
        self.last_error = None


def create_default_validator() -> FileValidator:
    """
    Create a validator with default configuration.

    Returns:
        FileValidator with default settings
    """
    return FileValidator(ValidationConfig())


def validate_file_path(
    file_path: str | Path, validator: FileValidator | None = None
) -> None:
    """
    Convenience function to validate a file path.

    Args:
        file_path: Path to validate
        validator: Optional custom validator

    Raises:
        FileValidationError: If validation fails
        SecurityError: If security checks fail

    Example:
        >>> validate_file_path("document.pdf")  # OK
        >>> validate_file_path("virus.exe")  # Raises SecurityError
    """
    if validator is None:
        validator = create_default_validator()

    validator.validate_file(file_path)
