"""Comprehensive test suite for Assessment, Evaluation, and Grading Engine (Phase P10)."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.domain.assessment.deterministic import DeterministicGrader
from app.domain.assessment.evaluators import AdaptiveEngine, CodingEvaluator, SubjectiveEvaluator
from app.domain.assessment.models import (
    AssessmentItem,
    QuestionType,
    Rubric,
    RubricCriterion,
)
from app.domain.assessment.sanitizer import AssessmentSanitizer
from app.main import app


@pytest.fixture
async def assess_test_client():
    """Provides AsyncClient with an isolated in-memory test database."""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await test_engine.dispose()


async def register_and_login(client: AsyncClient, email: str, full_name: str) -> tuple[dict, str]:
    """Helper to register and login a user."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": full_name},
    )
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = res.json()["access_token"]
    user_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    return user_res.json(), token


# --- 1. Unit Tests: Evaluators & Anti-Leakage ---


def test_deterministic_mcq_evaluation():
    options = [
        "Newton's First Law",
        "Newton's Second Law",
        "Newton's Third Law",
        "Law of Gravitation",
    ]
    # 1. Exact string match
    is_corr, frac, fb = DeterministicGrader.grade_mcq(
        "Newton's Second Law", "Newton's Second Law", options
    )
    assert is_corr is True
    assert frac == 1.0

    # 2. Option letter index ('B' or '(b)' or 'Option B')
    is_corr, frac, _ = DeterministicGrader.grade_mcq("(b)", "Newton's Second Law", options)
    assert is_corr is True
    assert frac == 1.0

    is_corr, frac, _ = DeterministicGrader.grade_mcq("Option B", "Newton's Second Law", options)
    assert is_corr is True
    assert frac == 1.0

    # 3. 1-based numeric index ('2')
    is_corr, frac, _ = DeterministicGrader.grade_mcq("2", "Newton's Second Law", options)
    assert is_corr is True
    assert frac == 1.0

    # 4. Incorrect option
    is_corr, frac, fb = DeterministicGrader.grade_mcq("Option A", "Newton's Second Law", options)
    assert is_corr is False
    assert frac == 0.0


def test_deterministic_boolean_evaluation():
    is_corr, frac, _ = DeterministicGrader.grade_boolean("true", "True")
    assert is_corr is True
    assert frac == 1.0

    is_corr, frac, _ = DeterministicGrader.grade_boolean("yes", "True")
    assert is_corr is True

    is_corr, frac, _ = DeterministicGrader.grade_boolean("0", "False")
    assert is_corr is True

    is_corr, frac, _ = DeterministicGrader.grade_boolean("false", "True")
    assert is_corr is False
    assert frac == 0.0


def test_deterministic_numerical_evaluation():
    # 1. Within tolerance (±2%)
    is_corr, frac, _ = DeterministicGrader.grade_numerical(
        student_answer="9.85 m/s", correct_answer="9.80 m/s", tolerance_pct=2.0
    )
    assert is_corr is True
    assert frac == 1.0

    # 2. Outside tolerance
    is_corr, frac, _ = DeterministicGrader.grade_numerical(
        student_answer="10.5 m/s", correct_answer="9.80 m/s", tolerance_pct=2.0
    )
    assert is_corr is False
    assert frac == 0.0

    # 3. Missing unit when expected
    is_corr, frac, fb = DeterministicGrader.grade_numerical(
        student_answer="9.80", correct_answer="9.80", expected_unit="kg"
    )
    assert is_corr is False
    assert "Missing required unit" in fb

    # 4. Scientific notation
    is_corr, frac, _ = DeterministicGrader.grade_numerical(
        student_answer="1.5e3 J", correct_answer="1500 J", tolerance_pct=1.0
    )
    assert is_corr is True

    # 5. NaN / Infinity injection rejection
    is_corr, frac, fb = DeterministicGrader.grade_numerical(
        student_answer="NaN", correct_answer="42"
    )
    assert is_corr is False
    assert "NaN and Infinity are not permitted" in fb


