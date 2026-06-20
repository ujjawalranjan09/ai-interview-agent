"""Calendar integration service — Google Calendar, Outlook, .ics generation."""
from datetime import timedelta

import httpx
from icalendar import Calendar, Event

from app.models.interview import Interview
from app.models.candidate import Candidate
from app.models.availability import ScheduledInterview


async def create_google_calendar_event(
    credential: dict,
    slot: ScheduledInterview,
    interview: Interview,
    candidate: Candidate,
) -> str:
    access_token = credential.get("access_token", "")
    start_time = slot.scheduled_at
    end_time = start_time + timedelta(minutes=slot.duration_minutes)

    event = {
        "summary": f"Interview: {candidate.name}",
        "description": f"AI Interview with {candidate.name}",
        "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
        "attendees": [{"email": candidate.email}] if candidate.email else [],
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers={"Authorization": f"Bearer {access_token}"},
            json=event,
        )
        if resp.is_success:
            return resp.json().get("id", "")
        return ""


async def create_outlook_event(
    credential: dict,
    slot: ScheduledInterview,
    interview: Interview,
    candidate: Candidate,
) -> str:
    access_token = credential.get("access_token", "")
    start_time = slot.scheduled_at
    end_time = start_time + timedelta(minutes=slot.duration_minutes)

    event = {
        "subject": f"Interview: {candidate.name}",
        "body": {"contentType": "Text", "content": f"AI Interview with {candidate.name}"},
        "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
        "attendees": [{"emailAddress": {"address": candidate.email}}] if candidate.email else [],
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            "https://graph.microsoft.com/v1.0/me/events",
            headers={"Authorization": f"Bearer {access_token}"},
            json=event,
        )
        if resp.is_success:
            return resp.json().get("id", "")
        return ""


async def generate_ics_file(
    slot: ScheduledInterview,
    interview: Interview,
    candidate: Candidate,
) -> bytes:
    cal = Calendar()
    cal.add("prodid", "-//AI Interview Agent//EN")
    cal.add("version", "2.0")

    event = Event()
    event.add("summary", f"Interview: {candidate.name}")
    event.add("dtstart", slot.scheduled_at)
    event.add("dtend", slot.scheduled_at + timedelta(minutes=slot.duration_minutes))
    event.add("description", f"AI Interview with {candidate.name}")
    if candidate.email:
        event.add("attendee", candidate.email)
    cal.add_component(event)
    return cal.to_ical()
