"""Rubric-based answer evaluator — extended scoring with criteria."""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RubricCriterion:
    """A single rubric criterion."""
    id: str
    name: str
    description: str
    weight: float
    max_score: float = 100.0


@dataclass
class Rubric:
    """A rubric for evaluating answers."""
    id: str
    name: str
    description: str
    criteria: List[RubricCriterion]
    total_weight: float = 0.0

    def __post_init__(self):
        self.total_weight = sum(c.weight for c in self.criteria)


# Pre-defined rubrics for different question types
DEFAULT_RUBRICS = {
    "technical": Rubric(
        id="technical-rubric",
        name="Technical Answer Rubric",
        description="Evaluates technical accuracy, depth, and clarity",
        criteria=[
            RubricCriterion(
                id="accuracy",
                name="Technical Accuracy",
                description="Correctness of technical information provided",
                weight=0.3,
            ),
            RubricCriterion(
                id="depth",
                name="Depth of Knowledge",
                description="Demonstrates understanding beyond surface level",
                weight=0.25,
            ),
            RubricCriterion(
                id="completeness",
                name="Completeness",
                description="Covers all important aspects of the question",
                weight=0.2,
            ),
            RubricCriterion(
                id="clarity",
                name="Clarity",
                description="Explanation is clear and well-organized",
                weight=0.15,
            ),
            RubricCriterion(
                id="examples",
                name="Examples",
                description="Provides relevant examples or applications",
                weight=0.1,
            ),
        ],
    ),
    "behavioral": Rubric(
        id="behavioral-rubric",
        name="Behavioral Answer Rubric",
        description="Evaluates STAR method and behavioral response quality",
        criteria=[
            RubricCriterion(
                id="situation",
                name="Situation Clarity",
                description="Clearly describes the context and situation",
                weight=0.2,
            ),
            RubricCriterion(
                id="task",
                name="Task Definition",
                description="Explains the specific task or responsibility",
                weight=0.15,
            ),
            RubricCriterion(
                id="action",
                name="Action Detail",
                description="Describes specific actions taken",
                weight=0.3,
            ),
            RubricCriterion(
                id="result",
                name="Result Impact",
                description="Quantifies or describes the outcome",
                weight=0.25,
            ),
            RubricCriterion(
                id="reflection",
                name="Learning/Reflection",
                description="Shows what was learned or how it applies",
                weight=0.1,
            ),
        ],
    ),
    "conceptual": Rubric(
        id="conceptual-rubric",
        name="Conceptual Answer Rubric",
        description="Evaluates understanding of concepts and principles",
        criteria=[
            RubricCriterion(
                id="definition",
                name="Definition Accuracy",
                description="Correctly defines the concept",
                weight=0.25,
            ),
            RubricCriterion(
                id="explanation",
                name="Explanation Depth",
                description="Explains how and why it works",
                weight=0.3,
            ),
            RubricCriterion(
                id="connections",
                name="Connections",
                description="Relates to other concepts or real-world applications",
                weight=0.2,
            ),
            RubricCriterion(
                id="critique",
                name="Critical Analysis",
                description="Discusses strengths, weaknesses, or trade-offs",
                weight=0.25,
            ),
        ],
    ),
}


def get_rubric(question_type: str) -> Rubric:
    """Get rubric for question type, fallback to technical."""
    return DEFAULT_RUBRICS.get(question_type, DEFAULT_RUBRICS["technical"])


