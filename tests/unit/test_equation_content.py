"""
Unit tests for EquationContent model

Tests the EquationContent class for proper functionality, validation, and edge cases.
"""

from datetime import UTC, datetime

import pytest

from src.models.base_models import ContentPosition
from src.models.content_elements import (
    ContentElement,
    ContentElementType,
    RelationshipType,
)
from src.models.equation_content import EquationContent


class TestEquationContentInitialization:
    """Test cases for EquationContent initialization."""

    def test_basic_creation_with_latex(self):
        """Test creating a basic equation with LaTeX code."""
        equation = EquationContent(latex_code=r"E = mc^2")

        assert equation.element_type == ContentElementType.EQUATION
        assert equation.latex_code == r"E = mc^2"
        assert equation.rendered_text is None
        assert equation.is_inline is False

    def test_basic_creation_with_rendered_text(self):
        """Test creating equation with rendered text only."""
        equation = EquationContent(rendered_text="E = mc²")

        assert equation.rendered_text == "E = mc²"
        assert equation.latex_code is None

    def test_creation_with_both_representations(self):
        """Test creating equation with both LaTeX and rendered text."""
        equation = EquationContent(latex_code=r"E = mc^2", rendered_text="E = mc²")

        assert equation.latex_code == r"E = mc^2"
        assert equation.rendered_text == "E = mc²"

    def test_creation_without_any_representation_raises_error(self):
        """Test that creating equation without any representation raises ValueError."""
        with pytest.raises(
            ValueError,
            match=r"at least one of latex_code or rendered_text must be provided",
        ):
            EquationContent()

    def test_inline_equation(self):
        """Test creating an inline equation."""
        equation = EquationContent(latex_code=r"x^2", is_inline=True)

        assert equation.is_inline is True
        assert equation.is_display_mode() is False

    def test_display_mode_equation(self):
        """Test creating a display mode equation."""
        equation = EquationContent(
            latex_code=r"\int_0^\infty e^{-x} dx = 1", is_inline=False
        )

        assert equation.is_inline is False
        assert equation.is_display_mode() is True

    def test_numbered_equation(self):
        """Test creating a numbered equation."""
        equation = EquationContent(
            latex_code=r"a^2 + b^2 = c^2", equation_number="3.14"
        )

        assert equation.equation_number == "3.14"
        assert equation.is_numbered() is True

    def test_equation_with_context_before(self):
        """Test equation with context before."""
        equation = EquationContent(
            latex_code=r"F = ma", context_before="Newton's second law states that"
        )

        assert equation.context_before == "Newton's second law states that"
        assert equation.has_context() is True

    def test_equation_with_context_after(self):
        """Test equation with context after."""
        equation = EquationContent(
            latex_code=r"E = mc^2", context_after="is Einstein's famous equation"
        )

        assert equation.context_after == "is Einstein's famous equation"
        assert equation.has_context() is True

    def test_equation_with_both_contexts(self):
        """Test equation with both before and after context."""
        equation = EquationContent(
            latex_code=r"\pi \approx 3.14159",
            context_before="The value of pi",
            context_after="is approximately 3.14159",
        )

        assert equation.context_before == "The value of pi"
        assert equation.context_after == "is approximately 3.14159"
        assert (
            equation.surrounding_context
            == "The value of pi ... is approximately 3.14159"
        )

    def test_equation_with_explicit_surrounding_context(self):
        """Test equation with explicit surrounding_context."""
        equation = EquationContent(
            latex_code=r"x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}",
            surrounding_context="Quadratic formula for solving ax²+bx+c=0",
        )

        assert (
            equation.surrounding_context == "Quadratic formula for solving ax²+bx+c=0"
        )

    def test_equation_with_type(self):
        """Test equation with equation_type."""
        equation = EquationContent(
            latex_code=r"\frac{dy}{dx} = f(x)", equation_type="differential"
        )

        assert equation.equation_type == "differential"

    def test_equation_with_variables(self):
        """Test equation with variables list."""
        equation = EquationContent(
            latex_code=r"y = mx + b", variables=["x", "y", "m", "b"]
        )

        assert equation.variables == ["x", "y", "m", "b"]

    def test_equation_with_constants(self):
        """Test equation with constants list."""
        equation = EquationContent(
            latex_code=r"F = G\frac{m_1 m_2}{r^2}", constants=["G"]
        )

        assert equation.constants == ["G"]

    def test_equation_with_position(self):
        """Test equation with position information."""
        position = ContentPosition(page_number=10, paragraph_index=3)
        equation = EquationContent(
            latex_code=r"\sum_{i=1}^n i = \frac{n(n+1)}{2}", position=position
        )

        assert equation.position == position
        assert equation.position.page_number == 10


