"""Teams integration service — Adaptive Card notifications via webhook."""

import httpx

from app.models.interview import Interview
from app.models.candidate import Candidate


async def send_teams_notification(webhook_url: str, card: dict) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(webhook_url, json=card)
            return resp.is_success
    except Exception:
        return False


def format_interview_card(interview: Interview, candidate: Candidate) -> dict:
    return {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {"type": "TextBlock", "size": "Medium", "weight": "Bolder", "text": "Interview Completed ✅"},
                    {"type": "FactSet", "facts": [
                        {"title": "Candidate", "value": candidate.name},
                        {"title": "Score", "value": f"{interview.total_score:.1f}"},
                        {"title": "Questions", "value": f"{interview.questions_answered}/{interview.question_count}"},
                        {"title": "Status", "value": interview.status},
                    ]},
                ],
                "actions": [{"type": "Action.OpenUrl", "title": "View Report", "url": f"/dashboard/interviews/{interview.id}"}],
            },
        }],
    }


def format_report_card(interview_id: str, score: float) -> dict:
    return {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {"type": "TextBlock", "size": "Medium", "weight": "Bolder", "text": "Report Ready 📊"},
                    {"type": "TextBlock", "text": f"Interview report is ready with a score of *{score:.1f}*."},
                ],
                "actions": [{"type": "Action.OpenUrl", "title": "View Report", "url": f"/dashboard/interviews/{interview_id}"}],
            },
        }],
    }