def test_subjective_evaluator_rubric_and_misconceptions():
    rubric = Rubric(
        rubric_id="rub_thermo",
        title="Thermodynamics Rubric",
        criteria=[
            RubricCriterion("conceptual_accuracy", "Concepts", max_points=4.0, weight=1.0),
            RubricCriterion("clarity", "Clarity", max_points=4.0, weight=1.0),
        ],
    )
    item = AssessmentItem(
        id="q_thermo",
        item_type=QuestionType.SUBJECTIVE,
        question_text="Explain the first law of thermodynamics and distinguish heat and work.",
        concept_id="thermo_law1",
        max_marks=10.0,
        correct_answer="Energy conservation where change in internal energy equals heat added minus work done by system.",
        rubric=rubric,
    )

    # 1. Answer with misconception: "heat is work"
    res_miscon = SubjectiveEvaluator.evaluate(
        item=item,
        student_answer="The first law means heat is work and energy is conserved.",
        rubric=rubric,
    )
    assert res_miscon.misconception_code == "MISCON_HEAT_WORK"
    assert "Misconception identified" in res_miscon.feedback
    assert res_miscon.is_correct is False

    # 2. Accurate answer
    res_correct = SubjectiveEvaluator.evaluate(
        item=item,
        student_answer="The first law represents energy conservation where change in internal energy equals heat added minus work done by the system in a thermodynamic cycle.",
        rubric=rubric,
    )
    assert res_correct.is_correct is True
    assert res_correct.score >= 7.0
    assert res_correct.ai_confidence >= 0.70


def test_coding_evaluator_syntax_and_test_cases():
    item = AssessmentItem(
        id="q_py_sum",
        item_type=QuestionType.CODING,
        question_text="Write a function add(a, b) that returns the sum.",
        concept_id="python_funcs",
        max_marks=10.0,
        test_cases=[
            {"function_name": "add", "input": [2, 3], "expected": 5},
            {"function_name": "add", "input": [-1, 1], "expected": 0},
            {"function_name": "add", "input": [0, 0], "expected": 0},
        ],
    )

    # 1. Correct code
    good_code = "def add(a, b):\n    return a + b\n"
    res_good = CodingEvaluator.evaluate(item, good_code)
    assert res_good.is_correct is True
    assert res_good.score == 10.0

    # 2. Partially correct code
    buggy_code = "def add(a, b):\n    return a * b\n"
    res_buggy = CodingEvaluator.evaluate(item, buggy_code)
    assert res_buggy.is_correct is False
    assert res_buggy.score < 10.0

    # 3. Syntax error
    syntax_code = "def add(a, b\n    return a + b"
    res_syntax = CodingEvaluator.evaluate(item, syntax_code)
    assert res_syntax.is_correct is False
    assert "SyntaxError" in res_syntax.feedback


def test_adaptive_difficulty_progression():
    items = [
        AssessmentItem("q1", QuestionType.MCQ, "Diff 1", "c1", difficulty=1),
        AssessmentItem("q2", QuestionType.MCQ, "Diff 2", "c1", difficulty=2),
        AssessmentItem("q3", QuestionType.MCQ, "Diff 3", "c1", difficulty=3),
        AssessmentItem("q4", QuestionType.MCQ, "Diff 4", "c1", difficulty=4),
        AssessmentItem("q5", QuestionType.MCQ, "Diff 5", "c1", difficulty=5),
    ]

    # Success on difficulty 2 -> progresses to difficulty 3
    next_item = AdaptiveEngine.select_next_item(
        current_difficulty=2,
        is_previous_correct=True,
        available_items=items,
        answered_ids={"q1", "q2"},
    )
    assert next_item is not None
    assert next_item.id == "q3"
    assert next_item.difficulty == 3

    # Failure on difficulty 3 -> scaffolds back to difficulty 2 (or closest available)
    next_scaffold = AdaptiveEngine.select_next_item(
        current_difficulty=3,
        is_previous_correct=False,
        available_items=items,
        answered_ids={"q2", "q3"},
    )
    assert next_scaffold is not None
    assert next_scaffold.difficulty <= 2


def test_anti_leakage_sanitizer():
    item = {
        "id": "q1",
        "item_type": "MCQ",
        "question_text": "What is 2+2?",
        "options": ["3", "4", "5"],
        "correct_answer": "4",
        "correct_index": 1,
        "explanation": "2+2 equals 4 by basic arithmetic.",
        "internal_notes": "Very easy question.",
        "hints": ["Count on fingers."],
    }
    sanitized = AssessmentSanitizer.sanitize_item_for_student(item, allow_hints=False)
    assert "correct_answer" not in sanitized
    assert "correct_index" not in sanitized
    assert "explanation" not in sanitized
    assert "internal_notes" not in sanitized
    assert "hints" not in sanitized
    assert AssessmentSanitizer.verify_no_leakage(sanitized) is True


