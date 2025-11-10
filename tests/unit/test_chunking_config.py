"""
Tests for ChunkingConfig and related classes.

This module tests the chunking configuration system including:
- ChunkingConfig creation and validation
- Default configuration profiles
- Configuration serialization/deserialization
- Strategy and boundary type validation
"""

import pytest

from src.models.chunking_config import (
    BoundaryType,
    ChunkingConfig,
    ChunkingStrategy,
)


class TestChunkingStrategy:
    """Tests for ChunkingStrategy enum."""

    def test_strategy_values(self):
        """Test that all strategies have correct values."""
        assert ChunkingStrategy.FIXED_SIZE.value == "fixed_size"
        assert ChunkingStrategy.SENTENCE.value == "sentence"
        assert ChunkingStrategy.PARAGRAPH.value == "paragraph"
        assert ChunkingStrategy.SEMANTIC.value == "semantic"
        assert ChunkingStrategy.HIERARCHICAL.value == "hierarchical"
        assert ChunkingStrategy.SLIDING_WINDOW.value == "sliding_window"

    def test_strategy_enumeration(self):
        """Test that we can enumerate all strategies."""
        strategies = list(ChunkingStrategy)
        assert len(strategies) == 6
        assert ChunkingStrategy.PARAGRAPH in strategies


class TestBoundaryType:
    """Tests for BoundaryType enum."""

    def test_boundary_values(self):
        """Test that all boundary types have correct values."""
        assert BoundaryType.CHARACTER.value == "character"
        assert BoundaryType.TOKEN.value == "token"
        assert BoundaryType.SENTENCE.value == "sentence"
        assert BoundaryType.PARAGRAPH.value == "paragraph"
        assert BoundaryType.SECTION.value == "section"

    def test_boundary_enumeration(self):
        """Test that we can enumerate all boundary types."""
        boundaries = list(BoundaryType)
        assert len(boundaries) == 5
        assert BoundaryType.CHARACTER in boundaries


class TestChunkingConfigBasics:
    """Tests for basic ChunkingConfig functionality."""

    def test_default_initialization(self):
        """Test creating config with default values."""
        config = ChunkingConfig()

        assert config.strategy == ChunkingStrategy.PARAGRAPH
        assert config.chunk_size == 512
        assert config.chunk_overlap == 50
        assert config.boundary_type == BoundaryType.CHARACTER
        assert config.min_chunk_size == 100
        assert config.max_chunk_size == 2048
        assert config.respect_sentence_boundaries is True
        assert config.respect_paragraph_boundaries is True
        assert config.respect_section_boundaries is False

    def test_custom_initialization(self):
        """Test creating config with custom values."""
        config = ChunkingConfig(
            strategy=ChunkingStrategy.SENTENCE,
            chunk_size=256,
            chunk_overlap=25,
            min_chunk_size=50,
            max_chunk_size=512,
        )

        assert config.strategy == ChunkingStrategy.SENTENCE
        assert config.chunk_size == 256
        assert config.chunk_overlap == 25
        assert config.min_chunk_size == 50
        assert config.max_chunk_size == 512

    def test_metadata_fields_default(self):
        """Test that metadata_fields defaults to empty list."""
        config = ChunkingConfig()
        assert config.metadata_fields == []
        assert isinstance(config.metadata_fields, list)


class TestChunkingConfigValidation:
    """Tests for ChunkingConfig validation."""

    def test_invalid_chunk_size_negative(self):
        """Test that negative chunk size raises error."""
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            ChunkingConfig(chunk_size=-1)

    def test_invalid_chunk_size_zero(self):
        """Test that zero chunk size raises error."""
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            ChunkingConfig(chunk_size=0)

    def test_invalid_min_chunk_size(self):
        """Test that negative min_chunk_size raises error."""
        with pytest.raises(ValueError, match="min_chunk_size must be positive"):
            ChunkingConfig(min_chunk_size=-1)

    def test_invalid_max_less_than_min(self):
        """Test that max < min raises error."""
        with pytest.raises(ValueError, match="max_chunk_size must be >= min_chunk_size"):
            ChunkingConfig(min_chunk_size=100, max_chunk_size=50)

    def test_invalid_chunk_size_too_small(self):
        """Test that chunk_size < min_chunk_size raises error."""
        with pytest.raises(ValueError, match="chunk_size must be >= min_chunk_size"):
            ChunkingConfig(chunk_size=50, min_chunk_size=100)

    def test_invalid_chunk_size_too_large(self):
        """Test that chunk_size > max_chunk_size raises error."""
        with pytest.raises(ValueError, match="chunk_size must be <= max_chunk_size"):
            ChunkingConfig(chunk_size=3000, max_chunk_size=2048)

    def test_invalid_overlap_negative(self):
        """Test that negative overlap raises error."""
        with pytest.raises(ValueError, match="chunk_overlap must be non-negative"):
            ChunkingConfig(chunk_overlap=-1)

    def test_invalid_overlap_too_large(self):
        """Test that overlap >= chunk_size raises error."""
        with pytest.raises(ValueError, match="chunk_overlap must be < chunk_size"):
            ChunkingConfig(chunk_size=100, chunk_overlap=100)

    def test_invalid_overlap_greater_than_size(self):
        """Test that overlap > chunk_size raises error."""
        with pytest.raises(ValueError, match="chunk_overlap must be < chunk_size"):
            ChunkingConfig(chunk_size=100, chunk_overlap=150)