def evaluate_with_rubric(
    question: str,
    answer: str,
    question_type: str = "technical",
    custom_rubric: Optional[Rubric] = None,
) -> Dict[str, Any]:
    """Evaluate an answer using rubric-based scoring.
    
    Args:
        question: The question text
        answer: The candidate's answer
        question_type: Type of question (technical, behavioral, conceptual)
        custom_rubric: Optional custom rubric to use
        
    Returns:
        Dictionary with rubric scores and overall evaluation
    """
    if not answer or not answer.strip():
        return {
            "rubric_scores": {},
            "rubric_total": 0.0,
            "rubric_feedback": "No answer provided.",
            "criteria_scores": [],
        }

    rubric = custom_rubric or get_rubric(question_type)
    
    # Score each criterion
    criteria_scores = []
    total_weighted_score = 0.0
    
    for criterion in rubric.criteria:
        score = _score_criterion(criterion, question, answer)
        weighted_score = score * criterion.weight
        total_weighted_score += weighted_score
        
        criteria_scores.append({
            "criterion_id": criterion.id,
            "criterion_name": criterion.name,
            "score": round(score, 1),
            "weight": criterion.weight,
            "weighted_score": round(weighted_score, 1),
            "feedback": _criterion_feedback(criterion.id, score),
        })
    
    # Normalize to 0-100 scale
    rubric_total = (total_weighted_score / rubric.total_weight) * 100 if rubric.total_weight > 0 else 0
    
    # Generate overall feedback
    rubric_feedback = _generate_rubric_feedback(rubric_total, criteria_scores)
    
    return {
        "rubric_scores": {
            "total": round(rubric_total, 1),
            "rubric_name": rubric.name,
        },
        "rubric_total": round(rubric_total, 1),
        "rubric_feedback": rubric_feedback,
        "criteria_scores": criteria_scores,
    }


def _score_criterion(criterion: RubricCriterion, question: str, answer: str) -> float:
    """Score a single criterion based on answer analysis."""
    answer_lower = answer.lower()
    answer_words = answer.split()
    word_count = len(answer_words)
    
    base_score = 50.0  # Default middle score
    
    if criterion.id == "accuracy":
        # Technical accuracy: look for correct terminology
        technical_terms = [
            "algorithm", "function", "variable", "class", "method",
            "database", "api", "framework", "architecture", "pattern",
            "complexity", "performance", "security", "testing",
        ]
        term_count = sum(1 for term in technical_terms if term in answer_lower)
        base_score = min(100, 40 + term_count * 10)
        
    elif criterion.id == "depth":
        # Depth: check for detailed explanations
        depth_indicators = [
            "because", "therefore", "however", "specifically",
            "for example", "such as", "trade-off", "advantage",
            "implementation", "architecture", "design pattern",
            "in contrast", "alternatively", "furthermore",
        ]
        indicator_count = sum(1 for ind in depth_indicators if ind in answer_lower)
        base_score = min(100, 30 + indicator_count * 15)
        
    elif criterion.id == "completeness":
        # Completeness: check if multiple aspects are covered
        if word_count < 20:
            base_score = 30
        elif word_count < 50:
            base_score = 60
        else:
            base_score = 80
            
    elif criterion.id == "clarity":
        # Clarity: check for structured response
        structure_indicators = ["1.", "2.", "first", "second", "finally", "step"]
        structure_count = sum(1 for ind in structure_indicators if ind in answer_lower)
        base_score = min(100, 50 + structure_count * 15)
        
    elif criterion.id == "examples":
        # Examples: check for example-related words
        example_indicators = ["example", "instance", "case", "such as", "like", "including"]
        example_count = sum(1 for ind in example_indicators if ind in answer_lower)
        base_score = min(100, 40 + example_count * 20)
        
    elif criterion.id == "situation":
        # Situation clarity: check for context words
        context_indicators = ["when", "where", "during", "while", "at that time", "in that project"]
        context_count = sum(1 for ind in context_indicators if ind in answer_lower)
        base_score = min(100, 40 + context_count * 20)
        
    elif criterion.id == "task":
        # Task definition: check for responsibility words
        task_indicators = ["responsible for", "task was", "needed to", "required to", "goal"]
        task_count = sum(1 for ind in task_indicators if ind in answer_lower)
        base_score = min(100, 40 + task_count * 20)
        
    elif criterion.id == "action":
        # Action detail: check for action words
        action_indicators = ["implemented", "developed", "created", "designed", "led", "managed"]
        action_count = sum(1 for ind in action_indicators if ind in answer_lower)
        base_score = min(100, 30 + action_count * 15)
        
    elif criterion.id == "result":
        # Result impact: check for quantifiable outcomes
        result_indicators = ["increased", "decreased", "improved", "reduced", "%", "times", "hours"]
        result_count = sum(1 for ind in result_indicators if ind in answer_lower)
        base_score = min(100, 40 + result_count * 20)
        
    elif criterion.id == "reflection":
        # Reflection: check for learning words
        reflection_indicators = ["learned", "realized", "understand", "insight", "next time"]
        reflection_count = sum(1 for ind in reflection_indicators if ind in answer_lower)
        base_score = min(100, 40 + reflection_count * 20)
        
    elif criterion.id == "definition":
        # Definition accuracy: check for definition patterns
        definition_indicators = ["is a", "refers to", "means", "defined as", "can be described"]
        definition_count = sum(1 for ind in definition_indicators if ind in answer_lower)
        base_score = min(100, 40 + definition_count * 20)
        
    elif criterion.id == "explanation":
        # Explanation depth: check for how/why
        explanation_indicators = ["how", "why", "because", "reason", "mechanism", "process"]
        explanation_count = sum(1 for ind in explanation_indicators if ind in answer_lower)
        base_score = min(100, 40 + explanation_count * 15)
        
    elif criterion.id == "connections":
        # Connections: check for related concepts
        connection_indicators = ["similar to", "related to", "connects with", "used in", "applied to"]
        connection_count = sum(1 for ind in connection_indicators if ind in answer_lower)
        base_score = min(100, 40 + connection_count * 20)
        
    elif criterion.id == "critique":
        # Critical analysis: check for trade-offs
        critique_indicators = ["however", "but", "although", "trade-off", "limitation", "advantage"]
        critique_count = sum(1 for ind in critique_indicators if ind in answer_lower)
        base_score = min(100, 40 + critique_count * 15)
    
    # Add some variance based on answer length
    length_bonus = min(10, word_count / 10)
    base_score = min(100, base_score + length_bonus)
    
    return base_score


