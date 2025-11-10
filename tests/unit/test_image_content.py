"""
Unit Tests for ImageContent Class

Tests for:
- ImageContent initialization and validation
- Image format detection from magic bytes
- Image data handling and methods
- Caption and alt_text functionality
- Dimension management
- Serialization and representation
"""

import pytest

from src.models.base_models import ContentPosition
from src.models.content_elements import ContentElementType, RelationshipType
from src.models.image_content import ImageContent


class TestImageContentInitialization:
    """Tests for ImageContent initialization."""

    def test_basic_creation(self):
        """Test basic image content creation."""
        image = ImageContent()
        assert image.element_type == ContentElementType.IMAGE
        assert image.image_data is None
        assert image.caption is None
        assert image.alt_text is None
        assert image.image_format is None
        assert image.width is None
        assert image.height is None

    def test_with_image_data(self):
        """Test creation with image data."""
        data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        image = ImageContent(image_data=data)
        assert image.image_data == data
        assert image.size_bytes == len(data)

    def test_with_caption(self):
        """Test creation with caption."""
        image = ImageContent(caption="Figure 1: Architecture Diagram")
        assert image.caption == "Figure 1: Architecture Diagram"

    def test_with_alt_text(self):
        """Test creation with alternative text."""
        image = ImageContent(alt_text="Diagram showing system components")
        assert image.alt_text == "Diagram showing system components"

    def test_with_position(self):
        """Test creation with position."""
        position = ContentPosition(page_number=5, paragraph_index=2)
        image = ImageContent(position=position)
        assert image.position == position

    def test_with_dimensions(self):
        """Test creation with width and height."""
        image = ImageContent(width=800, height=600)
        assert image.width == 800
        assert image.height == 600

    def test_with_file_path(self):
        """Test creation with file path."""
        image = ImageContent(file_path="/path/to/image.png")
        assert image.file_path == "/path/to/image.png"

    def test_size_bytes_auto_calculated(self):
        """Test that size_bytes is automatically calculated from image_data."""
        data = b"test image data"
        image = ImageContent(image_data=data)
        assert image.size_bytes == len(data)

    def test_size_bytes_manual_override(self):
        """Test that manual size_bytes is preserved."""
        data = b"test data"
        image = ImageContent(image_data=data, size_bytes=100)
        assert image.size_bytes == 100  # Manual value preserved

    def test_negative_width_raises_error(self):
        """Test that negative width raises ValueError."""
        with pytest.raises(ValueError, match="width must be positive"):
            ImageContent(width=-100)

    def test_zero_width_raises_error(self):
        """Test that zero width raises ValueError."""
        with pytest.raises(ValueError, match="width must be positive"):
            ImageContent(width=0)

    def test_negative_height_raises_error(self):
        """Test that negative height raises ValueError."""
        with pytest.raises(ValueError, match="height must be positive"):
            ImageContent(height=-100)

    def test_zero_height_raises_error(self):
        """Test that zero height raises ValueError."""
        with pytest.raises(ValueError, match="height must be positive"):
            ImageContent(height=0)

    def test_negative_size_bytes_raises_error(self):
        """Test that negative size_bytes raises ValueError."""
        with pytest.raises(ValueError, match="size_bytes must be non-negative"):
            ImageContent(size_bytes=-100)


