"""Assessment domain data contracts and schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class QuestionType(StrEnum):
    MCQ = "MCQ"
    BOOLEAN = "BOOLEAN"
    NUMERICAL = "NUMERICAL"
    SUBJECTIVE = "SUBJECTIVE"
    CODING = "CODING"


class AssessmentTypeEnum(StrEnum):
    MCQ = "MCQ"
    NUMERICAL = "NUMERICAL"
    SUBJECTIVE = "SUBJECTIVE"
    CODING = "CODING"
    ADAPTIVE = "ADAPTIVE"
    TIMED_EXAM = "TIMED_EXAM"


@dataclass
class RubricCriterion:
    """Individual rubric criterion for subjective evaluation."""

    criterion_id: str
    name: str
    description: str = ""
    max_points: float = 4.0
    weight: float = 1.0
    levels: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "criterion_id": self.criterion_id,
            "name": self.name,
            "description": self.description,
            "max_points": self.max_points,
            "weight": self.weight,
            "levels": self.levels,
        }


@dataclass
class Rubric:
    """Multi-criterion scoring rubric."""

    rubric_id: str
    title: str
    description: str = ""
    criteria: list[RubricCriterion] = field(default_factory=list)

    @property
    def total_max_points(self) -> float:
        return sum(c.max_points * c.weight for c in self.criteria)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rubric_id": self.rubric_id,
            "title": self.title,
            "description": self.description,
            "criteria": [c.to_dict() for c in self.criteria],
            "total_max_points": self.total_max_points,
        }


@dataclass
class AssessmentItem:
    """Individual question or problem item in an assessment."""

    id: str
    item_type: QuestionType
    question_text: str
    concept_id: str
    max_marks: float = 4.0
    difficulty: int = 1  # 1 to 5
    options: list[str] | None = None
    correct_answer: str | None = None  # Protected: stripped for student
    expected_unit: str | None = None
    tolerance_pct: float = 2.0
    rubric: Rubric | None = None
    test_cases: list[dict[str, Any]] | None = None  # For coding: [{"input": ..., "expected": ...}]
    solution_code: str | None = None  # Protected
    explanation: str | None = None  # Protected
    hints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "item_type": self.item_type.value
            if isinstance(self.item_type, QuestionType)
            else str(self.item_type),
            "question_text": self.question_text,
            "concept_id": self.concept_id,
            "max_marks": self.max_marks,
            "difficulty": self.difficulty,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "expected_unit": self.expected_unit,
            "tolerance_pct": self.tolerance_pct,
            "rubric": self.rubric.to_dict() if self.rubric else None,
            "test_cases": self.test_cases,
            "solution_code": self.solution_code,
            "explanation": self.explanation,
            "hints": self.hints,
        }
        return data


@dataclass
class ItemGradingResult:
    """Evaluation result for an individual assessment item."""

    item_id: str
    student_answer: Any
    is_correct: bool
    score: float
    max_marks: float
    percentage: float = 0.0
    criterion_scores: dict[str, float] = field(default_factory=dict)
    feedback: str = ""
    misconception_code: str | None = None
    ai_graded: bool = False
    ai_confidence: float = 1.0
    ai_rationale: str = ""
    teacher_adjusted: bool = False
    teacher_comment: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "student_answer": self.student_answer,
            "is_correct": self.is_correct,
            "score": round(self.score, 2),
            "max_marks": round(self.max_marks, 2),
            "percentage": round(self.percentage, 2),
            "criterion_scores": self.criterion_scores,
            "feedback": self.feedback,
            "misconception_code": self.misconception_code,
            "ai_graded": self.ai_graded,
            "ai_confidence": self.ai_confidence,
            "ai_rationale": self.ai_rationale,
            "teacher_adjusted": self.teacher_adjusted,
            "teacher_comment": self.teacher_comment,
        }


@dataclass
class SubmissionSummary:
    """Comprehensive submission evaluation summary."""

    total_score: float
    max_score: float
    percentage: float
    passed: bool
    item_results: dict[str, ItemGradingResult]
    weak_concepts: list[str]
    misconceptions_flagged: list[str]
    overall_feedback: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_score": round(self.total_score, 2),
            "max_score": round(self.max_score, 2),
            "percentage": round(self.percentage, 2),
            "passed": self.passed,
            "item_results": {k: v.to_dict() for k, v in self.item_results.items()},
            "weak_concepts": self.weak_concepts,
            "misconceptions_flagged": self.misconceptions_flagged,
            "overall_feedback": self.overall_feedback,
        }
