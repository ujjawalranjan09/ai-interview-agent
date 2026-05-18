import pytest
from unittest.mock import MagicMock
from modules.orchestrator.interview_controller import InterviewController
from app.constants import InterviewState

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def controller(mock_db):
    return InterviewController()

def test_controller_initial_state(controller):
    assert controller.state_machine.current_state == InterviewState.IDLE

def test_controller_start_interview(controller):
    # Mock resume data
    candidate_data = {
        "name": "Test User",
        "email": "test@example.com",
        "skills": ["Python", "Unit Testing"],
        "projects": ["Test Project"]
    }

    # We need to mock more things if we want to run full flow,
    # but let's test state transitions via controller
    assert controller.state_machine.current_state == InterviewState.IDLE

    # Transition to resume processing
    success = controller.state_machine.transition(InterviewState.RESUME_PROCESSING)
    assert success
    assert controller.state_machine.current_state == InterviewState.RESUME_PROCESSING

def test_controller_invalid_transition(controller):
    # Try to jump to completed from idle
    success = controller.state_machine.transition(InterviewState.COMPLETED)
    assert not success
    assert controller.state_machine.current_state == InterviewState.IDLE

def test_performance_metrics_calculation():
    from modules.analytics.performance_engine import calculate_performance_metrics

    questions = [
        {
            "answer_score": 80,
            "question_type": "technical",
            "difficulty": "medium",
            "semantic_similarity_score": 80,
            "keyword_match_score": 80,
            "concept_coverage_score": 80
        },
        {
            "answer_score": 60,
            "question_type": "behavioral",
            "difficulty": "easy",
            "semantic_similarity_score": 60,
            "keyword_match_score": 60,
            "concept_coverage_score": 60
        }
    ]

    metrics = calculate_performance_metrics(questions)
    assert metrics["average_score"] == 70.0
    assert metrics["questions_answered"] == 2
    assert "technical" in metrics["scores_by_type"]
    assert "behavioral" in metrics["scores_by_type"]
    assert metrics["scores_by_type"]["technical"] == 80.0
    assert metrics["scores_by_type"]["behavioral"] == 60.0
