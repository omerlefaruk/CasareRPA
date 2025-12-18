"""
Automatic Code Language Detector for CasareRPA Expression Editor.

Provides heuristic-based language detection for the expression editor
when set to AUTO mode.
"""

import re
from typing import Dict

from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
    EditorType,
)


class CodeDetector:
    """
    Heuristic-based code language detector.

    Analyzes text content to guess the most likely programming language.
    Supports Python, JavaScript, JSON, YAML, and Markdown.
    """

    @staticmethod
    def detect_language(text: str) -> EditorType:
        """
        Detect the language of the given text.

        Args:
            text: Text content to analyze

        Returns:
            The detected EditorType, defaults to RICH_TEXT if uncertain
        """
        if not text or not text.strip():
            return EditorType.RICH_TEXT

        scores: Dict[EditorType, int] = {
            EditorType.CODE_PYTHON: 0,
            EditorType.CODE_JAVASCRIPT: 0,
            EditorType.CODE_JSON: 0,
            EditorType.CODE_YAML: 0,
            EditorType.MARKDOWN: 0,
        }

        # JSON Detection
        # Strict JSON usually starts/ends with {} or []
        stripped = text.strip()
        if (stripped.startswith("{") and stripped.endswith("}")) or (
            stripped.startswith("[") and stripped.endswith("]")
        ):
            scores[EditorType.CODE_JSON] += 50
            # Check for quoted keys
            if re.search(r'"[^"]+"\s*:', text):
                scores[EditorType.CODE_JSON] += 20

        # YAML Detection
        # Key-value pairs, dashes for lists
        if re.search(r"^[\w\-\s]+:\s", text, re.MULTILINE):
            scores[EditorType.CODE_YAML] += 20
        if re.search(r"^\s*-\s", text, re.MULTILINE):
            scores[EditorType.CODE_YAML] += 10
        # YAML often doesn't use quotes for keys
        if re.search(r"^[\w]+:\s", text, re.MULTILINE) and not re.search(
            r"^\s*[{[]", text
        ):
            scores[EditorType.CODE_YAML] += 15

        # Python Detection
        if re.search(r"\bdef\s+\w+\s*\(", text):
            scores[EditorType.CODE_PYTHON] += 30
        if re.search(r"\bimport\s+\w+", text) or re.search(
            r"\bfrom\s+\w+\s+import", text
        ):
            scores[EditorType.CODE_PYTHON] += 30
        if re.search(r"\bclass\s+\w+", text):
            scores[EditorType.CODE_PYTHON] += 20
        if re.search(r"^\s*if\s+.*:\s*$", text, re.MULTILINE):
            scores[EditorType.CODE_PYTHON] += 20
        if "#" in text and "//" not in text:
            scores[EditorType.CODE_PYTHON] += 5

        # JavaScript Detection
        if re.search(r"\bfunction\s+\w+\s*\(", text):
            scores[EditorType.CODE_JAVASCRIPT] += 30
        if re.search(r"\bconst\s+\w+\s*=", text) or re.search(r"\blet\s+\w+\s*=", text):
            scores[EditorType.CODE_JAVASCRIPT] += 20
        if re.search(r"\bconsole\.log\(", text):
            scores[EditorType.CODE_JAVASCRIPT] += 20
        if re.search(r"\=\>\s*\{", text):  # Arrow functions
            scores[EditorType.CODE_JAVASCRIPT] += 20
        if re.search(r"\bvar\s+\w+", text):
            scores[EditorType.CODE_JAVASCRIPT] += 10
        if "{" in text and "}" in text and ";" in text:
            scores[EditorType.CODE_JAVASCRIPT] += 10

        # Markdown Detection
        if re.search(r"^#+\s", text, re.MULTILINE):
            scores[EditorType.MARKDOWN] += 30
        if re.search(r"\*\*.*\*\*", text):
            scores[EditorType.MARKDOWN] += 10
        if re.search(r"\[.*\]\(.*\)", text):  # Links
            scores[EditorType.MARKDOWN] += 20
        if re.search(r"^\s*[-*]\s", text, re.MULTILINE):  # Lists
            scores[EditorType.MARKDOWN] += 10

        # Heuristic adjustments
        # If it looks like JSON but has no quotes on keys, it might be JS object or YAML
        # If it has comments // it's likely JS (or JSONC but we treat JSONC as JS often)

        # Get best match
        best_type = max(scores, key=scores.get)
        max_score = scores[best_type]

        # Threshold to avoid false positives on plain text
        if max_score < 10:
            return EditorType.RICH_TEXT

        return best_type