# --- 2. End-to-End Assessment Lifecycle & Security Tests ---


@pytest.mark.asyncio
async def test_full_assessment_lifecycle_and_grading(assess_test_client: AsyncClient):
    # 1. Register Teacher (who creates Org) and Student
    teacher_user, teacher_token = await register_and_login(
        assess_test_client, "prof.physics@example.internal", "Prof Physics"
    )
    org_res = await assess_test_client.post(
        "/api/v1/organizations",
        json={"name": "Physics Academy", "slug": "physics-acad"},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert org_res.status_code == 201
    org_id = org_res.json()["id"]
    teacher_headers = {"Authorization": f"Bearer {teacher_token}", "X-Organization-ID": org_id}

    # Register Student Alice
    alice_user, alice_token = await register_and_login(
        assess_test_client, "alice.phys@example.internal", "Alice Learner"
    )
    # Invite Alice to Org as STUDENT
    inv_res = await assess_test_client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "alice.phys@example.internal", "proposed_role": "STUDENT"},
        headers=teacher_headers,
    )
    await assess_test_client.post(
        "/api/v1/organizations/invitations/accept",
        json={"token": inv_res.json()["token"]},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    alice_headers = {"Authorization": f"Bearer {alice_token}", "X-Organization-ID": org_id}

    # Register Other Student Bob (in a different organization)
    bob_user, bob_token = await register_and_login(
        assess_test_client, "bob.chem@example.internal", "Bob Chemistry"
    )
    bob_org_res = await assess_test_client.post(
        "/api/v1/organizations",
        json={"name": "Chemistry Academy", "slug": "chem-acad"},
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    bob_org_id = bob_org_res.json()["id"]
    bob_headers = {"Authorization": f"Bearer {bob_token}", "X-Organization-ID": bob_org_id}

    # 2. Teacher creates Course, Publishes version, and Deploys offering
    crs_res = await assess_test_client.post(
        "/api/v1/courses",
        json={"code": "PHY101", "title": "Classical Mechanics"},
        headers=teacher_headers,
    )
    course_id = crs_res.json()["id"]

    v_res = await assess_test_client.get(
        f"/api/v1/courses/{course_id}/versions", headers=teacher_headers
    )
    version_id = v_res.json()[0]["id"]
    await assess_test_client.post(
        f"/api/v1/courses/{course_id}/versions/{version_id}/publish", headers=teacher_headers
    )

    off_res = await assess_test_client.post(
        "/api/v1/courses/offerings",
        json={"course_version_id": version_id, "term": "Spring 2026"},
        headers=teacher_headers,
    )
    offering_id = off_res.json()["id"]

    # Enroll Alice in Offering
    enr_res = await assess_test_client.post(
        f"/api/v1/courses/offerings/{offering_id}/enroll",
        json={"student_id": alice_user["id"]},
        headers=teacher_headers,
    )
    assert enr_res.status_code == 201, f"Enroll failed: {enr_res.text}"

    # 3. Teacher creates an Assessment with MCQ, Numerical, and Subjective items
    items_def = [
        {
            "id": "item_mcq_1",
            "item_type": "MCQ",
            "question_text": "What is SI unit of Force?",
            "concept_id": "mechanics_force",
            "max_marks": 5.0,
            "options": ["Joule", "Newton", "Watt", "Pascal"],
            "correct_answer": "Newton",
            "explanation": "Force is measured in Newtons (N).",
        },
        {
            "id": "item_num_1",
            "item_type": "NUMERICAL",
            "question_text": "Calculate acceleration due to gravity on Earth surface.",
            "concept_id": "mechanics_gravity",
            "max_marks": 5.0,
            "correct_answer": "9.8 m/s^2",
            "expected_unit": "m/s^2",
            "tolerance_pct": 2.0,
        },
        {
            "id": "item_subj_1",
            "item_type": "SUBJECTIVE",
            "question_text": "State Newton's third law of motion and give an example.",
            "concept_id": "mechanics_newton3",
            "max_marks": 10.0,
            "correct_answer": "For every action there is an equal and opposite reaction.",
        },
    ]

    create_res = await assess_test_client.post(
        "/api/v1/assessments",
        headers=teacher_headers,
        json={
            "offering_id": offering_id,
            "title": "Midterm Physics Exam",
            "assessment_type": "TIMED_EXAM",
            "total_points": 20.0,
            "time_limit_minutes": 60,
            "passing_score": 70.0,
            "items": items_def,
        },
    )
    assert create_res.status_code == 201
    assessment_id = create_res.json()["id"]

    # 4. Student tries to get unpublished assessment -> 403 Forbidden
    unpub_res = await assess_test_client.get(
        f"/api/v1/assessments/{assessment_id}", headers=alice_headers
    )
    assert unpub_res.status_code == 403

    # 5. Teacher publishes assessment
    pub_res = await assess_test_client.post(
        f"/api/v1/assessments/{assessment_id}/publish", headers=teacher_headers
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["is_published"] is True

    # 6. Alice views assessment -> Verified leak-free (no correct_answer or explanation)
    stud_view_res = await assess_test_client.get(
        f"/api/v1/assessments/{assessment_id}", headers=alice_headers
    )
    assert stud_view_res.status_code == 200
    stud_view = stud_view_res.json()
    assert len(stud_view["items"]) == 3
    for itm in stud_view["items"]:
        assert "correct_answer" not in itm
        assert "explanation" not in itm

    # 7. Alice starts attempt
    start_res = await assess_test_client.post(
        f"/api/v1/assessments/{assessment_id}/attempts", headers=alice_headers
    )
    assert start_res.status_code == 201
    attempt_id = start_res.json()["id"]
    assert start_res.json()["status"] == "in_progress"

    # 8. Alice autosaves draft
    draft_payload = {"item_mcq_1": "Newton", "item_num_1": "9.81 m/s^2"}
    save_res = await assess_test_client.put(
        f"/api/v1/assessments/attempts/{attempt_id}/autosave",
        headers=alice_headers,
        json={"draft_answers": draft_payload},
    )
    assert save_res.status_code == 200

    # Verify draft saved
    get_att = await assess_test_client.get(
        f"/api/v1/assessments/attempts/{attempt_id}", headers=alice_headers
    )
    assert get_att.json()["draft_answers"] == draft_payload

    # 9. Alice submits attempt
    submission_answers = {
        "item_mcq_1": "Option B",  # Matches "Newton"
        "item_num_1": "9.81 m/s^2",  # Within ±2% tolerance
        "item_subj_1": "For every action there is an equal and opposite reaction, like rocket propulsion.",
    }
    submit_res = await assess_test_client.post(
        f"/api/v1/assessments/attempts/{attempt_id}/submit",
        headers=alice_headers,
        json={"answers": submission_answers, "idempotency_key": "idemp_test_1"},
    )
    assert submit_res.status_code == 200
    summary = submit_res.json()
    assert summary["passed"] is True
    assert summary["total_score"] >= 14.0  # >= 70% of 20 points
    assert len(summary["item_results"]) == 3
    assert summary["item_results"]["item_mcq_1"]["is_correct"] is True
    assert summary["item_results"]["item_num_1"]["is_correct"] is True
    assert summary["item_results"]["item_subj_1"]["is_correct"] is True

    # 10. Idempotency test: Re-submitting returns identical graded summary without error
    resubmit_res = await assess_test_client.post(
        f"/api/v1/assessments/attempts/{attempt_id}/submit",
        headers=alice_headers,
        json={"answers": submission_answers, "idempotency_key": "idemp_test_1"},
    )
    assert resubmit_res.status_code == 200
    assert resubmit_res.json()["total_score"] == summary["total_score"]

    # 11. Security negative test: Bob (in other organization) cannot access Alice's attempt
    neg_res = await assess_test_client.get(
        f"/api/v1/assessments/attempts/{attempt_id}", headers=bob_headers
    )
    assert neg_res.status_code == 403

    # 12. Teacher manual override of a score
    att_details = (
        await assess_test_client.get(
            f"/api/v1/assessments/attempts/{attempt_id}", headers=teacher_headers
        )
    ).json()
    resp_id = att_details["responses"][0]["id"]
    override_res = await assess_test_client.post(
        f"/api/v1/assessments/attempts/{attempt_id}/override",
        headers=teacher_headers,
        json={
            "overrides": [
                {"response_id": resp_id, "override_score": 5.0, "comment": "Full marks verified."}
            ]
        },
    )
    assert override_res.status_code == 200
    assert override_res.json()["status"] == "graded"
