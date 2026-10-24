"""Exact, numerical, and rule-based deterministic evaluator."""

from __future__ import annotations

import math
import re
from typing import Any


class DeterministicGrader:
    """Exact, numerical, and rule-based deterministic evaluator."""

    @staticmethod
    def _normalize(text: Any) -> str:
        if text is None:
            return ""
        return re.sub(r"\s+", " ", str(text).strip().lower())

    @classmethod
    def grade_mcq(
        cls,
        student_answer: Any,
        correct_answer: str,
        options: list[str] | None = None,
    ) -> tuple[bool, float, str]:
        """Grade MCQ matching either option index/letter (e.g. 'A', '1') or option content."""
        norm_ans = cls._normalize(student_answer)
        norm_correct = cls._normalize(correct_answer)

        if not norm_ans:
            return False, 0.0, "No answer provided."

        if norm_ans == norm_correct:
            return True, 1.0, "Correct."

        # Normalize option letter wrappers like "(A)", "A.", "Option A", "[a]"
        cleaned_ans = re.sub(r"^(?:option|\[|\()?\s*([a-e])\s*(?:\]|\)|\.)?$", r"\1", norm_ans)
        cleaned_correct = re.sub(
            r"^(?:option|\[|\()?\s*([a-e])\s*(?:\]|\)|\.)?$", r"\1", norm_correct
        )

        if cleaned_ans == cleaned_correct:
            return True, 1.0, "Correct."

        letter_map = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4}
        if options:
            # 1. Student entered letter, correct is text
            if cleaned_ans in letter_map and letter_map[cleaned_ans] < len(options):
                selected_opt = cls._normalize(options[letter_map[cleaned_ans]])
                if selected_opt == norm_correct:
                    return True, 1.0, "Correct."

            # 2. Student entered text, correct is letter
            if cleaned_correct in letter_map and letter_map[cleaned_correct] < len(options):
                expected_opt = cls._normalize(options[letter_map[cleaned_correct]])
                if norm_ans == expected_opt:
                    return True, 1.0, "Correct."

            # 3. Numeric option index (1-based or 0-based)
            if norm_ans.isdigit():
                idx = int(norm_ans)
                if 1 <= idx <= len(options) and cls._normalize(options[idx - 1]) == norm_correct:
                    return True, 1.0, "Correct."
                if 0 <= idx < len(options) and cls._normalize(options[idx]) == norm_correct:
                    return True, 1.0, "Correct."

        return False, 0.0, f"Incorrect. Correct answer was: {correct_answer}"

    @classmethod
    def grade_boolean(cls, student_answer: Any, correct_answer: Any) -> tuple[bool, float, str]:
        """Grade True/False and Boolean equivalents."""
        norm_ans = cls._normalize(student_answer)
        norm_correct = cls._normalize(correct_answer)

        truthy = {"true", "t", "yes", "y", "1"}
        falsy = {"false", "f", "no", "n", "0"}

        bool_student = True if norm_ans in truthy else (False if norm_ans in falsy else None)
        bool_correct = (
            True if norm_correct in truthy else (False if norm_correct in falsy else None)
        )

        if bool_student is None:
            return (
                False,
                0.0,
                f"Invalid boolean response: '{student_answer}'. Expected True or False.",
            )

        if bool_student == bool_correct:
            return True, 1.0, "Correct."
        return False, 0.0, f"Incorrect. Expected {correct_answer}."

    @classmethod
    def grade_numerical(
        cls,
        student_answer: Any,
        correct_answer: Any,
        tolerance_pct: float = 2.0,
        expected_unit: str | None = None,
    ) -> tuple[bool, float, str]:
        """Grade numerical values with relative tolerance, unit verification, and edge-case protection."""
        if student_answer is None or str(student_answer).strip() == "":
            return False, 0.0, "No numerical answer provided."

        s_str = str(student_answer).strip()
        c_str = str(correct_answer).strip()

        # Reject NaN / Infinity tokens
        if re.search(r"\b(?:nan|inf|infinity)\b", s_str, re.IGNORECASE):
            return False, 0.0, "Invalid numerical value: NaN and Infinity are not permitted."
        if re.search(r"\b(?:nan|inf|infinity)\b", c_str, re.IGNORECASE):
            return False, 0.0, "Invalid question configuration: expected answer is NaN/Infinity."

        num_pattern = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
        has_digit = bool(re.search(r"\d", s_str))
        if not has_digit:
            return False, 0.0, "Could not parse numerical value: no numerical magnitude found."

        # Exclude exponents in units (like ^2 or m/s^2) before parsing standalone numbers
        s_clean = re.sub(r"[\^][\+\-]?\d+", "", s_str)
        s_clean = re.sub(r"(?<=[a-zA-Z°%/\*])(?<![eE])\d+", "", s_clean)
        if expected_unit:
            s_clean = re.sub(re.escape(expected_unit), "", s_clean, flags=re.IGNORECASE)

        all_matches = list(re.finditer(num_pattern, s_clean))
        target_s_num = None
        if len(all_matches) > 1:
            label_match = re.search(
                r"(?:final\s*(?:answer|result)?|answer\s*(?:is|:)?|result\s*(?:is|:)?|=)\s*("
                + num_pattern
                + r")",
                s_str,
                re.IGNORECASE,
            )
            if label_match:
                target_s_num = label_match.group(1)
            else:
                return (
                    False,
                    0.0,
                    "Ambiguous answer: multiple numerical values found without explicit final answer designation.",
                )
        elif len(all_matches) == 1:
            target_s_num = all_matches[0].group(0)
        else:
            return False, 0.0, "Could not parse numerical value."

        c_match = re.search(num_pattern, c_str)
        if not c_match:
            return False, 0.0, "Could not parse expected numerical value from question definition."

        try:
            val_student = float(target_s_num)
            val_correct = float(c_match.group(0))
        except (ValueError, TypeError):
            return False, 0.0, "Numerical float conversion failed."

        if math.isnan(val_student) or math.isinf(val_student):
            return False, 0.0, "Invalid numerical value: parsed as NaN or Infinity."

        if val_student == 0.0:
            val_student = 0.0
        if val_correct == 0.0:
            val_correct = 0.0

        # Unit verification
        unit_target = expected_unit
        if not unit_target and isinstance(correct_answer, str):
            unit_sub = re.search(
                r"(?:^|\s)" + num_pattern + r"\s*([a-zA-Z°%][a-zA-Z0-9/°%^*-]*)", c_str
            )
            if unit_sub:
                unit_candidate = unit_sub.group(1).strip()
                if unit_candidate.lower() not in ("e", "e-", "e+"):
                    unit_target = unit_candidate

        if unit_target:
            exp_unit_clean = unit_target.strip().lower()
            s_unit_match = re.search(
                re.escape(target_s_num) + r"\s*([a-zA-Z°%][a-zA-Z0-9/°%^*-]*)", s_str
            )
            student_unit = s_unit_match.group(1).strip().lower() if s_unit_match else ""
            if not student_unit:
                if exp_unit_clean not in s_str.lower():
                    return False, 0.0, f"Missing required unit: expected '{unit_target}'."
            elif student_unit != exp_unit_clean:
                return (
                    False,
                    0.0,
                    f"Incorrect unit: got '{student_unit}', expected '{unit_target}'.",
                )

        # Closeness check
        if val_correct == 0.0:
            is_close = abs(val_student) <= 1e-4
        else:
            rel_diff = abs((val_student - val_correct) / val_correct) * 100.0
            is_close = rel_diff <= tolerance_pct or math.isclose(
                val_student, val_correct, rel_tol=tolerance_pct / 100.0
            )

        if is_close:
            return True, 1.0, "Numerically correct."
        return (
            False,
            0.0,
            f"Incorrect calculation. Expected approximately {val_correct} (tolerance ±{tolerance_pct}%).",
        )