class TestImageFormatDetection:
    """Tests for image format detection."""

    def test_detect_png_format(self):
        """Test PNG format detection."""
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        image = ImageContent(image_data=png_header)
        assert image.image_format == "PNG"

    def test_detect_jpeg_format(self):
        """Test JPEG format detection."""
        jpeg_header = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        image = ImageContent(image_data=jpeg_header)
        assert image.image_format == "JPEG"

    def test_detect_gif87a_format(self):
        """Test GIF87a format detection."""
        gif_header = b"GIF87a" + b"\x00" * 100
        image = ImageContent(image_data=gif_header)
        assert image.image_format == "GIF"

    def test_detect_gif89a_format(self):
        """Test GIF89a format detection."""
        gif_header = b"GIF89a" + b"\x00" * 100
        image = ImageContent(image_data=gif_header)
        assert image.image_format == "GIF"

    def test_detect_bmp_format(self):
        """Test BMP format detection."""
        bmp_header = b"BM" + b"\x00" * 100
        image = ImageContent(image_data=bmp_header)
        assert image.image_format == "BMP"

    def test_detect_tiff_little_endian_format(self):
        """Test TIFF little-endian format detection."""
        tiff_header = b"II*\x00" + b"\x00" * 100
        image = ImageContent(image_data=tiff_header)
        assert image.image_format == "TIFF"

    def test_detect_tiff_big_endian_format(self):
        """Test TIFF big-endian format detection."""
        tiff_header = b"MM\x00*" + b"\x00" * 100
        image = ImageContent(image_data=tiff_header)
        assert image.image_format == "TIFF"

    def test_detect_webp_format(self):
        """Test WebP format detection."""
        webp_header = b"RIFF" + b"\x00" * 4 + b"WEBP" + b"\x00" * 100
        image = ImageContent(image_data=webp_header)
        assert image.image_format == "WEBP"

    def test_detect_ico_format(self):
        """Test ICO format detection."""
        ico_header = b"\x00\x00\x01\x00" + b"\x00" * 100
        image = ImageContent(image_data=ico_header)
        assert image.image_format == "ICO"

    def test_detect_format_unknown(self):
        """Test that unknown format returns None."""
        unknown_data = b"UNKNOWN" + b"\x00" * 100
        image = ImageContent(image_data=unknown_data)
        assert image.image_format is None

    def test_detect_format_no_data(self):
        """Test format detection with no image data."""
        image = ImageContent()
        assert image.detect_format() is None

    def test_detect_format_insufficient_data(self):
        """Test format detection with insufficient data."""
        small_data = b"PNG"  # Too short
        image = ImageContent(image_data=small_data)
        assert image.image_format is None

    def test_manual_format_preserved(self):
        """Test that manually set format is not overwritten."""
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        image = ImageContent(image_data=png_data, image_format="CUSTOM")
        assert image.image_format == "CUSTOM"


