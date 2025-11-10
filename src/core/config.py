"""Configuration Management.

This module provides configuration management for the RAG Backend application.
It supports environment-based configuration, validation, and type safety.
"""

import os
from enum import Enum
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Application environment types."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""

    # PostgreSQL settings
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_user: str = Field(default="postgres", description="PostgreSQL user")
    postgres_password: str = Field(
        default="password", description="PostgreSQL password"
    )
    postgres_database: str = Field(
        default="rag_backend", description="PostgreSQL database"
    )

    # LanceDB settings
    lancedb_path: str = Field(
        default="./data/lancedb", description="LanceDB storage path"
    )
    lancedb_table_name: str = Field(
        default="embeddings", description="LanceDB table name"
    )

    # Redis settings
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_password: str | None = Field(default=None, description="Redis password")
    redis_db: int = Field(default=0, description="Redis database number")

    model_config = {
        "env_prefix": "",
        "case_sensitive": False,
    }

    @property
    def postgres_url(self) -> str:
        """Generate PostgreSQL connection URL."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"


class EmbeddingConfig(BaseSettings):
    """Embedding model configuration settings."""

    model_name: str = Field(default="bge", description="Embedding model name")
    batch_size: int = Field(default=32, description="Embedding batch size")
    dimension: int = Field(default=768, description="Embedding dimension")
    device: str = Field(default="cpu", description="Embedding computation device")

    model_config = {
        "env_prefix": "EMBEDDING_",
        "case_sensitive": False,
    }

    @field_validator("model_name")
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        """Validate embedding model name."""
        allowed_models = ["bge", "qodo"]
        if v not in allowed_models:
            raise ValueError(f"model_name must be one of: {allowed_models}")
        return v

    @field_validator("device")
    @classmethod
    def validate_device(cls, v: str) -> str:
        """Validate device setting."""
        allowed_devices = ["cpu", "cuda", "mps"]
        if v not in allowed_devices:
            raise ValueError(f"device must be one of: {allowed_devices}")
        return v


class ChunkingConfig(BaseSettings):
    """Text chunking configuration settings."""

    chunk_size: int = Field(default=512, description="Text chunk size")
    overlap_size: int = Field(default=128, description="Chunk overlap size")
    min_chunk_size: int = Field(default=100, description="Minimum chunk size")
    max_chunk_size: int = Field(default=1024, description="Maximum chunk size")
    respect_sentence_boundaries: bool = Field(
        default=True, description="Respect sentence boundaries when chunking"
    )
    respect_paragraph_boundaries: bool = Field(
        default=True, description="Respect paragraph boundaries when chunking"
    )

    model_config = {
        "env_prefix": "CHUNK_",
        "case_sensitive": False,
    }

    @field_validator("chunk_size")
    @classmethod
    def validate_chunk_size(cls, v: int) -> int:
        """Validate chunk size is within bounds."""
        if v < 100 or v > 1024:
            raise ValueError("chunk_size must be between 100 and 1024")
        return v


class LLMConfig(BaseSettings):
    """LLM integration configuration settings."""

    api_endpoint: str = Field(
        default="http://localhost:8080/api", description="LLM API endpoint"
    )
    api_key: str = Field(default="your-api-key-here", description="LLM API key")
    model_name: str = Field(default="llama2-7b", description="LLM model name")
    timeout: int = Field(default=30, description="LLM request timeout")
    max_tokens: int = Field(default=1024, description="Maximum tokens per request")
    temperature: float = Field(default=0.7, description="LLM temperature setting")

    model_config = {
        "env_prefix": "LLM_",
        "case_sensitive": False,
    }

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is between 0 and 2."""
        if v < 0.0 or v > 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
        return v


