"""
Production Environment Detection Demo

This script demonstrates how the debug logging system automatically
detects production environments and adjusts logging behavior accordingly.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.debug_logger import (
    DebugConfig,
    PDFDebugLogger,
    get_production_safe_debug_logger,
    is_production,
)
from src.processors.excel_processor import ExcelProcessor
from src.processors.pdf_processor import PDFProcessor


def demo_production_detection() -> None:
    """Demonstrate production environment detection."""
    print("=== Production Environment Detection Demo ===")
    print()

    # 1. Check current environment
    print("1. Current Environment Detection")
    print("-" * 35)

    config = DebugConfig()
    env_info = config.get_environment_info()

    print(f"Environment Type: {env_info['environment_type']}")
    print(f"Production Mode: {env_info['is_production']}")
    print(f"Debug Enabled: {env_info['debug_enabled']}")
    print()

    if env_info["relevant_env_vars"]:
        print("Relevant Environment Variables:")
        for key, value in env_info["relevant_env_vars"].items():
            print(f"  {key} = {value}")
    else:
        print("No relevant environment variables detected")

    print()

    # 2. Demonstrate automatic configuration
    print("2. Automatic Debug Configuration")
    print("-" * 33)

    print("Default configuration (auto-detect enabled):")
    default_config = DebugConfig()
    print(f"  - Enabled: {default_config.enabled}")
    print(f"  - Level: {default_config.level}")
    print(f"  - Image logging: {default_config.log_images}")
    print(f"  - Performance logging: {default_config.log_performance}")

    print()
    print("Forced development configuration:")
    dev_config = DebugConfig(enabled=True, auto_detect_production=False)
    print(f"  - Enabled: {dev_config.enabled}")
    print(f"  - Level: {dev_config.level}")
    print(f"  - Image logging: {dev_config.log_images}")

    print()
    print("Forced production configuration:")
    prod_config = DebugConfig(enabled=False, auto_detect_production=False)
    print(f"  - Enabled: {prod_config.enabled}")
    print(f"  - Level: {prod_config.level}")
    print(f"  - Image logging: {prod_config.log_images}")

    print()

    # 3. Demonstrate logger behavior
    print("3. Logger Behavior in Different Modes")
    print("-" * 37)

    print("Development mode logger:")
    dev_logger = PDFDebugLogger(auto_detect_production=False)
    with dev_logger.debug_operation("Test Operation"):
        dev_logger.debug_stage("Sample stage")
        dev_logger.debug_data("Sample data", {"test": "value"})

    print()
    print("Production-aware logger (auto-detect):")
    prod_logger = get_production_safe_debug_logger()
    with prod_logger.debug_operation("Test Operation"):
        prod_logger.debug_stage("Sample stage")
        prod_logger.debug_data("Sample data", {"test": "value"})

    print()

    # 4. Simulate production environment
    print("4. Simulating Production Environment")
    print("-" * 35)

    # Save current environment
    original_env = os.environ.get("ENVIRONMENT", "")

    # Set production environment
    os.environ["ENVIRONMENT"] = "production"

    print("Set ENVIRONMENT=production")

    # Test configuration in simulated production
    sim_config = DebugConfig()
    sim_env_info = sim_config.get_environment_info()

    print(f"Detected Environment: {sim_env_info['environment_type']}")
    print(f"Debug Enabled: {sim_env_info['debug_enabled']}")
    print(f"Logging Level: {sim_config.level}")

    # Test logger in simulated production
    print()
    print("Logger behavior in simulated production:")
    sim_logger = PDFDebugLogger(auto_detect_production=True)
    with sim_logger.debug_operation("Test Operation"):
        sim_logger.debug_stage("This should be suppressed")
        sim_logger.debug_data(
            "This data logging should be suppressed", {"sensitive": "data"}
        )

    # Restore original environment
    if original_env:
        os.environ["ENVIRONMENT"] = original_env
    else:
        os.environ.pop("ENVIRONMENT", None)

    print()

    # 5. Processor integration
    print("5. Processor Integration")
    print("-" * 23)

    print("Creating processors with auto production detection...")

    # PDF Processor
    pdf_processor = PDFProcessor(debug=True)
    print(f"PDF Processor debug mode: {hasattr(pdf_processor, 'debug_logger')}")

    # Excel Processor
    excel_processor = ExcelProcessor(debug=True)
    print(f"Excel Processor debug mode: {hasattr(excel_processor, 'debug_logger')}")

    print()

    # 6. Quick utility functions
    print("6. Quick Utility Functions")
    print("-" * 26)

    print(f"is_production(): {is_production()}")

    quick_logger = get_production_safe_debug_logger()
    production_mode = getattr(quick_logger, "production_mode", False)
    print(f"Production-safe logger in production mode: {production_mode}")

    print()
    print("=== Demo Complete ===")
    print()
    print("Key Takeaways:")
    print("1. Debug logging automatically detects production environments")
    print("2. In production, debug logging is minimized to ERROR level only")
    print(
        "3. Sensitive debug features (data logging, performance tracking) are disabled"
    )
    print("4. You can override auto-detection by setting enabled=True/False explicitly")
    print("5. Processors automatically integrate with production-safe logging")


def demo_environment_variables() -> None:
    """Show what environment variables trigger production detection."""
    print()
    print("=== Environment Variables for Production Detection ===")
    print()
    print("The following environment variables trigger production mode:")
    print()

    production_vars = [
        ("ENVIRONMENT", ["prod", "production"]),
        ("ENV", ["prod", "production"]),
        ("NODE_ENV", ["production"]),
        ("FLASK_ENV", ["production"]),
        ("DJANGO_ENV", ["production"]),
        ("PYTHON_ENV", ["production"]),
        ("DEBUG", ["false", "0", "no"]),
        ("DEBUG_MODE", ["false", "0", "no"]),
        ("CONTAINER_ENV", ["production"]),
        ("DEPLOYMENT_ENV", ["production"]),
    ]

    print("Standard Environment Variables:")
    for var, values in production_vars:
        print(f"  {var}: {', '.join(values)}")

    print()
    print("Cloud Platform Indicators (presence triggers production):")
    cloud_vars = [
        "KUBERNETES_SERVICE_HOST",
        "AWS_EXECUTION_ENV",
        "GOOGLE_CLOUD_PROJECT",
        "AZURE_FUNCTIONS_ENVIRONMENT",
    ]

    for var in cloud_vars:
        print(f"  {var}")

    print()
    print("Example usage:")
    print("  # Development (debug enabled)")
    print("  # No special environment variables")
    print()
    print("  # Production (debug disabled)")
    print("  export ENVIRONMENT=production")
    print("  # or")
    print("  export ENV=prod")
    print("  # or")
    print("  export DEBUG=false")


if __name__ == "__main__":
    demo_production_detection()
    demo_environment_variables()
