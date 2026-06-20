"""Rubric seed data — default rubrics for different question types."""

from app.services.rubric_evaluator import DEFAULT_RUBRICS


def get_seed_rubrics():
    """Get default rubrics as dictionary list for database seeding."""
    rubrics = []
    
    for key, rubric in DEFAULT_RUBRICS.items():
        criteria = []
        for criterion in rubric.criteria:
            criteria.append({
                "id": criterion.id,
                "name": criterion.name,
                "description": criterion.description,
                "weight": criterion.weight,
                "max_score": criterion.max_score,
            })
        
        rubrics.append({
            "name": rubric.name,
            "description": rubric.description,
            "question_type": key,
            "criteria": criteria,
            "is_default": True,
        })
    
    return rubrics