class TestImageContentMethods:
    """Tests for ImageContent helper methods."""

    def test_has_caption_true(self):
        """Test has_caption returns True when caption exists."""
        image = ImageContent(caption="Test caption")
        assert image.has_caption()

    def test_has_caption_false_none(self):
        """Test has_caption returns False when caption is None."""
        image = ImageContent()
        assert not image.has_caption()

    def test_has_caption_false_empty(self):
        """Test has_caption returns False when caption is empty."""
        image = ImageContent(caption="")
        assert not image.has_caption()

    def test_has_caption_false_whitespace(self):
        """Test has_caption returns False when caption is only whitespace."""
        image = ImageContent(caption="   ")
        assert not image.has_caption()

    def test_has_alt_text_true(self):
        """Test has_alt_text returns True when alt_text exists."""
        image = ImageContent(alt_text="Alternative description")
        assert image.has_alt_text()

    def test_has_alt_text_false_none(self):
        """Test has_alt_text returns False when alt_text is None."""
        image = ImageContent()
        assert not image.has_alt_text()

    def test_has_alt_text_false_empty(self):
        """Test has_alt_text returns False when alt_text is empty."""
        image = ImageContent(alt_text="")
        assert not image.has_alt_text()

    def test_has_alt_text_false_whitespace(self):
        """Test has_alt_text returns False when alt_text is only whitespace."""
        image = ImageContent(alt_text="   ")
        assert not image.has_alt_text()

    def test_has_image_data_true(self):
        """Test has_image_data returns True when data exists."""
        image = ImageContent(image_data=b"test data")
        assert image.has_image_data()

    def test_has_image_data_false_none(self):
        """Test has_image_data returns False when data is None."""
        image = ImageContent()
        assert not image.has_image_data()

    def test_has_image_data_false_empty(self):
        """Test has_image_data returns False when data is empty."""
        image = ImageContent(image_data=b"")
        assert not image.has_image_data()

    def test_get_dimensions_with_values(self):
        """Test get_dimensions returns tuple with values."""
        image = ImageContent(width=1920, height=1080)
        assert image.get_dimensions() == (1920, 1080)

    def test_get_dimensions_none_values(self):
        """Test get_dimensions returns tuple with None values."""
        image = ImageContent()
        assert image.get_dimensions() == (None, None)

    def test_get_dimensions_partial_values(self):
        """Test get_dimensions with only one dimension set."""
        image = ImageContent(width=800)
        assert image.get_dimensions() == (800, None)

    def test_set_dimensions_valid(self):
        """Test set_dimensions with valid values."""
        image = ImageContent()
        image.set_dimensions(1024, 768)
        assert image.width == 1024
        assert image.height == 768

    def test_set_dimensions_negative_width_raises_error(self):
        """Test set_dimensions raises error for negative width."""
        image = ImageContent()
        with pytest.raises(ValueError, match="width must be positive"):
            image.set_dimensions(-100, 768)

    def test_set_dimensions_zero_width_raises_error(self):
        """Test set_dimensions raises error for zero width."""
        image = ImageContent()
        with pytest.raises(ValueError, match="width must be positive"):
            image.set_dimensions(0, 768)

    def test_set_dimensions_negative_height_raises_error(self):
        """Test set_dimensions raises error for negative height."""
        image = ImageContent()
        with pytest.raises(ValueError, match="height must be positive"):
            image.set_dimensions(1024, -768)

    def test_set_dimensions_zero_height_raises_error(self):
        """Test set_dimensions raises error for zero height."""
        image = ImageContent()
        with pytest.raises(ValueError, match="height must be positive"):
            image.set_dimensions(1024, 0)

    def test_clear_image_data(self):
        """Test clearing image data."""
        image = ImageContent(image_data=b"test data" * 1000)
        assert image.has_image_data()

        image.clear_image_data()
        assert not image.has_image_data()
        assert image.size_bytes == 0

    def test_clear_image_data_preserves_metadata(self):
        """Test that clearing image data preserves other metadata."""
        image = ImageContent(
            image_data=b"test data",
            caption="Test caption",
            alt_text="Test alt text",
            width=800,
            height=600,
        )

        image.clear_image_data()

        assert image.caption == "Test caption"
        assert image.alt_text == "Test alt text"
        assert image.width == 800
        assert image.height == 600


class TestImageContentSerialization:
    """Tests for ImageContent serialization methods."""

    def test_to_dict_basic(self):
        """Test basic to_dict conversion."""
        image = ImageContent(caption="Test")
        result = image.to_dict()

        assert result["element_type"] == "image"
        assert result["caption"] == "Test"
        assert "image_data" not in result  # Should not include binary data
        assert "has_image_data" in result

    def test_to_dict_with_image_data(self):
        """Test to_dict indicates presence of image data."""
        image = ImageContent(image_data=b"test data")
        result = image.to_dict()

        assert result["has_image_data"] is True
        assert result["size_bytes"] == 9
        assert "image_data" not in result

    def test_to_dict_without_image_data(self):
        """Test to_dict indicates absence of image data."""
        image = ImageContent()
        result = image.to_dict()

        assert result["has_image_data"] is False

    def test_to_dict_all_fields(self):
        """Test to_dict with all fields populated."""
        position = ContentPosition(page_number=5)
        image = ImageContent(
            caption="Figure 1",
            alt_text="Diagram",
            width=1920,
            height=1080,
            image_format="PNG",
            file_path="/path/to/image.png",
            position=position,
        )
        result = image.to_dict()

        assert result["caption"] == "Figure 1"
        assert result["alt_text"] == "Diagram"
        assert result["width"] == 1920
        assert result["height"] == 1080
        assert result["image_format"] == "PNG"
        assert result["file_path"] == "/path/to/image.png"
        assert result["position"]["page_number"] == 5

    def test_repr_basic(self):
        """Test __repr__ with basic image."""
        image = ImageContent()
        repr_str = repr(image)

        assert "ImageContent" in repr_str
        assert "format=None" in repr_str
        assert "dims=unknown" in repr_str
        assert "has_data=False" in repr_str

    def test_repr_with_dimensions(self):
        """Test __repr__ with dimensions."""
        image = ImageContent(width=800, height=600)
        repr_str = repr(image)

        assert "dims=800x600" in repr_str

    def test_repr_with_caption_short(self):
        """Test __repr__ with short caption."""
        image = ImageContent(caption="Short caption")
        repr_str = repr(image)

        assert 'caption="Short caption"' in repr_str

    def test_repr_with_caption_long(self):
        """Test __repr__ with long caption that gets truncated."""
        long_caption = (
            "This is a very long caption that should be truncated in the representation"
        )
        image = ImageContent(caption=long_caption)
        repr_str = repr(image)

        assert "caption=" in repr_str
        assert "..." in repr_str  # Truncation indicator
        assert len(long_caption) > 30  # Ensure it's actually long

    def test_repr_with_format_and_data(self):
        """Test __repr__ with format and data."""
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        image = ImageContent(image_data=png_data)
        repr_str = repr(image)

        assert "format=PNG" in repr_str
        assert "has_data=True" in repr_str


