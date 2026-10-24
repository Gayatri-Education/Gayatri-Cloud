"""Subjective, coding, and adaptive assessment evaluators."""

from __future__ import annotations

import ast
import re
from typing import Any

from app.domain.assessment.models import AssessmentItem, ItemGradingResult, Rubric
from app.domain.assessment.rubrics import RubricEngine


class SubjectiveEvaluator:
    """Evaluates open-ended subjective responses against rubrics and detects misconceptions."""

    MISCONCEPTION_PATTERNS = {
        "MISCON_HEAT_WORK": {
            "keywords": ["heat is work", "heat equals work", "work cannot be converted"],
            "feedback": "Misconception identified: Heat (q) and Work (w) are path functions of energy transfer, not identical state quantities.",
        },
        "MISCON_ISOTHERMAL_ADIABATIC": {
            "keywords": [
                "isothermal means no heat transfer",
                "adiabatic means constant temperature",
                "isothermal adiabatic same",
            ],
            "feedback": "Misconception identified: Isothermal means constant temperature (ΔT=0), whereas Adiabatic means zero heat exchange (q=0).",
        },
        "MISCON_BOND_BREAKING": {
            "keywords": [
                "bond breaking releases energy",
                "breaking bonds creates energy",
                "forming bonds absorbs energy",
            ],
            "feedback": "Misconception identified: Breaking chemical bonds always requires energy (endothermic), while forming bonds releases energy (exothermic).",
        },
    }

    @classmethod
    def evaluate(
        cls,
        item: AssessmentItem,
        student_answer: Any,
        rubric: Rubric | None = None,
    ) -> ItemGradingResult:
        """Score subjective answer using rubric, keyword matching, and misconception heuristics."""
        ans_str = str(student_answer or "").strip()
        ans_lower = ans_str.lower()
        max_marks = float(item.max_marks)

        if not ans_str:
            return ItemGradingResult(
                item_id=item.id,
                student_answer=student_answer,
                is_correct=False,
                score=0.0,
                max_marks=max_marks,
                percentage=0.0,
                feedback="No response provided.",
                ai_graded=True,
                ai_confidence=1.0,
                ai_rationale="Blank answer submitted.",
            )

        # 1. Detect known misconceptions
        detected_misconception = None
        misconception_feedback = ""
        for code, data in cls.MISCONCEPTION_PATTERNS.items():
            for kw in data["keywords"]:
                if kw in ans_lower:
                    detected_misconception = code
                    misconception_feedback = data["feedback"]
                    break
            if detected_misconception:
                break

        # 2. Select rubric
        active_rubric = rubric or item.rubric or RubricEngine.get_standard_rubric()

        # 3. Calculate keyword matches
        expected_ans = str(item.correct_answer or "")
        keywords = [
            w.strip().lower()
            for w in re.findall(r"\w+", expected_ans)
            if len(w) >= 3 and w.lower() not in {"the", "and", "that", "this", "with", "from"}
        ]
        matches = sum(1 for kw in keywords if kw in ans_lower)
        keyword_ratio = (
            (matches / len(keywords)) if keywords else (1.0 if len(ans_str) >= 20 else 0.5)
        )

        # 4. Score rubric criteria
        criterion_scores: dict[str, float] = {}
        for crit in active_rubric.criteria:
            crit_id = crit.criterion_id.lower()
            if "concept" in crit_id or "accuracy" in crit_id:
                if detected_misconception:
                    c_score = crit.max_points * 0.25
                elif keyword_ratio >= 0.70:
                    c_score = crit.max_points * 1.0
                elif keyword_ratio >= 0.35:
                    c_score = crit.max_points * 0.75
                elif len(ans_str) > 15:
                    c_score = crit.max_points * 0.5
                else:
                    c_score = crit.max_points * 0.25
            elif "step" in crit_id or "execution" in crit_id or "evidence" in crit_id:
                if keyword_ratio >= 0.50:
                    c_score = crit.max_points * 1.0
                elif keyword_ratio >= 0.25:
                    c_score = crit.max_points * 0.75
                else:
                    c_score = crit.max_points * 0.50
            else:
                # Clarity / explanation
                if len(ans_str) >= 40:
                    c_score = crit.max_points * 1.0
                elif len(ans_str) >= 15:
                    c_score = crit.max_points * 0.75
                else:
                    c_score = crit.max_points * 0.50

            criterion_scores[crit.criterion_id] = c_score

        eval_result = RubricEngine.evaluate_with_rubric(active_rubric, criterion_scores)
        fraction_earned = eval_result["total_earned"] / max(eval_result["total_possible"], 1e-4)
        scaled_score = round(fraction_earned * max_marks, 2)
        is_correct = fraction_earned >= 0.70

        feedback = (
            "Response demonstrates strong conceptual mastery."
            if is_correct
            else "Response addresses some points but needs further conceptual development."
        )
        if misconception_feedback:
            feedback = f"{feedback} {misconception_feedback}"

        confidence = round(
            min(0.99, max(0.50, 0.45 + 0.35 * keyword_ratio + 0.20 * fraction_earned)), 2
        )
        rationale = f"Evaluated against '{active_rubric.title}' ({eval_result['percentage']}% criteria met)."

        return ItemGradingResult(
            item_id=item.id,
            student_answer=student_answer,
            is_correct=is_correct,
            score=scaled_score,
            max_marks=max_marks,
            percentage=round(fraction_earned * 100.0, 2),
            criterion_scores=criterion_scores,
            feedback=feedback,
            misconception_code=detected_misconception,
            ai_graded=True,
            ai_confidence=confidence,
            ai_rationale=rationale,
        )