class TestEquationContentMethods:
    """Test cases for EquationContent methods."""

    def test_has_latex_code_true(self):
        """Test has_latex_code returns True when LaTeX exists."""
        equation = EquationContent(latex_code=r"a + b = c")
        assert equation.has_latex_code() is True

    def test_has_latex_code_false_none(self):
        """Test has_latex_code returns False when LaTeX is None."""
        equation = EquationContent(rendered_text="a + b = c")
        assert equation.has_latex_code() is False

    def test_has_latex_code_false_empty(self):
        """Test has_latex_code returns False for empty string."""
        equation = EquationContent(latex_code="", rendered_text="text")
        assert equation.has_latex_code() is False

    def test_has_latex_code_false_whitespace(self):
        """Test has_latex_code returns False for whitespace only."""
        equation = EquationContent(latex_code="   ", rendered_text="text")
        assert equation.has_latex_code() is False

    def test_has_rendered_text_true(self):
        """Test has_rendered_text returns True when text exists."""
        equation = EquationContent(rendered_text="x² + y² = r²")
        assert equation.has_rendered_text() is True

    def test_has_rendered_text_false_none(self):
        """Test has_rendered_text returns False when text is None."""
        equation = EquationContent(latex_code=r"x^2")
        assert equation.has_rendered_text() is False

    def test_has_rendered_text_false_empty(self):
        """Test has_rendered_text returns False for empty string."""
        equation = EquationContent(latex_code=r"x^2", rendered_text="")
        assert equation.has_rendered_text() is False

    def test_has_equation_number_true(self):
        """Test has_equation_number returns True when number exists."""
        equation = EquationContent(latex_code=r"x = 1", equation_number="5")
        assert equation.has_equation_number() is True

    def test_has_equation_number_false(self):
        """Test has_equation_number returns False when no number."""
        equation = EquationContent(latex_code=r"x = 1")
        assert equation.has_equation_number() is False

    def test_has_context_with_surrounding(self):
        """Test has_context returns True with surrounding_context."""
        equation = EquationContent(
            latex_code=r"x = 1", surrounding_context="Some context"
        )
        assert equation.has_context() is True

    def test_has_context_with_before(self):
        """Test has_context returns True with context_before."""
        equation = EquationContent(latex_code=r"x = 1", context_before="Before")
        assert equation.has_context() is True

    def test_has_context_with_after(self):
        """Test has_context returns True with context_after."""
        equation = EquationContent(latex_code=r"x = 1", context_after="After")
        assert equation.has_context() is True

    def test_has_context_false(self):
        """Test has_context returns False without any context."""
        equation = EquationContent(latex_code=r"x = 1")
        assert equation.has_context() is False

    def test_get_display_text_prefers_rendered(self):
        """Test get_display_text prefers rendered_text over LaTeX."""
        equation = EquationContent(latex_code=r"x^2", rendered_text="x²")
        assert equation.get_display_text() == "x²"

    def test_get_display_text_falls_back_to_latex(self):
        """Test get_display_text uses LaTeX when no rendered text."""
        equation = EquationContent(latex_code=r"x^2")
        assert equation.get_display_text() == r"x^2"

    def test_get_display_text_empty_when_none(self):
        """Test get_display_text returns empty string when both are None."""
        equation = EquationContent(latex_code="x")
        equation.latex_code = None  # Bypass validation for testing
        assert equation.get_display_text() == ""

    def test_get_full_context_with_all_parts(self):
        """Test get_full_context with before, equation, and after."""
        equation = EquationContent(
            latex_code=r"E = mc^2",
            rendered_text="E = mc²",
            context_before="Einstein's equation",
            context_after="relates energy and mass",
        )

        context = equation.get_full_context()
        assert "Einstein's equation" in context
        assert "[E = mc²]" in context
        assert "relates energy and mass" in context

    def test_get_full_context_with_only_before(self):
        """Test get_full_context with only context_before."""
        equation = EquationContent(latex_code=r"F = ma", context_before="Newton's law")

        context = equation.get_full_context()
        assert "Newton's law" in context
        assert "[" in context  # Should have equation

    def test_get_full_context_with_only_after(self):
        """Test get_full_context with only context_after."""
        equation = EquationContent(
            latex_code=r"a^2 + b^2 = c^2", context_after="is the Pythagorean theorem"
        )

        context = equation.get_full_context()
        assert "is the Pythagorean theorem" in context

    def test_get_full_context_empty(self):
        """Test get_full_context returns empty when no context."""
        equation = EquationContent(latex_code=r"x = 1")
        equation.context_before = None
        equation.context_after = None

        # Should still have equation representation
        context = equation.get_full_context()
        assert "[" in context

    def test_set_context_before(self):
        """Test set_context for context_before."""
        equation = EquationContent(latex_code=r"x = 1")
        equation.set_context(before="New before text")

        assert equation.context_before == "New before text"
        assert "New before text" in equation.surrounding_context

    def test_set_context_after(self):
        """Test set_context for context_after."""
        equation = EquationContent(latex_code=r"x = 1")
        equation.set_context(after="New after text")

        assert equation.context_after == "New after text"
        assert "New after text" in equation.surrounding_context

    def test_set_context_both(self):
        """Test set_context for both before and after."""
        equation = EquationContent(latex_code=r"x = 1")
        equation.set_context(before="Before", after="After")

        assert equation.context_before == "Before"
        assert equation.context_after == "After"
        assert equation.surrounding_context == "Before ... After"

    def test_set_context_updates_surrounding(self):
        """Test that set_context properly updates surrounding_context."""
        equation = EquationContent(latex_code=r"x = 1", context_before="Old before")

        equation.set_context(before="New before", after="New after")
        assert equation.surrounding_context == "New before ... New after"

    def test_extract_variables_simple(self):
        """Test extract_variables with simple equation."""
        equation = EquationContent(latex_code=r"y = mx + b")
        variables = equation.extract_variables()

        assert "x" in variables or "y" in variables  # Should find at least some

    def test_extract_variables_no_latex(self):
        """Test extract_variables returns empty list without LaTeX."""
        equation = EquationContent(rendered_text="x = 1")
        variables = equation.extract_variables()

        assert variables == []

    def test_extract_variables_uses_existing_list(self):
        """Test extract_variables returns copy of existing variables list."""
        equation = EquationContent(latex_code=r"E = mc^2", variables=["E", "m", "c"])

        variables = equation.extract_variables()
        assert variables == ["E", "m", "c"]

        # Verify it's a copy
        variables.append("x")
        assert "x" not in equation.variables


