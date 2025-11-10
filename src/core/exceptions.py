"""
Exception Handling

This module defines custom exceptions for the RAG Backend application
and provides centralized error handling functionality.
"""

from typing import Any, Dict, Optional


class RAGBackendException(Exception):
    """Base exception for all RAG Backend errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class ProcessingException(RAGBackendException):
    """Exception raised during document processing."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        processor_type: Optional[str] = None,
        **kwargs
    ):
        details = {
            "file_path": file_path,
            "processor_type": processor_type,
            **kwargs
        }
        super().__init__(message, "PROCESSING_ERROR", details)


class UnsupportedFormatException(ProcessingException):
    """Exception raised when file format is not supported."""
    
    def __init__(self, file_path: str, file_type: str):
        message = f"Unsupported file format: {file_type}"
        super().__init__(
            message,
            file_path=file_path,
            error_code="UNSUPPORTED_FORMAT"
        )


class FileNotFoundError(ProcessingException):
    """Exception raised when file cannot be found."""
    
    def __init__(self, file_path: str):
        message = f"File not found: {file_path}"
        super().__init__(
            message,
            file_path=file_path,
            error_code="FILE_NOT_FOUND"
        )


class FileTooLargeError(ProcessingException):
    """Exception raised when file exceeds size limits."""
    
    def __init__(self, file_path: str, file_size: int, max_size: int):
        message = f"File too large: {file_size} bytes (max: {max_size} bytes)"
        super().__init__(
            message,
            file_path=file_path,
            file_size=file_size,
            max_size=max_size,
            error_code="FILE_TOO_LARGE"
        )


class CorruptedFileError(ProcessingException):
    """Exception raised when file is corrupted or invalid."""
    
    def __init__(self, file_path: str, reason: str):
        message = f"Corrupted file: {reason}"
        super().__init__(
            message,
            file_path=file_path,
            reason=reason,
            error_code="CORRUPTED_FILE"
        )


class EmbeddingException(RAGBackendException):
    """Exception raised during embedding generation."""
    
    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        text_length: Optional[int] = None,
        **kwargs
    ):
        details = {
            "model_name": model_name,
            "text_length": text_length,
            **kwargs
        }
        super().__init__(message, "EMBEDDING_ERROR", details)


class VectorStoreException(RAGBackendException):
    """Exception raised during vector store operations."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table_name: Optional[str] = None,
        **kwargs
    ):
        details = {
            "operation": operation,
            "table_name": table_name,
            **kwargs
        }
        super().__init__(message, "VECTOR_STORE_ERROR", details)


class QueryProcessingException(RAGBackendException):
    """Exception raised during query processing."""
    
    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        stage: Optional[str] = None,
        **kwargs
    ):
        details = {
            "query": query,
            "stage": stage,
            **kwargs
        }
        super().__init__(message, "QUERY_PROCESSING_ERROR", details)


class LLMException(RAGBackendException):
    """Exception raised during LLM operations."""
    
    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        endpoint: Optional[str] = None,
        **kwargs
    ):
        details = {
            "model_name": model_name,
            "endpoint": endpoint,
            **kwargs
        }
        super().__init__(message, "LLM_ERROR", details)


class ConfigurationException(RAGBackendException):
    """Exception raised for configuration errors."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        **kwargs
    ):
        details = {
            "config_key": config_key,
            "config_value": config_value,
            **kwargs
        }
        super().__init__(message, "CONFIGURATION_ERROR", details)


class ValidationException(RAGBackendException):
    """Exception raised for validation errors."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        details = {
            "field": field,
            "value": value,
            **kwargs
        }
        super().__init__(message, "VALIDATION_ERROR", details)


class AuthenticationException(RAGBackendException):
    """Exception raised for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationException(RAGBackendException):
    """Exception raised for authorization errors."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class RateLimitException(RAGBackendException):
    """Exception raised when rate limits are exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: Optional[int] = None,
        window: Optional[int] = None,
        **kwargs
    ):
        details = {
            "limit": limit,
            "window": window,
            **kwargs
        }
        super().__init__(message, "RATE_LIMIT_ERROR", details)


def handle_exception(exception: Exception) -> Dict[str, Any]:
    """
    Handle exceptions and return standardized error response.
    
    Args:
        exception: Exception to handle
    
    Returns:
        Standardized error response dictionary
    """
    if isinstance(exception, RAGBackendException):
        return {
            "error": True,
            "error_code": exception.error_code,
            "message": exception.message,
            "details": exception.details
        }
    else:
        return {
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": {
                "exception_type": type(exception).__name__,
                "exception_message": str(exception)
            }
        }