"""
Integration example for ProcessorFactory.

Demonstrates how to use the ProcessorFactory for automatic
file type detection and processing.
"""

from pathlib import Path

from src.models.base_models import MultiModalContent
from src.processors.base import DataProcessor
from src.processors.factory import (
    ProcessorFactory,
    ProcessorFactoryBuilder,
    get_default_factory,
)


def example_basic_usage() -> None:
    """
    Example: Basic usage with default factory.
    """
    print("\n=== Basic ProcessorFactory Usage ===\n")

    # Get the default factory singleton
    factory = get_default_factory()

    # Show supported file types
    print("Supported processors:")
    for processor_name in factory.get_supported_processors():
        print(f"  - {processor_name}")

    print("\nSupported file extensions:")
    extensions = factory.get_supported_extensions()
    print(f"  {', '.join(sorted(extensions)[:10])}...")  # Show first 10

    # Check if specific files can be processed
    print("\nChecking file support:")
    test_files = [
        "document.pdf",
        "report.docx",
        "data.xlsx",
        "readme.md",
        "notes.txt",
        "unknown.xyz",
    ]

    for file_path in test_files:
        can_process = factory.can_process(file_path)
        status = "✓ Supported" if can_process else "✗ Not supported"
        print(f"  {file_path:<20} {status}")


def example_automatic_processing() -> None:
    """
    Example: Automatically process files based on type.
    """
    print("\n=== Automatic File Processing ===\n")

    factory = get_default_factory()

    # Simulate processing different file types
    print("Processing different file types:\n")

    file_examples = [
        ("research_paper.pdf", "PDF document"),
        ("proposal.docx", "Word document"),
        ("budget.xlsx", "Excel spreadsheet"),
        ("README.md", "Markdown file"),
        ("log.txt", "Text file"),
    ]

    for filename, description in file_examples:
        print(f"File: {filename} ({description})")

        # Get appropriate processor
        processor = factory.get_processor_for_file(filename)

        if processor:
            print(f"  → Processor: {processor.__class__.__name__}")
            print(f"  → Can process: {processor.can_process(filename)}")
        else:
            print("  → No processor available")

        print()


def example_custom_processor() -> None:
    """
    Example: Register and use a custom processor.
    """
    print("\n=== Custom Processor Registration ===\n")

    # Create a custom processor for CSV files
    class CSVProcessor(DataProcessor):
        """Custom processor for CSV files."""

        def can_process(self, file_path: Path | str) -> bool:
            """Check if file is a CSV."""
            return str(file_path).lower().endswith(".csv")

        def process(self, file_path: Path | str, **kwargs: object) -> MultiModalContent:
            """Process CSV file."""
            print(f"    Processing CSV: {file_path}")

            # Create content (simplified)
            content = MultiModalContent(document_id=Path(file_path).stem)

            # In real implementation, would parse CSV and create chunks
            # For demo, just return basic content
            return content

    # Create factory and register custom processor
    factory = ProcessorFactory()
    factory.register_custom_processor(
        name="csv",
        processor_class=CSVProcessor,  # type: ignore[type-abstract]
        extensions=[".csv", ".tsv"],
        mime_types=["text/csv", "text/tab-separated-values"],
    )

    print("Registered custom CSV processor")
    print(f"Supported processors: {factory.get_supported_processors()}\n")

    # Test the custom processor
    csv_file = "data.csv"
    print(f"Testing with: {csv_file}")

    processor = factory.get_processor_for_file(csv_file)
    if processor:
        print(f"  Got processor: {processor.__class__.__name__}")
        print(f"  Can process: {processor.can_process(csv_file)}")


def example_builder_pattern() -> None:
    """
    Example: Use builder pattern for factory configuration.
    """
    print("\n=== Builder Pattern Configuration ===\n")

    # Custom processors for specialized formats
    class LatexProcessor(DataProcessor):
        """Process LaTeX documents."""

        def can_process(self, file_path: Path | str) -> bool:
            return str(file_path).lower().endswith((".tex", ".latex"))

        def process(self, file_path: Path | str, **kwargs: object) -> MultiModalContent:
            print(f"    Processing LaTeX: {file_path}")
            return MultiModalContent(document_id="latex-doc")

    class BibtexProcessor(DataProcessor):
        """Process BibTeX bibliography files."""

        def can_process(self, file_path: Path | str) -> bool:
            return str(file_path).lower().endswith(".bib")

        def process(self, file_path: Path | str, **kwargs: object) -> MultiModalContent:
            print(f"    Processing BibTeX: {file_path}")
            return MultiModalContent(document_id="bibtex-doc")

    # Build factory with custom processors using fluent interface
    factory = (
        ProcessorFactoryBuilder()
        .with_processor(
            name="latex",
            processor_class=LatexProcessor,  # type: ignore[type-abstract]
            extensions=[".tex", ".latex"],
            mime_types=["application/x-latex", "text/x-tex"],
        )
        .with_processor(
            name="bibtex",
            processor_class=BibtexProcessor,  # type: ignore[type-abstract]
            extensions=[".bib"],
            mime_types=["application/x-bibtex"],
        )
        .build()
    )

    print("Built factory with custom processors\n")

    # Test the configured factory
    test_files = [
        "paper.tex",
        "references.bib",
        "document.pdf",  # Built-in processor
    ]

    for filename in test_files:
        processor = factory.get_processor_for_file(filename)
        if processor:
            print(f"{filename:<20} → {processor.__class__.__name__}")
        else:
            print(f"{filename:<20} → No processor")