class TestImageContentInheritance:
    """Tests for inherited ContentElement functionality."""

    def test_inherits_from_content_element(self):
        """Test that ImageContent properly inherits from ContentElement."""
        image = ImageContent()
        assert hasattr(image, "id")
        assert hasattr(image, "metadata")
        assert hasattr(image, "relationships")
        assert hasattr(image, "confidence")

    def test_add_relationship(self):
        """Test adding relationships to image."""
        image = ImageContent(caption="Figure 1")
        rel = image.add_relationship("caption-id", RelationshipType.CAPTION)

        assert len(image.relationships) == 1
        assert rel.source_id == image.id
        assert rel.target_id == "caption-id"

    def test_metadata_storage(self):
        """Test storing metadata in image."""
        metadata = {"source": "screenshot", "dpi": 300}
        image = ImageContent(metadata=metadata)

        assert image.metadata == metadata

    def test_confidence_score(self):
        """Test confidence score on image."""
        image = ImageContent(confidence=0.95)
        assert image.confidence == 0.95
        assert image.is_high_confidence()

    def test_position_tracking(self):
        """Test position tracking for image."""
        position = ContentPosition(
            page_number=10, paragraph_index=5, bbox=(100.0, 200.0, 300.0, 400.0)
        )
        image = ImageContent(position=position)

        assert image.position.page_number == 10
        assert image.position.paragraph_index == 5
        assert image.position.bbox == (100.0, 200.0, 300.0, 400.0)


class TestImageContentEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_caption_string(self):
        """Test behavior with empty caption string."""
        image = ImageContent(caption="")
        assert not image.has_caption()

    def test_whitespace_only_alt_text(self):
        """Test behavior with whitespace-only alt text."""
        image = ImageContent(alt_text="   \n\t  ")
        assert not image.has_alt_text()

    def test_very_large_dimensions(self):
        """Test handling of very large dimension values."""
        image = ImageContent(width=100000, height=100000)
        assert image.width == 100000
        assert image.height == 100000

    def test_format_case_preservation(self):
        """Test that manually set format preserves case."""
        image = ImageContent(image_format="jpeg")
        assert image.image_format == "jpeg"  # Case preserved

    def test_multiple_clear_image_data_calls(self):
        """Test calling clear_image_data multiple times."""
        image = ImageContent(image_data=b"test")
        image.clear_image_data()
        image.clear_image_data()  # Should not raise error
        assert image.size_bytes == 0

    def test_unicode_caption(self):
        """Test caption with unicode characters."""
        image = ImageContent(caption="图像标题 - 系统架构图")
        assert image.has_caption()
        assert "系统架构图" in image.caption

    def test_file_path_with_spaces(self):
        """Test file path with spaces and special characters."""
        path = "/path/to/My Documents/image file (1).png"
        image = ImageContent(file_path=path)
        assert image.file_path == path
