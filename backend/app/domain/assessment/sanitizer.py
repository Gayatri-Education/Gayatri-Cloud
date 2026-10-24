"""Anti-Answer-Leakage Sanitizer Service for Gayatri Cloud.

Ensures active assessment payloads delivered to students never leak unearned answers,
rubrics, correct indices, solutions, or teacher explanations.
"""

from __future__ import annotations

from typing import Any


class AssessmentSanitizer:
    """Authoritative sanitizer for assessment content delivery to students."""

    RESTRICTED_FIELDS = {
        "correct_answer",
        "answer",
        "expected_answer",
        "expected_value",
        "correct_index",
        "explanation",
        "solution",
        "solution_code",
        "rubric",
        "internal_notes",
        "common_misconceptions",
    }

    @classmethod
    def sanitize_item_for_student(cls, item: Any, allow_hints: bool = False) -> dict[str, Any]:
        """Strip answer keys, solutions, rubrics, and explanations from assessment items."""
        if hasattr(item, "to_dict") and callable(item.to_dict):
            raw = item.to_dict()
        elif isinstance(item, dict):
            raw = dict(item)
        else:
            raw = {
                "id": getattr(item, "id", ""),
                "question_text": getattr(item, "question_text", getattr(item, "question", "")),
                "item_type": getattr(item, "item_type", getattr(item, "type", "MCQ")),
                "options": getattr(item, "options", []),
                "difficulty": getattr(item, "difficulty", 1),
                "concept_id": getattr(item, "concept_id", ""),
                "max_marks": getattr(item, "max_marks", 4.0),
            }

        sanitized: dict[str, Any] = {}
        for k, v in raw.items():
            if k in cls.RESTRICTED_FIELDS:
                continue
            if k == "hints" and not allow_hints:
                continue
            # For coding questions, sanitize internal test case details if needed
            if k == "test_cases" and isinstance(v, list):
                # Provide only visible inputs, strip expected answers
                sanitized_tests = []
                for tc in v:
                    if isinstance(tc, dict):
                        sanitized_tests.append({"input": tc.get("input")})
                    else:
                        sanitized_tests.append(tc)
                sanitized["test_cases"] = sanitized_tests
                continue

            sanitized[k] = v

        return sanitized

    @classmethod
    def sanitize_assessment_for_student(
        cls,
        assessment_dict: dict[str, Any],
        items: list[Any],
        allow_hints: bool = False,
    ) -> dict[str, Any]:
        """Produce clean, leak-free assessment payload for student examination."""
        sanitized_assessment = dict(assessment_dict)
        # Remove any internal rubrics or answer configs from top-level metadata
        for rf in cls.RESTRICTED_FIELDS:
            sanitized_assessment.pop(rf, None)

        sanitized_items = [
            cls.sanitize_item_for_student(item, allow_hints=allow_hints) for item in items
        ]
        sanitized_assessment["items"] = sanitized_items
        return sanitized_assessment

    @classmethod
    def verify_no_leakage(cls, payload: Any) -> bool:
        """Verify that a given payload contains zero restricted answer leakage fields."""
        if isinstance(payload, dict):
            for k, v in payload.items():
                if k in cls.RESTRICTED_FIELDS:
                    return False
                if not cls.verify_no_leakage(v):
                    return False
        elif isinstance(payload, list):
            for elem in payload:
                if not cls.verify_no_leakage(elem):
                    return False
        return True