class StorageConfig(BaseSettings):
    """File storage configuration settings."""

    upload_dir: str = Field(
        default="./data/uploads", description="Upload directory path"
    )
    max_file_size: int = Field(
        default=52428800, description="Maximum file size in bytes"
    )  # 50MB
    allowed_extensions: list[str] = Field(
        default=["pdf", "docx", "xlsx", "txt", "md"],
        description="Allowed file extensions",
    )

    model_config = {
        "env_prefix": "STORAGE_",
        "case_sensitive": False,
    }

    @field_validator("allowed_extensions", mode="before")
    @classmethod
    def parse_allowed_extensions(cls, v: str | list[str]) -> list[str]:
        """Parse allowed extensions from string or list."""
        if isinstance(v, str):
            return [ext.strip().lower() for ext in v.split(",")]
        return [ext.lower() for ext in v]


class ServerConfig(BaseSettings):
    """Server configuration settings."""

    host: str = Field(default="0.0.0.0", description="Server host")  # nosec B104
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of workers")
    reload: bool = Field(default=False, description="Enable auto-reload")
    debug: bool = Field(default=False, description="Enable debug mode")

    model_config = {
        "env_prefix": "SERVER_",
        "case_sensitive": False,
    }


class LoggingConfig(BaseSettings):
    """Logging configuration settings."""

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format")
    output: str = Field(default="stdout", description="Log output destination")
    file_path: str | None = Field(default=None, description="Log file path")

    model_config = {
        "env_prefix": "LOG_",
        "case_sensitive": False,
    }

    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"level must be one of: {allowed_levels}")
        return v.upper()


class AppConfig(BaseSettings):
    """Main application configuration."""

    # Application settings
    app_name: str = Field(default="RAG Backend", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: Environment = Field(
        default=Environment.DEVELOPMENT, description="Application environment"
    )
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Application secret key",
    )

    # Component configurations
    database: DatabaseConfig = DatabaseConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    chunking: ChunkingConfig = ChunkingConfig()
    llm: LLMConfig = LLMConfig()
    storage: StorageConfig = StorageConfig()
    server: ServerConfig = ServerConfig()
    logging: LoggingConfig = LoggingConfig()

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @field_validator("environment", mode="before")
    @classmethod
    def parse_environment(cls, v: str | Environment) -> Environment:
        """Parse environment from string."""
        if isinstance(v, str):
            return Environment(v.lower())
        return v

    def create_directories(self) -> None:
        """Create necessary directories."""
        dirs_to_create = [
            self.storage.upload_dir,
            self.database.lancedb_path,
        ]

        # Add log directory if file logging is enabled
        if self.logging.file_path:
            log_dir = Path(self.logging.file_path).parent
            dirs_to_create.append(str(log_dir))

        for dir_path in dirs_to_create:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


class ConfigManager:
    """Configuration manager singleton."""

    _instance: AppConfig | None = None

    @classmethod
    def get_config(cls) -> AppConfig:
        """Get the global configuration instance."""
        if cls._instance is None:
            cls._instance = AppConfig()
            cls._instance.create_directories()
        return cls._instance

    @classmethod
    def load_config(cls, config_file: str | None = None) -> AppConfig:
        """Load configuration from file."""
        if config_file:
            # Load from specific config file
            # In Pydantic v2, we need to set the env_file via environment or other means
            original_env_file = os.environ.get("ENV_FILE")
            try:
                os.environ["ENV_FILE"] = config_file
                cls._instance = AppConfig()
            finally:
                if original_env_file is not None:
                    os.environ["ENV_FILE"] = original_env_file
                elif "ENV_FILE" in os.environ:
                    del os.environ["ENV_FILE"]
        else:
            # Load from default .env file
            cls._instance = AppConfig()

        cls._instance.create_directories()
        return cls._instance

    @classmethod
    def reset_config(cls) -> None:
        """Reset global configuration (useful for testing)."""
        cls._instance = None


# Global configuration instance
config: AppConfig | None = None


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    return ConfigManager.get_config()


def load_config(config_file: str | None = None) -> AppConfig:
    """Load configuration from file."""
    return ConfigManager.load_config(config_file)


def reset_config() -> None:
    """Reset global configuration (useful for testing)."""
    ConfigManager.reset_config()