class TestChunkingConfigStrategyValidation:
    """Tests for strategy-specific validation."""

    def test_semantic_requires_sentence_boundaries(self):
        """Test that semantic strategy requires sentence boundaries."""
        with pytest.raises(
            ValueError, match="Semantic strategy requires respect_sentence_boundaries=True"
        ):
            ChunkingConfig(
                strategy=ChunkingStrategy.SEMANTIC,
                respect_sentence_boundaries=False,
            )

    def test_semantic_with_sentence_boundaries_ok(self):
        """Test that semantic strategy works with sentence boundaries."""
        config = ChunkingConfig(
            strategy=ChunkingStrategy.SEMANTIC,
            respect_sentence_boundaries=True,
        )
        assert config.strategy == ChunkingStrategy.SEMANTIC

    def test_hierarchical_requires_section_boundaries(self):
        """Test that hierarchical strategy requires section boundaries."""
        with pytest.raises(
            ValueError,
            match="Hierarchical strategy requires respect_section_boundaries=True",
        ):
            ChunkingConfig(
                strategy=ChunkingStrategy.HIERARCHICAL,
                respect_section_boundaries=False,
            )

    def test_hierarchical_with_section_boundaries_ok(self):
        """Test that hierarchical strategy works with section boundaries."""
        config = ChunkingConfig(
            strategy=ChunkingStrategy.HIERARCHICAL,
            respect_section_boundaries=True,
        )
        assert config.strategy == ChunkingStrategy.HIERARCHICAL


class TestChunkingConfigProfiles:
    """Tests for predefined configuration profiles."""

    def test_default_profile(self):
        """Test default configuration profile."""
        config = ChunkingConfig.default()

        assert config.strategy == ChunkingStrategy.PARAGRAPH
        assert config.chunk_size == 512
        assert config.chunk_overlap == 50
        assert config.min_chunk_size == 100
        assert config.max_chunk_size == 2048
        assert config.respect_sentence_boundaries is True
        assert config.respect_paragraph_boundaries is True

    def test_small_chunks_profile(self):
        """Test small chunks configuration profile."""
        config = ChunkingConfig.small_chunks()

        assert config.strategy == ChunkingStrategy.SENTENCE
        assert config.chunk_size == 256
        assert config.chunk_overlap == 25
        assert config.min_chunk_size == 50
        assert config.max_chunk_size == 512
        assert config.respect_sentence_boundaries is True
        assert config.respect_paragraph_boundaries is False

    def test_large_chunks_profile(self):
        """Test large chunks configuration profile."""
        config = ChunkingConfig.large_chunks()

        assert config.strategy == ChunkingStrategy.PARAGRAPH
        assert config.chunk_size == 1024
        assert config.chunk_overlap == 100
        assert config.min_chunk_size == 200
        assert config.max_chunk_size == 4096

    def test_semantic_chunks_profile(self):
        """Test semantic chunks configuration profile."""
        config = ChunkingConfig.semantic_chunks()

        assert config.strategy == ChunkingStrategy.SEMANTIC
        assert config.chunk_size == 512
        assert config.boundary_type == BoundaryType.SENTENCE
        assert config.respect_sentence_boundaries is True

    def test_hierarchical_chunks_profile(self):
        """Test hierarchical chunks configuration profile."""
        config = ChunkingConfig.hierarchical_chunks()

        assert config.strategy == ChunkingStrategy.HIERARCHICAL
        assert config.chunk_size == 768
        assert config.boundary_type == BoundaryType.SECTION
        assert config.respect_section_boundaries is True


