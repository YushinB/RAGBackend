"""
Configuration Management

This module provides configuration management for the RAG Backend application.
It supports environment-based configuration, validation, and type safety.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseSettings, Field, validator


class Environment(str, Enum):
    """Application environment types."""
    
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""
    
    # PostgreSQL settings
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_user: str = Field(default="postgres", env="POSTGRES_USER")
    postgres_password: str = Field(env="POSTGRES_PASSWORD")
    postgres_database: str = Field(default="rag_backend", env="POSTGRES_DATABASE")
    
    # LanceDB settings
    lancedb_path: str = Field(default="./data/lancedb", env="LANCEDB_PATH")
    lancedb_table_name: str = Field(default="embeddings", env="LANCEDB_TABLE_NAME")
    
    # Redis settings
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    @property
    def postgres_url(self) -> str:
        """Generate PostgreSQL connection URL."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"


class EmbeddingConfig(BaseSettings):
    """Embedding model configuration settings."""
    
    model_name: str = Field(default="bge", env="EMBEDDING_MODEL")
    batch_size: int = Field(default=32, env="EMBEDDING_BATCH_SIZE")
    dimension: int = Field(default=768, env="EMBEDDING_DIMENSION")
    device: str = Field(default="cpu", env="EMBEDDING_DEVICE")
    
    @validator("model_name")
    def validate_model_name(cls, v):
        """Validate embedding model name."""
        allowed_models = ["bge", "qodo"]
        if v not in allowed_models:
            raise ValueError(f"model_name must be one of: {allowed_models}")
        return v
    
    @validator("device")
    def validate_device(cls, v):
        """Validate device setting."""
        allowed_devices = ["cpu", "cuda", "mps"]
        if v not in allowed_devices:
            raise ValueError(f"device must be one of: {allowed_devices}")
        return v


class ChunkingConfig(BaseSettings):
    """Text chunking configuration settings."""
    
    chunk_size: int = Field(default=512, env="CHUNK_SIZE")
    overlap_size: int = Field(default=128, env="CHUNK_OVERLAP")
    min_chunk_size: int = Field(default=100, env="MIN_CHUNK_SIZE")
    max_chunk_size: int = Field(default=1024, env="MAX_CHUNK_SIZE")
    respect_sentence_boundaries: bool = Field(default=True, env="RESPECT_SENTENCE_BOUNDARIES")
    respect_paragraph_boundaries: bool = Field(default=True, env="RESPECT_PARAGRAPH_BOUNDARIES")
    
    @validator("chunk_size")
    def validate_chunk_size(cls, v, values):
        """Validate chunk size is within bounds."""
        min_size = values.get("min_chunk_size", 100)
        max_size = values.get("max_chunk_size", 1024)
        if v < min_size or v > max_size:
            raise ValueError(f"chunk_size must be between {min_size} and {max_size}")
        return v


class LLMConfig(BaseSettings):
    """LLM integration configuration settings."""
    
    api_endpoint: str = Field(env="LLM_API_ENDPOINT")
    api_key: str = Field(env="LLM_API_KEY")
    model_name: str = Field(default="llama2-7b", env="LLM_MODEL_NAME")
    timeout: int = Field(default=30, env="LLM_TIMEOUT")
    max_tokens: int = Field(default=1024, env="LLM_MAX_TOKENS")
    temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    
    @validator("temperature")
    def validate_temperature(cls, v):
        """Validate temperature is between 0 and 2."""
        if v < 0.0 or v > 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
        return v


class StorageConfig(BaseSettings):
    """File storage configuration settings."""
    
    upload_dir: str = Field(default="./data/uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(default=52428800, env="MAX_FILE_SIZE")  # 50MB
    allowed_extensions: List[str] = Field(
        default=["pdf", "docx", "xlsx", "txt", "md"],
        env="ALLOWED_EXTENSIONS"
    )
    
    @validator("allowed_extensions", pre=True)
    def parse_allowed_extensions(cls, v):
        """Parse allowed extensions from string or list."""
        if isinstance(v, str):
            return [ext.strip().lower() for ext in v.split(",")]
        return [ext.lower() for ext in v]


class ServerConfig(BaseSettings):
    """Server configuration settings."""
    
    host: str = Field(default="0.0.0.0", env="SERVER_HOST")
    port: int = Field(default=8000, env="SERVER_PORT")
    workers: int = Field(default=1, env="SERVER_WORKERS")
    reload: bool = Field(default=False, env="SERVER_RELOAD")
    debug: bool = Field(default=False, env="DEBUG")


class LoggingConfig(BaseSettings):
    """Logging configuration settings."""
    
    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(default="json", env="LOG_FORMAT")
    output: str = Field(default="stdout", env="LOG_OUTPUT")
    file_path: Optional[str] = Field(default=None, env="LOG_FILE")
    
    @validator("level")
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"level must be one of: {allowed_levels}")
        return v.upper()


class AppConfig(BaseSettings):
    """Main application configuration."""
    
    # Application settings
    app_name: str = Field(default="RAG Backend", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    secret_key: str = Field(env="SECRET_KEY")
    
    # Component configurations
    database: DatabaseConfig = DatabaseConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    chunking: ChunkingConfig = ChunkingConfig()
    llm: LLMConfig = LLMConfig()
    storage: StorageConfig = StorageConfig()
    server: ServerConfig = ServerConfig()
    logging: LoggingConfig = LoggingConfig()
    
    class Config:
        """Pydantic configuration."""
        
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("environment", pre=True)
    def parse_environment(cls, v):
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


# Global configuration instance
config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    global config
    if config is None:
        config = AppConfig()
        config.create_directories()
    return config


def load_config(config_file: Optional[str] = None) -> AppConfig:
    """Load configuration from file."""
    global config
    
    if config_file:
        # Load from specific config file
        config = AppConfig(_env_file=config_file)
    else:
        # Load from default .env file
        config = AppConfig()
    
    config.create_directories()
    return config


def reset_config() -> None:
    """Reset global configuration (useful for testing)."""
    global config
    config = None