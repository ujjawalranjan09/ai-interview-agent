"""Slack integration service — webhook notifications via Block Kit."""

import httpx

from app.models.interview import Interview
from app.models.candidate import Candidate


async def send_slack_notification(webhook_url: str, message: dict) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(webhook_url, json=message)
            return resp.is_success
    except Exception:
        return False


def format_interview_completed(interview: Interview, candidate: Candidate) -> dict:
    return {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Interview Completed ✅"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Candidate:* {candidate.name}"},
                    {"type": "mrkdwn", "text": f"*Score:* {interview.total_score:.1f}"},
                    {"type": "mrkdwn", "text": f"*Questions:* {interview.questions_answered}/{interview.question_count}"},
                    {"type": "mrkdwn", "text": f"*Status:* {interview.status}"},
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Report"},
                        "url": f"/dashboard/interviews/{interview.id}",
                        "action_id": "view_report",
                    }
                ],
            },
        ]
    }


def format_report_ready(interview_id: str, score: float) -> dict:
    return {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Report Ready 📊"},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"Interview report is ready with a score of *{score:.1f}*."},
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Report"},
                        "url": f"/dashboard/interviews/{interview_id}",
                        "action_id": "view_report",
                    }
                ],
            },
        ]
    }


def format_daily_summary(interviews: list, stats: dict) -> dict:
    return {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Daily Summary 📋"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Interviews:* {stats.get('total', 0)}"},
                    {"type": "mrkdwn", "text": f"*Avg Score:* {stats.get('avg_score', 0):.1f}"},
                ],
            },
        ]
    }