class TestChunkingConfigSerialization:
    """Tests for configuration serialization."""

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = ChunkingConfig(
            strategy=ChunkingStrategy.PARAGRAPH,
            chunk_size=512,
            chunk_overlap=50,
        )

        data = config.to_dict()

        assert data["strategy"] == "paragraph"
        assert data["chunk_size"] == 512
        assert data["chunk_overlap"] == 50
        assert data["boundary_type"] == "character"
        assert "min_chunk_size" in data
        assert "max_chunk_size" in data

    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "strategy": "sentence",
            "chunk_size": 256,
            "chunk_overlap": 25,
            "boundary_type": "token",
            "min_chunk_size": 50,
            "max_chunk_size": 512,
        }

        config = ChunkingConfig.from_dict(data)

        assert config.strategy == ChunkingStrategy.SENTENCE
        assert config.chunk_size == 256
        assert config.chunk_overlap == 25
        assert config.boundary_type == BoundaryType.TOKEN

    def test_from_dict_with_defaults(self):
        """Test creating config from partial dictionary."""
        data = {"chunk_size": 300}

        config = ChunkingConfig.from_dict(data)

        assert config.chunk_size == 300
        assert config.strategy == ChunkingStrategy.PARAGRAPH  # Default
        assert config.chunk_overlap == 50  # Default

    def test_roundtrip_serialization(self):
        """Test that config survives to_dict -> from_dict roundtrip."""
        original = ChunkingConfig(
            strategy=ChunkingStrategy.SEMANTIC,
            chunk_size=768,
            chunk_overlap=75,
            metadata_fields=["author", "date"],
        )

        data = original.to_dict()
        restored = ChunkingConfig.from_dict(data)

        assert restored.strategy == original.strategy
        assert restored.chunk_size == original.chunk_size
        assert restored.chunk_overlap == original.chunk_overlap
        assert restored.metadata_fields == original.metadata_fields


class TestChunkingConfigUtilities:
    """Tests for utility methods."""

    def test_validate_chunk_size_valid(self):
        """Test validating a chunk size within bounds."""
        config = ChunkingConfig(min_chunk_size=100, max_chunk_size=1000)

        assert config.validate_chunk_size(500) is True
        assert config.validate_chunk_size(100) is True
        assert config.validate_chunk_size(1000) is True

    def test_validate_chunk_size_invalid(self):
        """Test validating a chunk size outside bounds."""
        config = ChunkingConfig(min_chunk_size=100, max_chunk_size=1000)

        assert config.validate_chunk_size(50) is False
        assert config.validate_chunk_size(1500) is False
        assert config.validate_chunk_size(0) is False

    def test_adjust_for_code_content(self):
        """Test adjusting config for code content."""
        base_config = ChunkingConfig()
        code_config = base_config.adjust_for_content_type("code")

        assert code_config.chunk_overlap < base_config.chunk_overlap
        assert code_config.preserve_formatting is True
        assert code_config.respect_sentence_boundaries is False
        assert code_config.respect_paragraph_boundaries is True

    def test_adjust_for_markdown_content(self):
        """Test adjusting config for markdown content."""
        base_config = ChunkingConfig()
        md_config = base_config.adjust_for_content_type("markdown")

        assert md_config.strategy == ChunkingStrategy.HIERARCHICAL
        assert md_config.boundary_type == BoundaryType.SECTION
        assert md_config.respect_section_boundaries is True

    def test_adjust_for_latex_content(self):
        """Test adjusting config for LaTeX content."""
        base_config = ChunkingConfig()
        latex_config = base_config.adjust_for_content_type("latex")

        assert latex_config.preserve_formatting is True
        assert latex_config.respect_sentence_boundaries is True

    def test_adjust_for_unknown_content(self):
        """Test adjusting config for unknown content type."""
        base_config = ChunkingConfig(metadata_fields=["test"])
        unknown_config = base_config.adjust_for_content_type("unknown")

        # Should return a copy with same settings
        assert unknown_config.strategy == base_config.strategy
        assert unknown_config.chunk_size == base_config.chunk_size
        # But should be a different object
        assert unknown_config is not base_config
        # And should have a copy of the list
        assert unknown_config.metadata_fields is not base_config.metadata_fields


class TestChunkingConfigEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_minimum_valid_config(self):
        """Test creating config with minimum valid values."""
        config = ChunkingConfig(
            chunk_size=2,
            chunk_overlap=0,
            min_chunk_size=1,
            max_chunk_size=2,
        )

        assert config.chunk_size == 2
        assert config.chunk_overlap == 0

    def test_zero_overlap_valid(self):
        """Test that zero overlap is valid."""
        config = ChunkingConfig(chunk_overlap=0)
        assert config.chunk_overlap == 0

    def test_equal_min_max_size(self):
        """Test that min and max size can be equal."""
        config = ChunkingConfig(
            chunk_size=500,
            min_chunk_size=500,
            max_chunk_size=500,
        )

        assert config.min_chunk_size == config.max_chunk_size
        assert config.chunk_size == 500

    def test_metadata_fields_modification(self):
        """Test that metadata_fields can be modified after creation."""
        config = ChunkingConfig()
        config.metadata_fields.append("custom_field")

        assert "custom_field" in config.metadata_fields

    def test_large_chunk_sizes(self):
        """Test with very large chunk sizes."""
        config = ChunkingConfig(
            chunk_size=10000,
            chunk_overlap=1000,
            min_chunk_size=5000,
            max_chunk_size=20000,
        )

        assert config.chunk_size == 10000
        assert config.validate_chunk_size(15000) is True
