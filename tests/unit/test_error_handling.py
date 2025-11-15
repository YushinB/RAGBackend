"""
Tests for error handling and validation (T5.2).

Tests comprehensive error handling, file validation,
and security features.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.processors.error_handling import (
    ErrorHandler,
    FileValidationError,
    FileValidator,
    ProcessingError,
    ProcessingErrorType,
    SecurityError,
    ValidationConfig,
    create_default_validator,
    validate_file_path,
)


class TestProcessingError:
    """Tests for ProcessingError exception."""

    def test_initialization(self):
        """Test error initialization."""
        error = ProcessingError(
            error_type=ProcessingErrorType.FILE_NOT_FOUND,
            message="File not found",
            file_path="test.pdf",
            details={"extra": "info"},
        )

        assert error.error_type == ProcessingErrorType.FILE_NOT_FOUND
        assert error.message == "File not found"
        assert error.file_path == "test.pdf"
        assert error.details == {"extra": "info"}

    def test_string_representation(self):
        """Test error string representation."""
        error = ProcessingError(
            ProcessingErrorType.FILE_CORRUPTED,
            "Corrupted file",
            "document.pdf",
            {"reason": "invalid header"},
        )

        error_str = str(error)
        assert "[file_corrupted]" in error_str
        assert "Corrupted file" in error_str
        assert "document.pdf" in error_str
        assert "invalid header" in error_str


class TestFileValidationError:
    """Tests for FileValidationError."""

    def test_initialization(self):
        """Test validation error initialization."""
        error = FileValidationError("Invalid file", "test.pdf", {"size": 0})

        assert error.error_type == ProcessingErrorType.VALIDATION_ERROR
        assert "Invalid file" in str(error)


class TestSecurityError:
    """Tests for SecurityError."""

    def test_initialization(self):
        """Test security error initialization."""
        error = SecurityError(
            "Malware detected", "virus.exe", {"signature": "malicious"}
        )

        assert error.error_type == ProcessingErrorType.SECURITY_ERROR
        assert "Malware detected" in str(error)


class TestValidationConfig:
    """Tests for ValidationConfig."""

    def test_default_configuration(self):
        """Test default validation configuration."""
        config = ValidationConfig()

        assert config.max_file_size == 100 * 1024 * 1024  # 100 MB
        assert config.min_file_size == 0
        assert config.allowed_extensions is None
        assert config.scan_for_malware is True
        assert config.check_path_traversal is True
        assert ".exe" in config.blocked_extensions
        assert ".sh" in config.blocked_extensions

    def test_custom_configuration(self):
        """Test custom validation configuration."""
        config = ValidationConfig(
            max_file_size=50 * 1024 * 1024,  # 50 MB
            min_file_size=1024,  # 1 KB
            allowed_extensions={".pdf", ".docx"},
            scan_for_malware=False,
        )

        assert config.max_file_size == 50 * 1024 * 1024
        assert config.min_file_size == 1024
        assert config.allowed_extensions == {".pdf", ".docx"}
        assert config.scan_for_malware is False


class TestFileValidator:
    """Tests for FileValidator."""

    def test_initialization(self):
        """Test validator initialization."""
        validator = FileValidator()
        assert validator.config is not None

        custom_config = ValidationConfig(max_file_size=1024)
        validator = FileValidator(custom_config)
        assert validator.config.max_file_size == 1024

    def test_validate_nonexistent_file(self):
        """Test validation of nonexistent file."""
        validator = FileValidator()

        with pytest.raises(FileValidationError) as exc_info:
            validator.validate_file("nonexistent.pdf")

        assert "does not exist" in str(exc_info.value)

    def test_validate_directory_not_file(self):
        """Test validation rejects directories."""
        validator = FileValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileValidationError) as exc_info:
                validator.validate_file(tmpdir)

            assert "not a file" in str(exc_info.value)

    def test_validate_file_too_small(self):
        """Test validation of file too small."""
        config = ValidationConfig(min_file_size=1024)  # 1 KB minimum
        validator = FileValidator(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("small")  # Less than 1 KB
            temp_path = f.name

        try:
            with pytest.raises(FileValidationError) as exc_info:
                validator.validate_file(temp_path)

            assert "too small" in str(exc_info.value).lower()
        finally:
            Path(temp_path).unlink()

    def test_validate_file_too_large(self):
        """Test validation of file too large."""
        config = ValidationConfig(max_file_size=100)  # 100 bytes maximum
        validator = FileValidator(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("x" * 200)  # More than 100 bytes
            temp_path = f.name

        try:
            with pytest.raises(FileValidationError) as exc_info:
                validator.validate_file(temp_path)

            assert "too large" in str(exc_info.value).lower()
        finally:
            Path(temp_path).unlink()

    def test_validate_blocked_extension(self):
        """Test validation of blocked file extensions."""
        validator = FileValidator()

        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(SecurityError) as exc_info:
                validator.validate_file(temp_path)

            assert "blocked" in str(exc_info.value).lower()
        finally:
            Path(temp_path).unlink()

    def test_validate_allowed_extension(self):
        """Test validation with allowed extensions."""
        config = ValidationConfig(allowed_extensions={".pdf", ".docx"})
        validator = FileValidator(config)

        # Create valid file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"PDF content")
            pdf_path = f.name

        # Create file with disallowed extension
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"Text content")
            txt_path = f.name

        try:
            # PDF should pass
            validator.validate_file(pdf_path)

            # TXT should fail
            with pytest.raises(FileValidationError) as exc_info:
                validator.validate_file(txt_path)

            assert "not allowed" in str(exc_info.value).lower()
        finally:
            Path(pdf_path).unlink()
            Path(txt_path).unlink()

    def test_validate_path_traversal(self):
        """Test detection of path traversal attempts."""
        validator = FileValidator()

        # Test various path traversal patterns
        traversal_paths = [
            "../etc/passwd",
            "..\\windows\\system32",
            "dir/../../etc/passwd",
        ]

        for path in traversal_paths:
            # These won't exist, but should be caught by traversal check
            # Mock exists(), is_file(), and stat() for this test
            with (
                patch.object(Path, "exists", return_value=True),
                patch.object(Path, "is_file", return_value=True),
            ):
                # Mock stat() to return a valid stat result
                mock_stat = MagicMock()
                mock_stat.st_size = 1000
                with (
                    patch.object(Path, "stat", return_value=mock_stat),
                    pytest.raises(SecurityError) as exc_info,
                ):
                    validator.validate_file(path)

                assert "traversal" in str(exc_info.value).lower()

    def test_validate_path_length(self):
        """Test validation of path length."""
        config = ValidationConfig(max_path_length=50)
        validator = FileValidator(config)

        # Create file with very long path
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"content")
            temp_path = f.name

        try:
            # Path should be rejected if it's longer than max_path_length
            # Get actual path length after resolution
            resolved_length = len(str(Path(temp_path).resolve()))

            if resolved_length > config.max_path_length:
                with pytest.raises(FileValidationError) as exc_info:
                    validator.validate_file(temp_path)

                assert "too long" in str(exc_info.value).lower()
        finally:
            Path(temp_path).unlink()

    def test_validate_ascii_filename(self):
        """Test validation of ASCII-only filenames."""
        config = ValidationConfig(require_ascii_names=True)
        validator = FileValidator(config)

        # Test with non-ASCII characters (if filesystem supports it)
        try:
            with tempfile.NamedTemporaryFile(
                suffix="файл.txt", mode="w", delete=False
            ) as f:
                f.write("content")
                temp_path = f.name

            with pytest.raises(FileValidationError) as exc_info:
                validator.validate_file(temp_path)

            assert "non-ascii" in str(exc_info.value).lower()

            Path(temp_path).unlink()
        except (OSError, UnicodeError):
            # Skip test if filesystem doesn't support non-ASCII names
            pytest.skip("Filesystem doesn't support non-ASCII filenames")

    def test_validate_malware_scan_executable(self):
        """Test malware scanning detects executables."""
        validator = FileValidator()

        # Create file with executable signature (MZ header)
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
            f.write(b"MZ" + b"\x00" * 100)  # DOS/Windows executable signature
            temp_path = f.name

        try:
            with pytest.raises(SecurityError) as exc_info:
                validator.validate_file(temp_path)

            assert "executable" in str(exc_info.value).lower()
        finally:
            Path(temp_path).unlink()

    def test_validate_malware_scan_elf(self):
        """Test malware scanning detects ELF binaries."""
        validator = FileValidator()

        # Create file with ELF signature
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
            f.write(b"\x7fELF" + b"\x00" * 100)  # Linux executable signature
            temp_path = f.name

        try:
            with pytest.raises(SecurityError) as exc_info:
                validator.validate_file(temp_path)

            assert "executable" in str(exc_info.value).lower()
        finally:
            Path(temp_path).unlink()

    def test_validate_malware_scan_disabled(self):
        """Test validation with malware scanning disabled."""
        config = ValidationConfig(scan_for_malware=False)
        validator = FileValidator(config)

        # Create file with executable signature
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
            f.write(b"MZ" + b"\x00" * 100)
            temp_path = f.name

        try:
            # Should not raise SecurityError
            validator.validate_file(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_validate_valid_file(self):
        """Test validation of valid file."""
        validator = FileValidator()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Valid file content\n" * 100)
            temp_path = f.name

        try:
            # Should not raise any exception
            validator.validate_file(temp_path)
        finally:
            Path(temp_path).unlink()


class TestErrorHandler:
    """Tests for ErrorHandler."""

    def test_initialization(self):
        """Test error handler initialization."""
        handler = ErrorHandler(log_errors=True, raise_on_error=True)

        assert handler.log_errors is True
        assert handler.raise_on_error is True
        assert handler.error_count == 0
        assert handler.last_error is None

    def test_handle_processing_error(self):
        """Test handling ProcessingError."""
        handler = ErrorHandler()

        error = ProcessingError(
            ProcessingErrorType.FILE_CORRUPTED,
            "Corrupted file",
            "test.pdf",
        )

        with pytest.raises(ProcessingError):
            handler.handle_error(error, "test.pdf")

        assert handler.error_count == 1
        assert handler.last_error == error

    def test_handle_standard_exception(self):
        """Test handling standard exceptions."""
        handler = ErrorHandler()

        with pytest.raises(ProcessingError) as exc_info:
            handler.handle_error(ValueError("Invalid value"), "test.pdf")

        assert handler.error_count == 1
        assert "Invalid value" in str(exc_info.value)

    def test_classify_file_not_found(self):
        """Test error classification for FileNotFoundError."""
        handler = ErrorHandler()

        with pytest.raises(ProcessingError) as exc_info:
            handler.handle_error(FileNotFoundError("Missing file"), "test.pdf")

        error = exc_info.value
        assert error.error_type == ProcessingErrorType.FILE_NOT_FOUND

    def test_classify_permission_error(self):
        """Test error classification for PermissionError."""
        handler = ErrorHandler()

        with pytest.raises(ProcessingError) as exc_info:
            handler.handle_error(PermissionError("Access denied"), "test.pdf")

        error = exc_info.value
        assert error.error_type == ProcessingErrorType.PERMISSION_DENIED

    def test_classify_memory_error(self):
        """Test error classification for MemoryError."""
        handler = ErrorHandler()

        with pytest.raises(ProcessingError) as exc_info:
            handler.handle_error(MemoryError("Out of memory"), "test.pdf")

        error = exc_info.value
        assert error.error_type == ProcessingErrorType.MEMORY_ERROR

    def test_classify_timeout_error(self):
        """Test error classification for TimeoutError."""
        handler = ErrorHandler()

        with pytest.raises(ProcessingError) as exc_info:
            handler.handle_error(TimeoutError("Operation timed out"), "test.pdf")

        error = exc_info.value
        assert error.error_type == ProcessingErrorType.TIMEOUT_ERROR

    def test_classify_corrupted_file(self):
        """Test error classification for corrupted files."""
        handler = ErrorHandler()

        with pytest.raises(ProcessingError) as exc_info:
            handler.handle_error(ValueError("File is corrupt or invalid"), "test.pdf")

        error = exc_info.value
        assert error.error_type == ProcessingErrorType.FILE_CORRUPTED

    def test_no_raise_on_error(self):
        """Test error handler that doesn't raise."""
        handler = ErrorHandler(raise_on_error=False)

        # Should not raise
        handler.handle_error(ValueError("Some error"), "test.pdf")

        assert handler.error_count == 1
        assert handler.last_error is not None

    def test_reset(self):
        """Test resetting error statistics."""
        handler = ErrorHandler(raise_on_error=False)

        handler.handle_error(ValueError("Error 1"), "test1.pdf")
        handler.handle_error(ValueError("Error 2"), "test2.pdf")

        assert handler.error_count == 2

        handler.reset()

        assert handler.error_count == 0
        assert handler.last_error is None


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_default_validator(self):
        """Test creating default validator."""
        validator = create_default_validator()

        assert isinstance(validator, FileValidator)
        assert validator.config.max_file_size == 100 * 1024 * 1024

    def test_validate_file_path_valid(self):
        """Test validate_file_path with valid file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Valid content")
            temp_path = f.name

        try:
            # Should not raise
            validate_file_path(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_validate_file_path_invalid(self):
        """Test validate_file_path with invalid file."""
        with pytest.raises(FileValidationError):
            validate_file_path("nonexistent.pdf")

    def test_validate_file_path_custom_validator(self):
        """Test validate_file_path with custom validator."""
        config = ValidationConfig(max_file_size=10)  # 10 bytes max
        validator = FileValidator(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is too long!")
            temp_path = f.name

        try:
            with pytest.raises(FileValidationError):
                validate_file_path(temp_path, validator)
        finally:
            Path(temp_path).unlink()


class TestIntegration:
    """Integration tests for error handling."""

    def test_full_validation_pipeline(self):
        """Test complete validation pipeline."""
        # Create validator with specific configuration
        config = ValidationConfig(
            max_file_size=1024 * 1024,  # 1 MB
            min_file_size=10,
            allowed_extensions={".txt", ".pdf"},
            scan_for_malware=True,
            check_path_traversal=True,
        )
        validator = FileValidator(config)

        # Create valid file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Valid content\n" * 10)
            temp_path = f.name

        try:
            # Should pass all validations
            validator.validate_file(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_multiple_validation_failures(self):
        """Test handling multiple validation failures."""
        config = ValidationConfig(
            max_file_size=100,
            allowed_extensions={".pdf"},
        )
        validator = FileValidator(config)

        # File with wrong extension and too large
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("x" * 200)
            temp_path = f.name

        try:
            # First validation error should be caught (extension)
            with pytest.raises(FileValidationError):
                validator.validate_file(temp_path)
        finally:
            Path(temp_path).unlink()
