"""
Code Style Validator for RAG Backend

This module validates that generated code follows the project's coding conventions
as defined in .pre-commit-config.yaml and pyproject.toml.
"""

import ast
import contextlib
import re
import subprocess  # nosec B404 - controlled environment usage
import tempfile
from pathlib import Path
from typing import NamedTuple


class StyleViolation(NamedTuple):
    """Represents a coding style violation."""

    file_path: str
    line: int
    column: int
    tool: str
    code: str
    message: str
    severity: str = "error"


class CodeStyleValidator:
    """Validates code against project coding conventions."""

    def __init__(self, project_root: Path | None = None):
        """
        Initialize the code style validator.

        Args:
            project_root: Path to project root (auto-detected if None)
        """
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.pyproject_path = self.project_root / "pyproject.toml"
        self.precommit_path = self.project_root / ".pre-commit-config.yaml"

    def validate_code(
        self, code: str, file_path: str = "generated.py"
    ) -> list[StyleViolation]:
        """
        Validate Python code against all style rules.

        Args:
            code: Python code to validate
            file_path: Virtual file path for context

        Returns:
            List of style violations found
        """
        violations = []

        # Create temporary file for validation
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write(code)
            temp_path = Path(temp_file.name)

        try:
            # Run all validation checks
            violations.extend(self._check_syntax(code, file_path))
            violations.extend(self._check_black_formatting(temp_path, file_path))
            violations.extend(self._check_ruff_linting(temp_path, file_path))
            violations.extend(self._check_mypy_typing(temp_path, file_path))
            violations.extend(self._check_import_sorting(temp_path, file_path))
            violations.extend(self._check_security(temp_path, file_path))
            violations.extend(self._check_custom_conventions(code, file_path))

        finally:
            # Cleanup
            temp_path.unlink(missing_ok=True)

        return violations

    def _check_syntax(self, code: str, file_path: str) -> list[StyleViolation]:
        """Check Python syntax."""
        violations = []

        try:
            ast.parse(code)
        except SyntaxError as e:
            violations.append(
                StyleViolation(
                    file_path=file_path,
                    line=e.lineno or 1,
                    column=e.offset or 1,
                    tool="python",
                    code="E999",
                    message=f"Syntax error: {e.msg}",
                    severity="error",
                )
            )

        return violations

    def _check_black_formatting(
        self, temp_path: Path, file_path: str
    ) -> list[StyleViolation]:
        """Check Black code formatting."""
        violations = []

        try:
            result = subprocess.run(  # nosec B603 B607 - controlled environment
                ["black", "--check", "--line-length=88", str(temp_path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                violations.append(
                    StyleViolation(
                        file_path=file_path,
                        line=1,
                        column=1,
                        tool="black",
                        code="BLACK001",
                        message="Code is not Black formatted (line length 88)",
                        severity="error",
                    )
                )

        except (subprocess.TimeoutExpired, FileNotFoundError):
            violations.append(
                StyleViolation(
                    file_path=file_path,
                    line=1,
                    column=1,
                    tool="black",
                    code="BLACK000",
                    message="Black formatter not available or timed out",
                    severity="warning",
                )
            )

        return violations

    def _check_ruff_linting(
        self, temp_path: Path, file_path: str
    ) -> list[StyleViolation]:
        """Check Ruff linting."""
        violations = []

        try:
            result = subprocess.run(  # nosec B603 B607 - controlled environment
                ["ruff", "check", "--line-length=88", str(temp_path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                # Parse Ruff output
                for line in result.stdout.splitlines():
                    if ":" in line and any(
                        code in line
                        for code in ["E", "W", "F", "I", "B", "C", "UP", "S"]
                    ):
                        parts = line.split(":", 3)
                        if len(parts) >= 3:
                            try:
                                line_num = int(parts[1])
                                col_num = int(parts[2]) if parts[2].isdigit() else 1
                                message = (
                                    parts[3].strip()
                                    if len(parts) > 3
                                    else "Ruff violation"
                                )

                                # Extract error code
                                code_match = re.search(r"([A-Z]\d+)", message)
                                error_code = (
                                    code_match.group(1) if code_match else "RUFF001"
                                )

                                violations.append(
                                    StyleViolation(
                                        file_path=file_path,
                                        line=line_num,
                                        column=col_num,
                                        tool="ruff",
                                        code=error_code,
                                        message=message,
                                        severity="error"
                                        if error_code.startswith(("E", "F", "S"))
                                        else "warning",
                                    )
                                )
                            except ValueError:
                                continue

        except (subprocess.TimeoutExpired, FileNotFoundError):
            violations.append(
                StyleViolation(
                    file_path=file_path,
                    line=1,
                    column=1,
                    tool="ruff",
                    code="RUFF000",
                    message="Ruff linter not available or timed out",
                    severity="warning",
                )
            )

        return violations

    def _check_mypy_typing(
        self, temp_path: Path, file_path: str
    ) -> list[StyleViolation]:
        """Check MyPy type annotations."""
        violations = []

        try:
            result = subprocess.run(  # nosec B603 B607 - controlled environment
                [
                    "mypy",
                    "--python-version=3.13",
                    "--disallow-untyped-defs",
                    str(temp_path),
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                # Parse MyPy output
                for line in result.stdout.splitlines():
                    if ":" in line and "error:" in line:
                        parts = line.split(":", 3)
                        if len(parts) >= 3:
                            try:
                                line_num = int(parts[1])
                                message = (
                                    parts[2].strip()
                                    if len(parts) > 2
                                    else "Type checking error"
                                )

                                violations.append(
                                    StyleViolation(
                                        file_path=file_path,
                                        line=line_num,
                                        column=1,
                                        tool="mypy",
                                        code="MYPY001",
                                        message=message,
                                        severity="error",
                                    )
                                )
                            except ValueError:
                                continue

        except (subprocess.TimeoutExpired, FileNotFoundError):
            violations.append(
                StyleViolation(
                    file_path=file_path,
                    line=1,
                    column=1,
                    tool="mypy",
                    code="MYPY000",
                    message="MyPy type checker not available or timed out",
                    severity="warning",
                )
            )

        return violations

    def _check_import_sorting(
        self, temp_path: Path, file_path: str
    ) -> list[StyleViolation]:
        """Check import sorting with isort."""
        violations = []

        try:
            result = subprocess.run(  # nosec B603 B607 - controlled environment
                [
                    "isort",
                    "--check-only",
                    "--profile=black",
                    "--line-length=88",
                    str(temp_path),
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                violations.append(
                    StyleViolation(
                        file_path=file_path,
                        line=1,
                        column=1,
                        tool="isort",
                        code="ISORT001",
                        message="Imports are not properly sorted",
                        severity="error",
                    )
                )

        except (subprocess.TimeoutExpired, FileNotFoundError):
            violations.append(
                StyleViolation(
                    file_path=file_path,
                    line=1,
                    column=1,
                    tool="isort",
                    code="ISORT000",
                    message="isort import sorter not available or timed out",
                    severity="warning",
                )
            )

        return violations

    def _check_security(self, temp_path: Path, file_path: str) -> list[StyleViolation]:
        """Check security with Bandit."""
        violations = []

        try:
            result = subprocess.run(  # nosec B603 B607 - controlled environment
                ["bandit", "-r", str(temp_path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            # Bandit returns non-zero for security issues, but that's expected
            if result.stdout:
                # Parse Bandit output for security issues
                for line in result.stdout.splitlines():
                    if ">> Issue:" in line:
                        violations.append(
                            StyleViolation(
                                file_path=file_path,
                                line=1,
                                column=1,
                                tool="bandit",
                                code="BANDIT001",
                                message=line.strip(),
                                severity="error",
                            )
                        )

        except (subprocess.TimeoutExpired, FileNotFoundError):
            violations.append(
                StyleViolation(
                    file_path=file_path,
                    line=1,
                    column=1,
                    tool="bandit",
                    code="BANDIT000",
                    message="Bandit security checker not available or timed out",
                    severity="warning",
                )
            )

        return violations

    def _check_custom_conventions(
        self, code: str, file_path: str
    ) -> list[StyleViolation]:
        """Check custom project conventions."""
        violations = []
        lines = code.splitlines()

        # Check docstring conventions
        for i, line in enumerate(lines):
            line_num = i + 1

            # Check for missing docstrings in classes and functions
            if line.strip().startswith(("class ", "def ", "async def ")):
                # Look for docstring in next few lines
                has_docstring = False
                for j in range(i + 1, min(i + 5, len(lines))):
                    if '"""' in lines[j] or "'''" in lines[j]:
                        has_docstring = True
                        break
                    if lines[j].strip() and not lines[j].strip().startswith("#"):
                        break

                if not has_docstring and not line.strip().startswith(
                    "def _"
                ):  # Skip private methods
                    violations.append(
                        StyleViolation(
                            file_path=file_path,
                            line=line_num,
                            column=1,
                            tool="custom",
                            code="DOC001",
                            message="Missing docstring for public function/class",
                            severity="warning",
                        )
                    )

            # Check for proper type annotations
            if (
                "def " in line
                and "->" not in line
                and not line.strip().startswith("def _")
                and ("self" in line or "cls" in line)  # Method
            ):
                violations.append(
                    StyleViolation(
                        file_path=file_path,
                        line=line_num,
                        column=1,
                        tool="custom",
                        code="TYPE001",
                        message="Missing return type annotation",
                        severity="warning",
                    )
                )

        return violations

    def format_violations(self, violations: list[StyleViolation]) -> str:
        """Format violations for display."""
        if not violations:
            return "✅ All coding conventions followed!"

        output = f"❌ Found {len(violations)} style violations:\n\n"

        # Group by tool
        by_tool: dict[str, list[StyleViolation]] = {}
        for violation in violations:
            if violation.tool not in by_tool:
                by_tool[violation.tool] = []
            by_tool[violation.tool].append(violation)

        for tool, tool_violations in by_tool.items():
            output += f"📋 {tool.upper()} Issues:\n"
            for v in tool_violations:
                severity_icon = "🚨" if v.severity == "error" else "⚠️"
                output += f"  {severity_icon} {v.file_path}:{v.line}:{v.column} {v.code} - {v.message}\n"
            output += "\n"

        return output

    def auto_fix_code(self, code: str) -> str:
        """
        Auto-fix code using available formatters.

        Args:
            code: Code to fix

        Returns:
            Fixed code
        """
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write(code)
            temp_path = Path(temp_file.name)

        try:
            # Run isort
            with contextlib.suppress(
                subprocess.CalledProcessError,
                subprocess.TimeoutExpired,
                FileNotFoundError,
            ):
                subprocess.run(  # nosec B603 B607 - controlled environment
                    ["isort", "--profile=black", "--line-length=88", str(temp_path)],
                    check=True,
                    capture_output=True,
                    timeout=30,
                )

            # Run Black
            with contextlib.suppress(
                subprocess.CalledProcessError,
                subprocess.TimeoutExpired,
                FileNotFoundError,
            ):
                subprocess.run(  # nosec B603 B607 - controlled environment
                    ["black", "--line-length=88", str(temp_path)],
                    check=True,
                    capture_output=True,
                    timeout=30,
                )

            # Run Ruff with auto-fix
            with contextlib.suppress(
                subprocess.CalledProcessError,
                subprocess.TimeoutExpired,
                FileNotFoundError,
            ):
                subprocess.run(  # nosec B603 B607 - controlled environment
                    ["ruff", "check", "--fix", "--line-length=88", str(temp_path)],
                    check=True,
                    capture_output=True,
                    timeout=30,
                )

            # Read fixed code
            fixed_code = temp_path.read_text()
            return fixed_code

        finally:
            temp_path.unlink(missing_ok=True)


def validate_generated_code(
    code: str, file_path: str = "generated.py"
) -> tuple[bool, str]:
    """
    Validate generated code against project standards.

    Args:
        code: Python code to validate
        file_path: Virtual file path for context

    Returns:
        Tuple of (is_valid, formatted_report)
    """
    validator = CodeStyleValidator()
    violations = validator.validate_code(code, file_path)
    report = validator.format_violations(violations)

    # Consider only errors as blocking (not warnings)
    has_errors = any(v.severity == "error" for v in violations)

    return not has_errors, report


def auto_fix_code(code: str) -> str:
    """
    Auto-fix code to meet project standards.

    Args:
        code: Code to fix

    Returns:
        Fixed code
    """
    validator = CodeStyleValidator()
    return validator.auto_fix_code(code)


if __name__ == "__main__":
    # Test the validator
    test_code = """
import os,sys
from typing import Dict
import json

class TestClass:
    def test_method(self,param1,param2):
        result=param1+param2
        return result
    """

    is_valid, report = validate_generated_code(test_code)
    print(report)

    if not is_valid:
        print("\n" + "=" * 50)
        print("AUTO-FIXING CODE...")
        print("=" * 50)

        fixed_code = auto_fix_code(test_code)
        print(fixed_code)

        print("\n" + "=" * 50)
        print("VALIDATION AFTER FIX:")
        print("=" * 50)

        is_valid_after, report_after = validate_generated_code(fixed_code)
        print(report_after)