def example_batch_processing() -> None:
    """
    Example: Process multiple files in batch.
    """
    print("\n=== Batch File Processing ===\n")

    factory = get_default_factory()

    # Simulate a directory of mixed file types
    files = [
        "chapter1.pdf",
        "chapter2.pdf",
        "notes.docx",
        "data.xlsx",
        "README.md",
        "todo.txt",
        "config.json",  # Text processor handles JSON
    ]

    print(f"Processing {len(files)} files:\n")

    processed = 0
    skipped = 0

    for file_path in files:
        try:
            processor = factory.get_processor_for_file(file_path)

            if processor and processor.can_process(file_path):
                print(f"✓ {file_path:<20} → {processor.__class__.__name__}")
                processed += 1
            else:
                print(f"✗ {file_path:<20} → Skipped (no processor)")
                skipped += 1

        except Exception as e:
            print(f"✗ {file_path:<20} → Error: {e}")
            skipped += 1

    print(f"\nResults: {processed} processed, {skipped} skipped")


def example_convenience_function() -> None:
    """
    Example: Use convenience function for quick processing.
    """
    print("\n=== Convenience Function Usage ===\n")

    print("The process_file() convenience function automatically:")
    print("  1. Detects file type")
    print("  2. Selects appropriate processor")
    print("  3. Processes the file")
    print("  4. Returns MultiModalContent\n")

    print("Example usage:")
    print('  content = process_file("document.pdf")')
    print('  content = process_file("data.xlsx", extract_formulas=True)')
    print('  content = process_file("README.md")\n')

    print("Note: Requires actual files to exist for processing")


def example_error_handling() -> None:
    """
    Example: Handle errors gracefully.
    """
    print("\n=== Error Handling ===\n")

    factory = ProcessorFactory()

    test_cases = [
        ("nonexistent.pdf", "File doesn't exist"),
        ("unknown.xyz", "Unsupported format"),
    ]

    for file_path, scenario in test_cases:
        print(f"Scenario: {scenario}")
        print(f"  File: {file_path}")

        try:
            # Check if can process
            if factory.can_process(file_path):
                print("  Status: Can process")
            else:
                print("  Status: Cannot process")

            # Try to get processor
            processor = factory.get_processor_for_file(file_path)
            if processor:
                print(f"  Processor: {processor.__class__.__name__}")
            else:
                print("  Processor: None found")

        except Exception as e:
            print(f"  Error: {type(e).__name__}: {e}")

        print()


def example_configuration_passing() -> None:
    """
    Example: Pass configuration to processors.
    """
    print("\n=== Configuration Passing ===\n")

    factory = ProcessorFactory()

    print("Get processor with custom configuration:\n")

    # Example configurations for different processors
    configs = [
        (
            "document.pdf",
            {"extract_images": True, "ocr_enabled": False},
        ),
        (
            "data.xlsx",
            {"extract_formulas": True, "sheet_name": "Summary"},
        ),
        (
            "README.md",
            {"parse_tables": True, "extract_links": True},
        ),
    ]

    for file_path, config in configs:
        print(f"File: {file_path}")
        print(f"Config: {config}")

        processor = factory.get_processor_for_file(file_path)
        if processor:
            print(f"Result: Created {processor.__class__.__name__} with config")
            # Note: Config would be passed to process() method when called
        print()


def main() -> None:
    """Run all examples."""
    print("=" * 70)
    print("ProcessorFactory - Integration Examples")
    print("=" * 70)

    example_basic_usage()
    example_automatic_processing()
    example_custom_processor()
    example_builder_pattern()
    example_batch_processing()
    example_convenience_function()
    example_error_handling()
    example_configuration_passing()

    print("\n" + "=" * 70)
    print("Examples completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
