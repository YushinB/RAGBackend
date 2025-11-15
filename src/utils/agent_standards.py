"""
Agent Code Generation Standards Enforcement

This module provides utilities for ensuring all generated code follows
the project's coding conventions as defined in the pre-commit configuration.

Import this module in agent code generation to automatically validate and fix code.
"""

from typing import Any

from src.utils.code_style_validator import auto_fix_code, validate_generated_code

# Coding Standards Checklist for Code Generation
CODING_STANDARDS = {
    "formatting": {
        "line_length": 88,
        "formatter": "Black",
        "indentation": "4 spaces",
        "quotes": "Double quotes preferred",
    },
    "imports": {
        "organization": "Standard -> Third-party -> Local",
        "sorting": "isort with Black profile",
        "unused": "Remove all unused imports",
    },
    "type_hints": {
        "required": "All public functions and methods",
        "style": "Python 3.13+ syntax (e.g., list[str] not List[str])",
        "imports": "from typing import only when necessary",
    },
    "docstrings": {
        "style": "Google style",
        "required": "All public classes, functions, and methods",
        "format": "Triple quotes with proper Args/Returns/Raises",
    },
    "naming": {
        "classes": "PascalCase",
        "functions_variables": "snake_case",
        "constants": "UPPER_SNAKE_CASE",
        "private_methods": "_leading_underscore",
    },
    "security": {
        "no_hardcoded_secrets": "Use environment variables",
        "safe_file_operations": "Use pathlib.Path",
        "input_validation": "Validate all external inputs",
    },
}


def generate_code_with_standards(code_template: str, **kwargs: Any) -> str:
    """
    Generate code that automatically follows project standards.

    Args:
        code_template: Code template to format
        **kwargs: Variables to substitute in template

    Returns:
        Properly formatted code that passes all checks
    """
    # Format the template
    try:
        formatted_code = code_template.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Missing template variable: {e}") from e

    # Auto-fix the code to meet standards
    fixed_code = auto_fix_code(formatted_code)

    # Validate the result
    is_valid, report = validate_generated_code(fixed_code)

    if not is_valid:
        print("⚠️ Generated code has style violations:")
        print(report)
        print("📝 Code was auto-fixed but may need manual review.")

    return fixed_code


def validate_and_fix_code(code: str, context: str = "") -> tuple[str, bool]:
    """
    Validate and auto-fix code to meet project standards.

    Args:
        code: Python code to validate and fix
        context: Optional context for error reporting

    Returns:
        Tuple of (fixed_code, was_valid_initially)
    """
    # Check if code is valid initially
    is_valid_initial, initial_report = validate_generated_code(code)

    if is_valid_initial:
        print(f"✅ Code {context}follows all standards!")
        return code, True

    print(f"🔧 Auto-fixing code {context}...")
    print(initial_report)

    # Auto-fix the code
    fixed_code = auto_fix_code(code)

    # Validate after fixing
    is_valid_after, after_report = validate_generated_code(fixed_code)

    if is_valid_after:
        print(f"✅ Code {context}successfully fixed!")
    else:
        print(f"⚠️ Some issues remain after auto-fix {context}:")
        print(after_report)

    return fixed_code, False