def _criterion_feedback(criterion_id: str, score: float) -> str:
    """Generate feedback for a specific criterion."""
    if score >= 80:
        level = "Excellent"
    elif score >= 60:
        level = "Good"
    elif score >= 40:
        level = "Needs improvement"
    else:
        level = "Poor"
    
    feedback_map = {
        "accuracy": f"{level} technical accuracy",
        "depth": f"{level} depth of knowledge",
        "completeness": f"{level} completeness of coverage",
        "clarity": f"{level} clarity of explanation",
        "examples": f"{level} use of examples",
        "situation": f"{level} situation description",
        "task": f"{level} task definition",
        "action": f"{level} action description",
        "result": f"{level} result articulation",
        "reflection": f"{level} reflection and learning",
        "definition": f"{level} definition accuracy",
        "explanation": f"{level} explanation depth",
        "connections": f"{level} concept connections",
        "critique": f"{level} critical analysis",
    }
    
    return feedback_map.get(criterion_id, f"{level} performance")


def _generate_rubric_feedback(total_score: float, criteria_scores: List[Dict]) -> str:
    """Generate overall rubric feedback."""
    parts = []
    
    if total_score >= 85:
        parts.append("Excellent response meeting high standards.")
    elif total_score >= 70:
        parts.append("Good response with room for improvement.")
    elif total_score >= 55:
        parts.append("Acceptable response, but could be stronger.")
    elif total_score >= 40:
        parts.append("Below average response, needs significant improvement.")
    else:
        parts.append("Poor response, major improvements needed.")
    
    # Find weakest criterion
    if criteria_scores:
        weakest = min(criteria_scores, key=lambda x: x["score"])
        if weakest["score"] < 50:
            parts.append(f"Focus on improving: {weakest['criterion_name']}.")
    
    return " ".join(parts)