class TestEquationContentSerialization:
    """Test cases for equation serialization."""

    def test_to_dict_basic(self):
        """Test basic to_dict conversion."""
        equation = EquationContent(
            latex_code=r"x^2 + y^2 = r^2",
            rendered_text="x² + y² = r²",
            equation_number="1",
        )

        result = equation.to_dict()

        assert result["element_type"] == "equation"
        assert result["latex_code"] == r"x^2 + y^2 = r^2"
        assert result["rendered_text"] == "x² + y² = r²"
        assert result["equation_number"] == "1"
        assert result["has_latex_code"] is True
        assert result["has_rendered_text"] is True
        assert result["is_numbered"] is True

    def test_to_dict_with_context(self):
        """Test to_dict with context information."""
        equation = EquationContent(
            latex_code=r"F = ma",
            context_before="Newton's second law",
            context_after="relates force, mass, and acceleration",
        )

        result = equation.to_dict()

        assert result["context_before"] == "Newton's second law"
        assert result["context_after"] == "relates force, mass, and acceleration"
        assert "Newton's second law" in result["surrounding_context"]

    def test_to_dict_inline_equation(self):
        """Test to_dict for inline equation."""
        equation = EquationContent(latex_code=r"e^{i\pi} + 1 = 0", is_inline=True)

        result = equation.to_dict()
        assert result["is_inline"] is True

    def test_to_dict_with_variables(self):
        """Test to_dict with variables and constants."""
        equation = EquationContent(
            latex_code=r"F = G\frac{m_1 m_2}{r^2}",
            variables=["F", "m_1", "m_2", "r"],
            constants=["G"],
        )

        result = equation.to_dict()
        assert result["variables"] == ["F", "m_1", "m_2", "r"]
        assert result["constants"] == ["G"]

    def test_repr_basic(self):
        """Test __repr__ for basic equation."""
        equation = EquationContent(
            latex_code=r"E = mc^2", rendered_text="E = mc²", equation_number="1"
        )

        repr_str = repr(equation)
        assert "EquationContent" in repr_str
        assert "E = mc²" in repr_str
        assert "#1" in repr_str

    def test_repr_inline(self):
        """Test __repr__ shows inline mode."""
        equation = EquationContent(latex_code=r"x^2", is_inline=True)

        repr_str = repr(equation)
        assert "inline" in repr_str

    def test_repr_display_mode(self):
        """Test __repr__ shows display mode."""
        equation = EquationContent(latex_code=r"\int x dx", is_inline=False)

        repr_str = repr(equation)
        assert "display" in repr_str

    def test_repr_unnumbered(self):
        """Test __repr__ shows unnumbered for equations without number."""
        equation = EquationContent(latex_code=r"x = 1")

        repr_str = repr(equation)
        assert "unnumbered" in repr_str

    def test_repr_long_equation(self):
        """Test __repr__ truncates long equations."""
        long_latex = r"\sum_{i=1}^{n} \int_0^\infty e^{-x^2} \frac{1}{\sqrt{2\pi}} dx"
        equation = EquationContent(latex_code=long_latex)

        repr_str = repr(equation)
        assert "..." in repr_str  # Should be truncated


