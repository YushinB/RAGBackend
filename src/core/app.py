"""Application Initialization.

This module provides initialization functionality for the RAG Backend application.
"""

import asyncio
import sys
from pathlib import Path

from .config import AppConfig, get_config, load_config
from .exceptions import ConfigurationException
from .logging import get_logger, setup_logging


async def initialize_app(config_file: str | None = None) -> AppConfig:
    """Initialize the RAG Backend application.

    Args:
        config_file: Optional path to configuration file

    Returns:
        Loaded configuration

    Raises:
        ConfigurationException: If configuration is invalid
    """
    try:
        # Load configuration
        if config_file:
            config = load_config(config_file)
        else:
            config = get_config()

        # Setup logging
        setup_logging(
            level=config.logging.level,
            format_type=config.logging.format,
            output=config.logging.output,
            file_path=config.logging.file_path,
        )

        logger = get_logger(__name__)
        logger.info(
            "Starting RAG Backend application",
            extra={
                "version": config.app_version,
                "environment": config.environment.value,
            },
        )

        # Create necessary directories
        config.create_directories()
        logger.info("Created application directories")

        # Validate configuration
        await validate_configuration(config)
        logger.info("Configuration validated successfully")

        return config

    except Exception as e:
        print(f"Failed to initialize application: {e}", file=sys.stderr)
        raise ConfigurationException(
            "Application initialization failed", details={"error": str(e)}
        ) from e


async def validate_configuration(config: AppConfig) -> None:
    """Validate application configuration.

    Args:
        config: Application configuration to validate

    Raises:
        ConfigurationException: If configuration is invalid
    """
    logger = get_logger(__name__)

    # Validate required directories exist or can be created
    try:
        directories_to_check = [
            config.storage.upload_dir,
            config.database.lancedb_path,
            Path(config.logging.file_path).parent if config.logging.file_path else None,
        ]

        for dir_path in directories_to_check:
            if dir_path:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                logger.debug(f"Validated directory: {dir_path}")

    except Exception as e:
        raise ConfigurationException(
            "Failed to create required directories", details={"error": str(e)}
        ) from e

    # Validate file size limits
    if config.storage.max_file_size <= 0:
        raise ConfigurationException(
            "Invalid max_file_size configuration",
            config_key="storage.max_file_size",
            config_value=config.storage.max_file_size,
        )

    # Validate chunk configuration
    if config.chunking.chunk_size <= 0:
        raise ConfigurationException(
            "Invalid chunk_size configuration",
            config_key="chunking.chunk_size",
            config_value=config.chunking.chunk_size,
        )

    if config.chunking.overlap_size >= config.chunking.chunk_size:
        raise ConfigurationException(
            "overlap_size must be less than chunk_size",
            config_key="chunking.overlap_size",
            config_value=config.chunking.overlap_size,
        )

    logger.info("Configuration validation completed")


async def shutdown_app() -> None:
    """Graceful application shutdown."""
    logger = get_logger(__name__)
    logger.info("Shutting down RAG Backend application")

    # Add cleanup tasks here in future milestones:
    # - Close database connections
    # - Cancel background tasks
    # - Save any pending data

    logger.info("Application shutdown complete")


def main() -> None:
    """Main entry point for the application."""
    try:
        asyncio.run(initialize_app())
        print("RAG Backend initialized successfully")
    except Exception as e:
        print(f"Failed to initialize RAG Backend: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