class CodingEvaluator:
    """Safely validates syntax and executes unit test cases against submitted code."""

    @classmethod
    def evaluate(cls, item: AssessmentItem, student_code: str) -> ItemGradingResult:
        """Validate Python syntax and evaluate against test cases."""
        code_str = str(student_code or "").strip()
        max_marks = float(item.max_marks)

        if not code_str:
            return ItemGradingResult(
                item_id=item.id,
                student_answer=student_code,
                is_correct=False,
                score=0.0,
                max_marks=max_marks,
                feedback="No code submitted.",
                ai_graded=False,
            )

        # 1. AST syntax check
        try:
            ast.parse(code_str)
        except SyntaxError as e:
            return ItemGradingResult(
                item_id=item.id,
                student_answer=student_code,
                is_correct=False,
                score=0.0,
                max_marks=max_marks,
                feedback=f"SyntaxError on line {e.lineno}: {e.msg}",
                ai_graded=False,
                ai_rationale="Failed Python syntax compilation check.",
            )

        # 2. Test case evaluation
        test_cases = item.test_cases or []
        if not test_cases:
            # If no explicit test cases, award full marks for syntactically valid code
            return ItemGradingResult(
                item_id=item.id,
                student_answer=student_code,
                is_correct=True,
                score=max_marks,
                max_marks=max_marks,
                percentage=100.0,
                feedback="Syntax valid and passes static checks.",
                ai_graded=False,
            )

        passed_tests = 0
        total_tests = len(test_cases)
        failures = []

        # Safe sandbox environment
        safe_builtins = {
            "abs": abs,
            "bool": bool,
            "dict": dict,
            "float": float,
            "int": int,
            "len": len,
            "list": list,
            "max": max,
            "min": min,
            "range": range,
            "round": round,
            "set": set,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "zip": zip,
        }

        try:
            local_scope: dict[str, Any] = {}
            # Execute user code to define functions
            exec(code_str, {"__builtins__": safe_builtins}, local_scope)

            for idx, tc in enumerate(test_cases):
                fn_name = tc.get("function_name")
                expected = tc.get("expected")
                args = tc.get("input", [])
                if not isinstance(args, list):
                    args = [args]

                if fn_name and fn_name in local_scope and callable(local_scope[fn_name]):
                    actual = local_scope[fn_name](*args)
                    if actual == expected:
                        passed_tests += 1
                    else:
                        failures.append(
                            f"Test {idx + 1}: {fn_name}({args}) returned {actual!r}, expected {expected!r}"
                        )
                else:
                    failures.append(f"Function '{fn_name}' not defined or not callable.")
        except Exception as e:
            return ItemGradingResult(
                item_id=item.id,
                student_answer=student_code,
                is_correct=False,
                score=0.0,
                max_marks=max_marks,
                feedback=f"Runtime error during execution: {type(e).__name__}: {e}",
                ai_graded=False,
            )

        fraction = passed_tests / max(total_tests, 1)
        score = round(fraction * max_marks, 2)
        is_correct = passed_tests == total_tests
        feedback = (
            f"All {total_tests} test cases passed."
            if is_correct
            else f"Passed {passed_tests}/{total_tests} test cases. {'; '.join(failures[:2])}"
        )

        return ItemGradingResult(
            item_id=item.id,
            student_answer=student_code,
            is_correct=is_correct,
            score=score,
            max_marks=max_marks,
            percentage=round(fraction * 100.0, 2),
            feedback=feedback,
            ai_graded=False,
        )


class AdaptiveEngine:
    """Selects the next assessment item dynamically based on student performance."""

    @classmethod
    def select_next_item(
        cls,
        current_difficulty: int,
        is_previous_correct: bool,
        available_items: list[AssessmentItem],
        answered_ids: set[str],
    ) -> AssessmentItem | None:
        """Increase difficulty on success, decrease or scaffold on failure."""
        if is_previous_correct:
            target_difficulty = min(5, current_difficulty + 1)
        else:
            target_difficulty = max(1, current_difficulty - 1)

        unanswered = [item for item in available_items if item.id not in answered_ids]
        if not unanswered:
            return None

        # Prefer exact difficulty match
        matching = [item for item in unanswered if item.difficulty == target_difficulty]
        if matching:
            return matching[0]

        # Otherwise pick closest difficulty
        unanswered.sort(key=lambda item: abs(item.difficulty - target_difficulty))
        return unanswered[0]