class TestEquationContentEdgeCases:
    """Test cases for edge cases and special scenarios."""

    def test_equation_with_unicode_latex(self):
        """Test equation with unicode characters in LaTeX."""
        equation = EquationContent(
            latex_code=r"\alpha + \beta = \gamma", rendered_text="alpha + beta = gamma"
        )

        assert equation.latex_code == r"\alpha + \beta = \gamma"
        assert equation.rendered_text == "alpha + beta = gamma"

    def test_equation_with_very_long_latex(self):
        """Test equation with very long LaTeX code."""
        long_latex = r"\frac{" + "x + " * 100 + r"1}{y}"
        equation = EquationContent(latex_code=long_latex)

        assert len(equation.latex_code) > 100
        assert equation.has_latex_code() is True

    def test_equation_with_empty_strings(self):
        """Test equation with empty string contexts."""
        equation = EquationContent(
            latex_code=r"x = 1", context_before="", context_after=""
        )

        # Empty strings should not create surrounding_context
        assert equation.surrounding_context == ""

    def test_equation_with_whitespace_contexts(self):
        """Test equation with whitespace-only contexts."""
        equation = EquationContent(
            latex_code=r"x = 1", context_before="   ", context_after="   "
        )

        # Whitespace should be stripped
        assert equation.surrounding_context.strip() == "..."

    def test_equation_number_as_string(self):
        """Test equation with various number formats."""
        # Simple number
        eq1 = EquationContent(latex_code=r"x = 1", equation_number="5")
        assert eq1.equation_number == "5"

        # Decimal number
        eq2 = EquationContent(latex_code=r"x = 1", equation_number="3.14")
        assert eq2.equation_number == "3.14"

        # Letter label
        eq3 = EquationContent(latex_code=r"x = 1", equation_number="A")
        assert eq3.equation_number == "A"

    def test_equation_with_special_latex_characters(self):
        """Test equation with special LaTeX characters."""
        equation = EquationContent(
            latex_code=r"\left\{\begin{matrix} x \\ y \end{matrix}\right\}"
        )

        assert r"\left\{" in equation.latex_code
        assert r"\right\}" in equation.latex_code

    def test_surrounding_context_with_newlines(self):
        """Test equation with newlines in context."""
        equation = EquationContent(
            latex_code=r"x = 1",
            context_before="Line 1\nLine 2",
            context_after="Line 3\nLine 4",
        )

        assert equation.context_before == "Line 1\nLine 2"
        assert equation.context_after == "Line 3\nLine 4"

    def test_equation_type_custom_values(self):
        """Test equation with various equation_type values."""
        types = ["algebraic", "differential", "integral", "matrix", "system"]

        for eq_type in types:
            equation = EquationContent(latex_code=r"x = 1", equation_type=eq_type)
            assert equation.equation_type == eq_type


