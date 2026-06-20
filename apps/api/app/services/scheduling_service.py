"""Scheduling service — availability and interview scheduling."""

import uuid
from datetime import datetime, time
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.availability import AvailabilitySlot, ScheduledInterview
from app.models.interview import Interview


async def get_availability(
    db: AsyncSession, user_id: uuid.UUID
) -> List[Dict[str, Any]]:
    result = await db.execute(
        select(AvailabilitySlot)
        .where(AvailabilitySlot.user_id == user_id, AvailabilitySlot.is_active)
        .order_by(AvailabilitySlot.day_of_week, AvailabilitySlot.start_time)
    )
    return [
        {
            "id": str(s.id),
            "day_of_week": s.day_of_week,
            "start_time": s.start_time.strftime("%H:%M"),
            "end_time": s.end_time.strftime("%H:%M"),
            "timezone": s.timezone,
        }
        for s in result.scalars().all()
    ]


async def set_availability(
    db: AsyncSession,
    user_id: uuid.UUID,
    slots: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    await db.execute(
        select(AvailabilitySlot).where(AvailabilitySlot.user_id == user_id)
    )
    existing_result = await db.execute(
        select(AvailabilitySlot).where(AvailabilitySlot.user_id == user_id)
    )
    for existing in existing_result.scalars().all():
        existing.is_active = False

    created = []
    for slot in slots:
        start_parts = slot["start_time"].split(":")
        end_parts = slot["end_time"].split(":")
        new_slot = AvailabilitySlot(
            user_id=user_id,
            day_of_week=slot["day_of_week"],
            start_time=time(int(start_parts[0]), int(start_parts[1])),
            end_time=time(int(end_parts[0]), int(end_parts[1])),
            timezone=slot.get("timezone", "UTC"),
            is_active=True,
        )
        db.add(new_slot)
        created.append(new_slot)
    await db.flush()
    return [
        {
            "id": str(s.id),
            "day_of_week": s.day_of_week,
            "start_time": s.start_time.strftime("%H:%M"),
            "end_time": s.end_time.strftime("%H:%M"),
            "timezone": s.timezone,
        }
        for s in created
    ]


async def schedule_interview(
    db: AsyncSession,
    interview_id: uuid.UUID,
    candidate_id: uuid.UUID,
    scheduled_at: datetime,
    duration_minutes: int = 60,
    interviewer_id: Optional[uuid.UUID] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    scheduled = ScheduledInterview(
        interview_id=interview_id,
        candidate_id=candidate_id,
        interviewer_id=interviewer_id,
        scheduled_at=scheduled_at,
        duration_minutes=duration_minutes,
        notes=notes,
    )
    db.add(scheduled)
    await db.flush()

    interview_result = await db.execute(
        select(Interview).where(Interview.id == interview_id)
    )
    interview = interview_result.scalar_one_or_none()
    if interview:
        interview.status = "scheduled"
        await db.flush()

    return {
        "id": str(scheduled.id),
        "interview_id": str(scheduled.interview_id),
        "scheduled_at": scheduled.scheduled_at.isoformat(),
        "duration_minutes": scheduled.duration_minutes,
        "status": scheduled.status,
    }


async def get_scheduled_interviews(
    db: AsyncSession,
    interviewer_id: Optional[uuid.UUID] = None,
    candidate_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    stmt = select(ScheduledInterview)
    if interviewer_id:
        stmt = stmt.where(ScheduledInterview.interviewer_id == interviewer_id)
    if candidate_id:
        stmt = stmt.where(ScheduledInterview.candidate_id == candidate_id)
    if status:
        stmt = stmt.where(ScheduledInterview.status == status)
    stmt = stmt.order_by(ScheduledInterview.scheduled_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": str(s.id),
                "interview_id": str(s.interview_id),
                "candidate_id": str(s.candidate_id),
                "interviewer_id": str(s.interviewer_id) if s.interviewer_id else None,
                "scheduled_at": s.scheduled_at.isoformat(),
                "duration_minutes": s.duration_minutes,
                "status": s.status,
                "meet_link": s.meet_link,
                "notes": s.notes,
            }
            for s in items
        ],
        "total": len(items),
        "page": page,
        "page_size": page_size,
    }


async def reschedule_interview(
    db: AsyncSession,
    scheduled_id: uuid.UUID,
    new_scheduled_at: datetime,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    result = await db.execute(
        select(ScheduledInterview).where(ScheduledInterview.id == scheduled_id)
    )
    scheduled = result.scalar_one_or_none()
    if not scheduled:
        raise ValueError("Scheduled interview not found")

    scheduled.scheduled_at = new_scheduled_at
    scheduled.reschedule_count += 1
    scheduled.status = "rescheduled"
    if notes:
        scheduled.notes = notes
    await db.flush()

    return {
        "id": str(scheduled.id),
        "scheduled_at": scheduled.scheduled_at.isoformat(),
        "status": scheduled.status,
        "reschedule_count": scheduled.reschedule_count,
    }


async def cancel_scheduled_interview(
    db: AsyncSession, scheduled_id: uuid.UUID
) -> Dict[str, Any]:
    result = await db.execute(
        select(ScheduledInterview).where(ScheduledInterview.id == scheduled_id)
    )
    scheduled = result.scalar_one_or_none()
    if not scheduled:
        raise ValueError("Scheduled interview not found")

    scheduled.status = "cancelled"
    await db.flush()

    interview_result = await db.execute(
        select(Interview).where(Interview.id == scheduled.interview_id)
    )
    interview = interview_result.scalar_one_or_none()
    if interview:
        interview.status = "cancelled"
        await db.flush()

    return {"id": str(scheduled.id), "status": "cancelled"}
