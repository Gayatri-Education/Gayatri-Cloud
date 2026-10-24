"""Multi-criterion rubric scoring and evaluation engine."""

from __future__ import annotations

from typing import Any

from app.domain.assessment.models import Rubric, RubricCriterion


class RubricEngine:
    """Calculates weighted rubric evaluations and standard rubric presets."""

    @classmethod
    def evaluate_with_rubric(
        cls, rubric: Rubric, criterion_scores: dict[str, float]
    ) -> dict[str, Any]:
        """Compute weighted score and percentages across all criteria."""
        total_earned = 0.0
        total_possible = 0.0
        details = {}

        for crit in rubric.criteria:
            raw_score = float(criterion_scores.get(crit.criterion_id, 0.0))
            # Bound score to [0, max_points]
            bounded_score = max(0.0, min(raw_score, crit.max_points))
            weighted_earned = bounded_score * crit.weight
            weighted_possible = crit.max_points * crit.weight

            total_earned += weighted_earned
            total_possible += weighted_possible

            details[crit.criterion_id] = {
                "name": crit.name,
                "raw_score": bounded_score,
                "max_points": crit.max_points,
                "weight": crit.weight,
                "weighted_earned": round(weighted_earned, 2),
                "weighted_possible": round(weighted_possible, 2),
            }

        percentage = (
            (total_earned / max(total_possible, 1e-4)) * 100.0 if total_possible > 0 else 0.0
        )

        return {
            "total_earned": round(total_earned, 2),
            "total_possible": round(total_possible, 2),
            "percentage": round(percentage, 2),
            "criterion_details": details,
        }

    @classmethod
    def get_standard_rubric(cls, name: str = "stem_problem_solving") -> Rubric:
        """Provide standard rubric presets."""
        if name == "stem_problem_solving":
            return Rubric(
                rubric_id="rubric_stem_problem_solving",
                title="STEM Problem Solving Rubric",
                description="Evaluates conceptual accuracy, step execution, and clear mathematical reasoning.",
                criteria=[
                    RubricCriterion(
                        criterion_id="conceptual_accuracy",
                        name="Conceptual Understanding",
                        description="Identifies core formulas, laws, and physical/mathematical principles.",
                        max_points=4.0,
                        weight=1.5,
                        levels={
                            "4": "Mastery of all underlying concepts.",
                            "2": "Partial understanding with minor flaws.",
                            "0": "Completely flawed or irrelevant principles.",
                        },
                    ),
                    RubricCriterion(
                        criterion_id="execution_steps",
                        name="Execution & Steps",
                        description="Applies systematic algebraic/logical steps toward the solution.",
                        max_points=4.0,
                        weight=1.0,
                        levels={
                            "4": "Flawless step execution.",
                            "2": "Minor calculation error.",
                            "0": "No coherent steps shown.",
                        },
                    ),
                    RubricCriterion(
                        criterion_id="clarity_reasoning",
                        name="Clarity & Justification",
                        description="Explains steps and justifies conclusions clearly.",
                        max_points=4.0,
                        weight=0.5,
                        levels={
                            "4": "Crystal clear reasoning.",
                            "2": "Adequate explanation.",
                            "0": "Unintelligible or missing explanation.",
                        },
                    ),
                ],
            )
        else:
            return Rubric(
                rubric_id="rubric_general_essay",
                title="General Subjective Essay Rubric",
                description="Evaluates argument coherence, evidence, and critical depth.",
                criteria=[
                    RubricCriterion(
                        criterion_id="core_argument",
                        name="Core Argument",
                        description="Clearly articulates central thesis.",
                        max_points=4.0,
                        weight=1.0,
                    ),
                    RubricCriterion(
                        criterion_id="evidence_justification",
                        name="Supporting Evidence",
                        description="Provides relevant examples and references.",
                        max_points=4.0,
                        weight=1.0,
                    ),
                ],
            )