class TestEquationContentInheritance:
    """Test cases verifying ContentElement inheritance."""

    def test_equation_inherits_from_content_element(self):
        """Test that EquationContent inherits ContentElement features."""
        equation = EquationContent(latex_code=r"x = 1")
        assert isinstance(equation, ContentElement)

    def test_equation_has_content_element_attributes(self):
        """Test that equation has all ContentElement attributes."""
        equation = EquationContent(
            latex_code=r"x = 1", confidence=0.98, metadata={"source": "pdf"}
        )

        # ContentElement attributes
        assert hasattr(equation, "id")
        assert hasattr(equation, "element_type")
        assert hasattr(equation, "position")
        assert hasattr(equation, "metadata")
        assert hasattr(equation, "confidence")
        assert hasattr(equation, "created_at")

        # Check values
        assert equation.element_type == ContentElementType.EQUATION
        assert equation.confidence == 0.98
        assert equation.metadata["source"] == "pdf"

    def test_equation_relationships_from_base(self):
        """Test that equation can use ContentElement relationship methods."""
        equation = EquationContent(latex_code=r"x = 1")

        # Add a relationship using ContentElement method
        equation.add_relationship(
            target_id="text_456",
            relationship_type=RelationshipType.REFERENCE,
            confidence=0.9,
        )

        assert len(equation.relationships) == 1
        assert equation.has_relationship("text_456")

    def test_equation_created_at_timestamp(self):
        """Test that equation has creation timestamp."""
        equation = EquationContent(latex_code=r"x = 1")

        assert equation.created_at is not None
        assert isinstance(equation.created_at, datetime)
        assert equation.created_at.tzinfo == UTC

    def test_equation_to_dict_includes_base_fields(self):
        """Test that to_dict includes ContentElement fields."""
        equation = EquationContent(latex_code=r"x = 1", metadata={"page": 5})

        result = equation.to_dict()

        # Base fields from ContentElement
        assert "id" in result
        assert "element_type" in result
        assert "confidence" in result
        assert "created_at" in result
        assert "metadata" in result

        # Equation-specific fields
        assert "latex_code" in result
        assert "rendered_text" in result
