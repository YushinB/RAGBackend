"""
Processor Factory for automatic file type detection and processor selection.

This module implements T5.1.1 and T5.1.2:
- File type detection based on extension and content
- Processor selection and instantiation
- Configuration parameter passing
- Processor registry and plugin system
- Error handling and validation (T5.2)
"""

import logging
import mimetypes
from pathlib import Path
from typing import Any, Protocol

from src.models.base_models import MultiModalContent
from src.processors.base import DataProcessor
from src.processors.error_handling import (
    ErrorHandler,
    FileValidator,
    ProcessingErrorType,
)
from src.processors.excel_processor import ExcelProcessor
from src.processors.markdown_processor import MarkdownProcessor
from src.processors.pdf_processor import PDFProcessor
from src.processors.text_processor import TextFileProcessor
from src.processors.word_processor import WordProcessor

# Configure logger
logger = logging.getLogger(__name__)


class ProcessorProtocol(Protocol):
    """Protocol defining the interface for document processors."""

    def can_process(self, file_path: str) -> bool:
        """Check if processor can handle the file."""
        ...

    def process(self, file_path: str, **kwargs: Any) -> MultiModalContent:
        """Process the file and return multi-modal content."""
        ...


class ProcessorRegistry:
    """
    Registry for document processors with plugin support.

    Allows dynamic registration of processors for extensibility.
    Implements T5.1.2 plugin system.
    """

    def __init__(self):
        """Initialize the processor registry."""
        self._processors: dict[str, type[DataProcessor]] = {}
        self._extension_map: dict[str, str] = {}
        self._mime_type_map: dict[str, str] = {}

        # Register default processors
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default built-in processors."""
        # PDF Processor
        self.register_processor(
            name="pdf",
            processor_class=PDFProcessor,
            extensions=[".pdf"],
            mime_types=["application/pdf"],
        )

        # Word Processor
        self.register_processor(
            name="word",
            processor_class=WordProcessor,
            extensions=[".docx", ".doc"],
            mime_types=[
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
            ],
        )

        # Excel Processor
        self.register_processor(
            name="excel",
            processor_class=ExcelProcessor,
            extensions=[".xlsx", ".xls"],
            mime_types=[
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel",
            ],
        )

        # Markdown Processor
        self.register_processor(
            name="markdown",
            processor_class=MarkdownProcessor,
            extensions=[".md", ".markdown"],
            mime_types=["text/markdown", "text/x-markdown"],
        )

        # Text Processor
        self.register_processor(
            name="text",
            processor_class=TextFileProcessor,
            extensions=[".txt", ".text", ".log", ".csv", ".json", ".xml", ".html"],
            mime_types=["text/plain", "text/csv", "application/json", "text/html"],
        )

    def register_processor(
        self,
        name: str,
        processor_class: type[DataProcessor],
        extensions: list[str],
        mime_types: list[str] | None = None,
    ) -> None:
        """
        Register a processor with the factory.

        Args:
            name: Unique name for the processor
            processor_class: Processor class to instantiate
            extensions: List of file extensions (e.g., ['.pdf', '.doc'])
            mime_types: Optional list of MIME types
        """
        if name in self._processors:
            raise ValueError(f"Processor '{name}' is already registered")

        self._processors[name] = processor_class

        # Map extensions to processor name
        for ext in extensions:
            ext = ext.lower()
            if not ext.startswith("."):
                ext = f".{ext}"
            self._extension_map[ext] = name

        # Map MIME types to processor name
        if mime_types:
            for mime_type in mime_types:
                self._mime_type_map[mime_type.lower()] = name

    def unregister_processor(self, name: str) -> None:
        """
        Unregister a processor from the factory.

        Args:
            name: Name of the processor to unregister
        """
        if name not in self._processors:
            raise ValueError(f"Processor '{name}' is not registered")

        # Remove from processors
        del self._processors[name]

        # Remove from extension map
        self._extension_map = {
            ext: proc for ext, proc in self._extension_map.items() if proc != name
        }

        # Remove from MIME type map
        self._mime_type_map = {
            mime: proc for mime, proc in self._mime_type_map.items() if proc != name
        }

    def get_processor_by_name(self, name: str) -> type[DataProcessor] | None:
        """
        Get processor class by name.

        Args:
            name: Name of the processor

        Returns:
            Processor class or None if not found
        """
        return self._processors.get(name)

    def get_processor_by_extension(self, extension: str) -> type[DataProcessor] | None:
        """
        Get processor class by file extension.

        Args:
            extension: File extension (e.g., '.pdf')

        Returns:
            Processor class or None if not found
        """
        extension = extension.lower()
        if not extension.startswith("."):
            extension = f".{extension}"

        processor_name = self._extension_map.get(extension)
        if processor_name:
            return self._processors.get(processor_name)
        return None

    def get_processor_by_mime_type(self, mime_type: str) -> type[DataProcessor] | None:
        """
        Get processor class by MIME type.

        Args:
            mime_type: MIME type (e.g., 'application/pdf')

        Returns:
            Processor class or None if not found
        """
        processor_name = self._mime_type_map.get(mime_type.lower())
        if processor_name:
            return self._processors.get(processor_name)
        return None

    def list_registered_processors(self) -> list[str]:
        """
        Get list of registered processor names.

        Returns:
            List of processor names
        """
        return list(self._processors.keys())

    def list_supported_extensions(self) -> list[str]:
        """
        Get list of all supported file extensions.

        Returns:
            List of extensions
        """
        return list(self._extension_map.keys())


class ProcessorFactory:
    """
    Factory for creating appropriate document processors.

    Implements T5.1.1:
    - File type detection logic
    - Processor selection and instantiation
    - Configuration parameter passing
    """

    def __init__(
        self,
        registry: ProcessorRegistry | None = None,
        validator: FileValidator | None = None,
        error_handler: ErrorHandler | None = None,
        enable_validation: bool = True,
    ):
        """
        Initialize the processor factory.

        Args:
            registry: Optional custom processor registry
            validator: Optional custom file validator
            error_handler: Optional custom error handler
            enable_validation: Whether to enable file validation (default: True)
        """
        self.registry = registry or ProcessorRegistry()
        self.validator = validator or FileValidator()
        self.error_handler = error_handler or ErrorHandler()
        self.enable_validation = enable_validation

        # Initialize mimetypes
        mimetypes.init()

        logger.debug("ProcessorFactory initialized")

    def detect_file_type(self, file_path: str) -> tuple[str | None, str | None]:
        """
        Detect file type from path and content.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (extension, mime_type)
        """
        path = Path(file_path)

        # Get extension
        extension = path.suffix.lower() if path.suffix else None

        # Guess MIME type
        mime_type, _ = mimetypes.guess_type(file_path)

        return extension, mime_type

    def get_processor_for_file(
        self, file_path: str, **config: Any
    ) -> DataProcessor | None:
        """
        Get appropriate processor for a file.

        Args:
            file_path: Path to the file
            **config: Configuration parameters to pass to processor

        Returns:
            Instantiated processor or None if no suitable processor found
        """
        # Detect file type
        extension, mime_type = self.detect_file_type(file_path)

        # Try to get processor by extension first
        processor_class = None
        if extension:
            processor_class = self.registry.get_processor_by_extension(extension)

        # Try MIME type if extension didn't work
        if not processor_class and mime_type:
            processor_class = self.registry.get_processor_by_mime_type(mime_type)

        # Instantiate processor if found
        if processor_class:
            return processor_class(**config)

        return None

    def process_file(self, file_path: str, **config: Any) -> MultiModalContent:
        """
        Automatically process a file with the appropriate processor.

        Includes comprehensive validation and error handling (T5.2).

        Args:
            file_path: Path to the file
            **config: Configuration parameters

        Returns:
            MultiModalContent from processing

        Raises:
            FileValidationError: If file validation fails
            SecurityError: If security checks fail
            ProcessingError: If processing fails-
            ValueError: If no suitable processor found
            FileNotFoundError: If file doesn't- exist
        """
        logger.info(f"Processing file: {file_path}")

        try:
            # Validate file if enabled
            if self.enable_validation:
                self.validator.validate_file(file_path)
                logger.debug(f"File validation passed: {file_path}")

            # Check file exists (redundant with validation, but explicit)
            if not Path(file_path).exists():
                self.error_handler.handle_error(
                    FileNotFoundError(f"File not found: {file_path}"),
                    file_path,
                    ProcessingErrorType.FILE_NOT_FOUND,
                )

            # Get processor
            processor = self.get_processor_for_file(file_path, **config)

            if not processor:
                extension, mime_type = self.detect_file_type(file_path)
                error_msg = (
                    f"No processor found for file: {file_path} "
                    f"(extension: {extension}, mime_type: {mime_type})"
                )
                self.error_handler.handle_error(
                    ValueError(error_msg),
                    file_path,
                    ProcessingErrorType.UNSUPPORTED_FORMAT,
                )

            # Verify processor can handle the file
            if not processor.can_process(file_path):
                error_msg = f"Processor cannot handle file: {file_path}"
                self.error_handler.handle_error(
                    ValueError(error_msg),
                    file_path,
                    ProcessingErrorType.UNSUPPORTED_FORMAT,
                )

            # Process the file
            logger.debug(f"Processing with {processor.__class__.__name__}")
            
            # Generate document ID from filename
            document_id = str(Path(file_path).stem)
            
            # Check if processor has extract_multimodal_content method (for PDF, Word, Excel)
            if hasattr(processor, 'extract_multimodal_content'):
                logger.debug(f"Using extract_multimodal_content for {processor.__class__.__name__}")
                content = processor.extract_multimodal_content(file_path, document_id)
            else:
                # Fallback: Extract text only (for simple processors like Text, Markdown)
                logger.debug(f"Using extract_text fallback for {processor.__class__.__name__}")
                text = processor.extract_text(file_path)
                
                # Create a TextChunk with the extracted text
                from src.models.base_models import TextChunk, ChunkType
                text_chunk = TextChunk(
                    chunk_id=f"{document_id}_chunk_0",
                    text=text,
                    chunk_type=ChunkType.PARAGRAPH,
                    position=0,
                    metadata={"source": str(file_path)}
                )
                
                # Create MultiModalContent with the text chunk
                content = MultiModalContent(
                    document_id=document_id,
                    metadata={"processor": processor.__class__.__name__, "source_file": str(file_path)}
                )
                content.add_text_chunk(text_chunk)
            
            logger.info(f"Successfully processed: {file_path}")
            return content

        except Exception as e:
            # Handle any processing errors
            self.error_handler.handle_error(e, file_path)
            # If we get here, error handler didn't raise (shouldn't happen with default config)
            raise

    def can_process(self, file_path: str) -> bool:
        """
        Check if a file can be processed.

        Args:
            file_path: Path to the file

        Returns:
            True if file can be processed, False otherwise
        """
        processor = self.get_processor_for_file(file_path)
        if not processor:
            return False

        return processor.can_process(file_path)

    def get_supported_extensions(self) -> list[str]:
        """
        Get list of all supported file extensions.

        Returns:
            List of supported extensions
        """
        return self.registry.list_supported_extensions()

    def get_supported_processors(self) -> list[str]:
        """
        Get list of all registered processors.

        Returns:
            List of processor names
        """
        return self.registry.list_registered_processors()

    def register_custom_processor(
        self,
        name: str,
        processor_class: type[DataProcessor],
        extensions: list[str],
        mime_types: list[str] | None = None,
    ) -> None:
        """
        Register a custom processor.

        Args:
            name: Unique name for the processor
            processor_class: Processor class
            extensions: Supported file extensions
            mime_types: Optional supported MIME types
        """
        self.registry.register_processor(name, processor_class, extensions, mime_types)


class ProcessorFactoryBuilder:
    """
    Builder for creating configured ProcessorFactory instances.

    Provides fluent interface for factory configuration.
    """

    def __init__(self):
        """Initialize the builder."""
        self._registry: ProcessorRegistry | None = None
        self._validator: FileValidator | None = None
        self._error_handler: ErrorHandler | None = None
        self._enable_validation: bool = True
        self._custom_processors: list[
            tuple[str, type[DataProcessor], list[str], list[str] | None]
        ] = []

    def with_custom_registry(
        self, registry: ProcessorRegistry
    ) -> "ProcessorFactoryBuilder":
        """
        Use a custom processor registry.

        Args:
            registry: Custom registry

        Returns:
            Self for chaining
        """
        self._registry = registry
        return self

    def with_validator(self, validator: FileValidator) -> "ProcessorFactoryBuilder":
        """
        Use a custom file validator.

        Args:
            validator: Custom validator

        Returns:
            Self for chaining
        """
        self._validator = validator
        return self

    def with_error_handler(
        self, error_handler: ErrorHandler
    ) -> "ProcessorFactoryBuilder":
        """
        Use a custom error handler.

        Args:
            error_handler: Custom error handler

        Returns:
            Self for chaining
        """
        self._error_handler = error_handler
        return self

    def with_validation(self, enable: bool) -> "ProcessorFactoryBuilder":
        """
        Enable or disable file validation.

        Args:
            enable: Whether to enable validation

        Returns:
            Self for chaining
        """
        self._enable_validation = enable
        return self

    def with_processor(
        self,
        name: str,
        processor_class: type[DataProcessor],
        extensions: list[str],
        mime_types: list[str] | None = None,
    ) -> "ProcessorFactoryBuilder":
        """
        Add a custom processor to the factory.

        Args:
            name: Processor name
            processor_class: Processor class
            extensions: Supported extensions
            mime_types: Optional MIME types

        Returns:
            Self for chaining
        """
        self._custom_processors.append((name, processor_class, extensions, mime_types))
        return self

    def build(self) -> ProcessorFactory:
        """
        Build the configured ProcessorFactory.

        Returns:
            Configured ProcessorFactory instance
        """
        factory = ProcessorFactory(
            registry=self._registry,
            validator=self._validator,
            error_handler=self._error_handler,
            enable_validation=self._enable_validation,
        )

        # Register custom processors
        for name, processor_class, extensions, mime_types in self._custom_processors:
            factory.register_custom_processor(
                name, processor_class, extensions, mime_types
            )

        return factory


# Singleton instance for convenience
_default_factory: ProcessorFactory | None = None


def get_default_factory() -> ProcessorFactory:
    """
    Get the default ProcessorFactory singleton.

    Returns:
        Default ProcessorFactory instance
    """
    global _default_factory
    if _default_factory is None:
        _default_factory = ProcessorFactory()
    return _default_factory


def process_file(file_path: str, **config: Any) -> MultiModalContent | None:
    """
    Convenience function to process a file with the default factory.

    Args:
        file_path: Path to the file
        **config: Configuration parameters

    Returns:
        MultiModalContent or None if processing failed
    """
    return get_default_factory().process_file(file_path, **config)
