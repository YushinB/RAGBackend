"""
Equation Content Model

This module defines the EquationContent class for handling mathematical equations
extracted from documents. EquationContent inherits from ContentElement and adds
equation-specific attributes and functionality.
"""

from dataclasses import dataclass

from .content_elements import ContentElement, ContentElementType


@dataclass
class EquationContent(ContentElement):
    """
    Represents a mathematical equation content element extracted from a document.

    This class extends ContentElement to handle equation-specific data including
    LaTeX code, rendered text, numbering, and surrounding context.

    Attributes:
        latex_code: LaTeX representation of the equation
        rendered_text: Plain text or MathML rendered version
        equation_number: Equation number/label in document (e.g., "1", "3.2")
        is_inline: Whether equation is inline (True) or display mode (False)
        surrounding_context: Text surrounding the equation for context
        context_before: Text appearing before the equation
        context_after: Text appearing after the equation
        equation_type: Type of equation (e.g., 'algebraic', 'differential', 'matrix')
        variables: List of variables used in the equation
        constants: List of constants used in the equation

    Inherits from ContentElement:
        id: Unique identifier
        element_type: Automatically set to ContentElementType.EQUATION
        position: Position in the document
        metadata: Additional metadata
        relationships: Relationships to other elements
        confidence: Extraction confidence score
        created_at: Creation timestamp
        source_document: Source document identifier

    Example:
        >>> equation = EquationContent(
        ...     latex_code=r"E = mc^2",
        ...     rendered_text="E = mc²",
        ...     equation_number="1",
        ...     is_inline=False,
        ...     context_before="Einstein's famous equation",
        ...     position=ContentPosition(page_number=42)
        ... )
        >>> equation.has_latex_code()
        True
    """

    # Equation-specific attributes
    latex_code: str | None = None
    rendered_text: str | None = None
    equation_number: str | None = None
    is_inline: bool = False
    surrounding_context: str | None = None
    context_before: str | None = None
    context_after: str | None = None
    equation_type: str | None = None
    variables: list[str] | None = None
    constants: list[str] | None = None

    def __post_init__(self) -> None:
        """Initialize and validate equation content after creation."""
        # Set element type to EQUATION
        self.element_type = ContentElementType.EQUATION

        # Call parent validation
        super().__post_init__()

        # Validate that at least one representation exists
        if not self.latex_code and not self.rendered_text:
            raise ValueError(
                "at least one of latex_code or rendered_text must be provided"
            )

        # Build surrounding_context if not provided but context_before/after exist
        if self.surrounding_context is None:
            if self.context_before is not None or self.context_after is not None:
                parts = []
                if self.context_before:
                    parts.append(self.context_before.strip())
                if self.context_after:
                    parts.append(self.context_after.strip())
                self.surrounding_context = " ... ".join(parts)

    def has_latex_code(self) -> bool:
        """
        Check if the equation has LaTeX code.

        Returns:
            True if latex_code exists and is non-empty, False otherwise
        """
        return bool(self.latex_code and self.latex_code.strip())

    def has_rendered_text(self) -> bool:
        """
        Check if the equation has rendered text.

        Returns:
            True if rendered_text exists and is non-empty, False otherwise
        """
        return bool(self.rendered_text and self.rendered_text.strip())

    def has_equation_number(self) -> bool:
        """
        Check if the equation has a number/label.

        Returns:
            True if equation_number exists and is non-empty, False otherwise
        """
        return bool(self.equation_number and self.equation_number.strip())

    def has_context(self) -> bool:
        """
        Check if the equation has surrounding context.

        Returns:
            True if any context exists, False otherwise
        """
        return bool(
            self.surrounding_context
            or self.context_before
            or self.context_after
        )

    def get_full_context(self) -> str:
        """
        Get the full context including before, equation, and after.

        Returns:
            String with full context, including the equation representation
        """
        parts = []

        if self.context_before:
            parts.append(self.context_before.strip())

        # Add equation representation
        if self.rendered_text:
            parts.append(f"[{self.rendered_text}]")
        elif self.latex_code:
            parts.append(f"[${self.latex_code}$]")

        if self.context_after:
            parts.append(self.context_after.strip())

        return " ".join(parts) if parts else ""

    def get_display_text(self) -> str:
        """
        Get the best available text representation of the equation.

        Returns:
            Rendered text if available, otherwise LaTeX code, or empty string
        """
        if self.rendered_text:
            return self.rendered_text
        if self.latex_code:
            return self.latex_code
        return ""

    def extract_variables(self) -> list[str]:
        """
        Extract variable names from LaTeX code.

        This is a simple extraction that looks for single letters in the LaTeX.
        Returns existing variables list if already populated.

        Returns:
            List of unique variable names found in the equation
        """
        if self.variables is not None:
            return self.variables.copy()

        if not self.latex_code:
            return []

        # Simple variable extraction: single letters (a-z, A-Z)
        import re

        # Match single letters that are likely variables
        # Exclude common LaTeX commands
        pattern = r'\b([a-zA-Z])\b'
        matches = re.findall(pattern, self.latex_code)

        # Remove common LaTeX keywords
        latex_keywords = {
            'e', 'i', 'n', 'x', 'y', 'z',  # Keep these as they're often variables
        }
        variables = sorted(set(m for m in matches if len(m) == 1))

        return variables

    def is_numbered(self) -> bool:
        """
        Check if this is a numbered equation.

        Returns:
            True if equation has a number, False otherwise
        """
        return self.has_equation_number()

    def is_display_mode(self) -> bool:
        """
        Check if this is a display mode equation (not inline).

        Returns:
            True if equation is in display mode, False if inline
        """
        return not self.is_inline

    def set_context(
        self,
        before: str | None = None,
        after: str | None = None
    ) -> None:
        """
        Set the surrounding context for the equation.

        Args:
            before: Text appearing before the equation
            after: Text appearing after the equation
        """
        if before is not None:
            self.context_before = before

        if after is not None:
            self.context_after = after

        # Rebuild surrounding_context
        if self.context_before or self.context_after:
            parts = []
            if self.context_before:
                parts.append(self.context_before.strip())
            if self.context_after:
                parts.append(self.context_after.strip())
            self.surrounding_context = " ... ".join(parts)

    def to_dict(self) -> dict[str, any]:
        """
        Convert equation content to dictionary format.

        Returns:
            Dictionary representation of the equation content
        """
        base_dict = super().to_dict()

        # Add equation-specific fields
        equation_dict = {
            "latex_code": self.latex_code,
            "rendered_text": self.rendered_text,
            "equation_number": self.equation_number,
            "is_inline": self.is_inline,
            "surrounding_context": self.surrounding_context,
            "context_before": self.context_before,
            "context_after": self.context_after,
            "equation_type": self.equation_type,
            "variables": self.variables,
            "constants": self.constants,
            "has_latex_code": self.has_latex_code(),
            "has_rendered_text": self.has_rendered_text(),
            "is_numbered": self.is_numbered(),
        }

        # Merge with base dictionary
        base_dict.update(equation_dict)
        return base_dict

    def __repr__(self) -> str:
        """
        Return a string representation of the EquationContent.

        Returns:
            String representation with key attributes
        """
        display_text = self.get_display_text()
        text_preview = (
            f'"{display_text[:40]}..."'
            if len(display_text) > 40
            else f'"{display_text}"'
        )

        mode = "inline" if self.is_inline else "display"
        number = f"#{self.equation_number}" if self.equation_number else "unnumbered"

        return (
            f"EquationContent(id={self.id[:8]}..., {text_preview}, "
            f"mode={mode}, {number})"
        )