# Template for common code patterns that follow standards
CODE_TEMPLATES = {
    "class_definition": '''
class {class_name}({base_classes}):
    """
    {class_description}

    {class_details}

    Attributes:
        {attributes}

    Example:
        >>> {example_usage}
    """

    def __init__(self, {init_params}) -> None:
        """
        Initialize {class_name}.

        Args:
            {init_args_description}
        """
        {init_implementation}

    {methods}
''',
    "method_definition": '''
    def {method_name}(self, {parameters}) -> {return_type}:
        """
        {method_description}

        Args:
            {args_description}

        Returns:
            {returns_description}

        Raises:
            {raises_description}

        Example:
            >>> {example}
        """
        {implementation}
''',
    "function_definition": '''
def {function_name}({parameters}) -> {return_type}:
    """
    {function_description}

    Args:
        {args_description}

    Returns:
        {returns_description}

    Raises:
        {raises_description}

    Example:
        >>> {example}
    """
    {implementation}
''',
    "processor_class": '''
from pathlib import Path
from typing import Any, Union
from uuid import uuid4

from src.core.debug_logger import PDFDebugLogger, debug_operation, get_production_safe_debug_logger
from src.models.base_models import MultiModalContent, TextChunk
from src.processors.base import DataProcessor


class {processor_name}(DataProcessor):
    """
    Processor for {file_type} documents.

    {processor_description}

    Attributes:
        supported_extensions: Set of file extensions {extensions}
        processor_name: Human-readable name ('{display_name}')
    """

    supported_extensions = {extensions}
    processor_name = "{display_name}"

    def __init__(self, **config: Any) -> None:
        """
        Initialize the {processor_name} processor.

        Args:
            **config: Configuration parameters:
                {config_description}
                - debug: Enable debug logging (default: False)
                - debug_level: Debug logging level (default: "DEBUG")
        """
        super().__init__(**config)
        {config_initialization}

        # Initialize debug logging with production detection
        debug_enabled = config.get("debug", False)
        debug_level = config.get("debug_level", "DEBUG")
        if debug_enabled:
            self.debug_logger = PDFDebugLogger(level=debug_level, auto_detect_production=True)
        else:
            self.debug_logger = get_production_safe_debug_logger()

    def can_process(self, file_path: Union[Path, str]) -> bool:
        """
        Determine if this processor can handle the given file.

        Args:
            file_path: Path to the file to check

        Returns:
            True if file can be processed, False otherwise
        """
        path = Path(file_path)
        return path.suffix.lower() in self.supported_extensions

    @debug_operation("{processor_name} Text Extraction")
    def extract_text(self, file_path: Union[Path, str]) -> str:
        """
        Extract all text content from the file.

        Args:
            file_path: Path to the file

        Returns:
            Extracted text content

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file is invalid or corrupted
        """
        self.validate_file(file_path)

        with self.debug_logger.debug_operation("Extract text", file_path=str(file_path)):
            {text_extraction_implementation}

    @debug_operation("{processor_name} Multimodal Content Extraction")
    def extract_multimodal_content(
        self,
        file_path: Union[Path, str],
        document_id: str
    ) -> MultiModalContent:
        """
        Extract all content including text, images, tables, and other elements.

        Args:
            file_path: Path to the file
            document_id: Unique identifier for this document

        Returns:
            MultiModalContent object with all extracted content

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file is invalid or corrupted
        """
        self.validate_file(file_path)

        with self.debug_logger.debug_operation("Multimodal extraction",
                                             file_path=str(file_path),
                                             document_id=document_id):
            {multimodal_extraction_implementation}
''',
}


def get_standard_imports_for_processor() -> str:
    """Get standard imports for processor classes."""
    return auto_fix_code("""
from pathlib import Path
from typing import Any, Union
from uuid import uuid4

from src.core.debug_logger import PDFDebugLogger, debug_operation, get_production_safe_debug_logger
from src.models.base_models import MultiModalContent, TextChunk
from src.processors.base import DataProcessor
""")


def ensure_standards(func: Any) -> Any:
    """
    Decorator to ensure generated code meets quality standards.

    Use this decorator on functions that generate code to automatically
    validate and fix the output.
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = func(*args, **kwargs)

        if isinstance(result, str):
            # Assume it's code to validate
            fixed_code, _was_valid = validate_and_fix_code(
                result, f"from {func.__name__} "
            )
            return fixed_code

        return result

    return wrapper


# Pre-commit hooks summary for reference
PRE_COMMIT_TOOLS = {
    "trailing-whitespace": "Remove trailing whitespace",
    "end-of-file-fixer": "Ensure files end with newline",
    "check-yaml": "Validate YAML syntax",
    "check-json": "Validate JSON syntax",
    "pretty-format-json": "Format JSON files",
    "check-merge-conflict": "Check for merge conflict markers",
    "check-toml": "Validate TOML syntax",
    "debug-statements": "Remove debug print/pdb statements",
    "black": "Code formatting (88 char line length)",
    "ruff": "Fast Python linter with auto-fixing",
    "ruff-format": "Additional formatting",
    "mypy": "Type checking with strict settings",
    "isort": "Import sorting (Black profile)",
    "bandit": "Security vulnerability scanning",
}

print("🛠️ Code generation standards loaded!")
print("📋 Pre-commit tools configured:")
for tool, description in PRE_COMMIT_TOOLS.items():
    print(f"  ✅ {tool}: {description}")
