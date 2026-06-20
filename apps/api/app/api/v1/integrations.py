"""Integrations API endpoints — Slack, Teams, ATS."""

import uuid
from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.slack_integration import SlackIntegration
from app.schemas.integration import SlackConnectRequest
from app.models.teams_integration import TeamsIntegration
from app.models.ats_integration import ATSIntegrationConfig
from app.services import slack_service, teams_service
from app.services.ats.greenhouse import GreenhouseIntegration
from app.services.ats.lever import LeverIntegration

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.post("/slack")
async def connect_slack(
    body: SlackConnectRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    integration = SlackIntegration(
        user_id=user.id,
        organization_id=getattr(user, "organization_id", None),
        webhook_url=body.webhook_url,
        channel_name=body.channel_name,
        events=body.events,
    )
    db.add(integration)
    await db.flush()
    return {"id": str(integration.id), "channel_name": integration.channel_name, "events": integration.events, "is_active": True}


@router.get("/slack")
async def list_slack(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SlackIntegration).where(SlackIntegration.user_id == user.id).order_by(SlackIntegration.created_at.desc())
    )
    return [
        {
            "id": str(s.id),
            "channel_name": s.channel_name,
            "events": s.events,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in result.scalars().all()
    ]


@router.delete("/slack/{integration_id}")
async def delete_slack(
    integration_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SlackIntegration).where(SlackIntegration.id == integration_id, SlackIntegration.user_id == user.id)
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    await db.delete(integration)
    await db.flush()
    return {"status": "deleted"}


@router.post("/slack/{integration_id}/test")
async def test_slack(
    integration_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SlackIntegration).where(SlackIntegration.id == integration_id, SlackIntegration.user_id == user.id)
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    test_msg = {
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": "Test Notification ✅"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": "Your Slack integration is working correctly!"}},
        ]
    }
    success = await slack_service.send_slack_notification(integration.webhook_url, test_msg)
    if not success:
        raise HTTPException(status_code=502, detail="Failed to send test message")
    return {"status": "test_sent"}


@router.post("/teams")
async def connect_teams(
    body: SlackConnectRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    integration = TeamsIntegration(
        user_id=user.id,
        organization_id=getattr(user, "organization_id", None),
        webhook_url=body.webhook_url,
        channel_name=body.channel_name,
        events=body.events,
    )
    db.add(integration)
    await db.flush()
    return {"id": str(integration.id), "channel_name": integration.channel_name, "events": integration.events, "is_active": True}


@router.get("/teams")
async def list_teams(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(TeamsIntegration).where(TeamsIntegration.user_id == user.id).order_by(TeamsIntegration.created_at.desc())
    )
    return [
        {"id": str(s.id), "channel_name": s.channel_name, "events": s.events, "is_active": s.is_active,
         "created_at": s.created_at.isoformat() if s.created_at else None}
        for s in result.scalars().all()
    ]


@router.delete("/teams/{integration_id}")
async def delete_teams(
    integration_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(TeamsIntegration).where(TeamsIntegration.id == integration_id, TeamsIntegration.user_id == user.id)
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    await db.delete(integration)
    await db.flush()
    return {"status": "deleted"}


@router.post("/teams/{integration_id}/test")
async def test_teams(
    integration_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(TeamsIntegration).where(TeamsIntegration.id == integration_id, TeamsIntegration.user_id == user.id)
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    test_card = {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard", "version": "1.4",
                "body": [{"type": "TextBlock", "text": "Test notification — your Teams integration is working!"}],
            },
        }],
    }
    success = await teams_service.send_teams_notification(integration.webhook_url, test_card)
    if not success:
        raise HTTPException(status_code=502, detail="Failed to send test message")
    return {"status": "test_sent"}


def _get_ats_provider(config: dict, provider: str) -> Any:
    if provider == "greenhouse":
        return GreenhouseIntegration(config)
    elif provider == "lever":
        return LeverIntegration(config)
    return None


@router.post("/ats")
async def connect_ats(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    org_id = getattr(user, "organization_id", None)
    if not org_id:
        raise HTTPException(status_code=400, detail="No organization associated")
    ats = ATSIntegrationConfig(
        organization_id=org_id,
        provider=body["provider"],
        config=body.get("config", {}),
        sync_direction=body.get("sync_direction", "push"),
    )
    db.add(ats)
    await db.flush()
    return {"id": str(ats.id), "provider": ats.provider, "is_active": True}


@router.get("/ats")
async def list_ats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    org_id = getattr(user, "organization_id", None)
    stmt = select(ATSIntegrationConfig)
    if org_id:
        stmt = stmt.where(ATSIntegrationConfig.organization_id == org_id)
    result = await db.execute(stmt.order_by(ATSIntegrationConfig.created_at.desc()))
    return [
        {"id": str(a.id), "provider": a.provider, "sync_direction": a.sync_direction, "is_active": a.is_active,
         "last_sync_at": a.last_sync_at.isoformat() if a.last_sync_at else None}
        for a in result.scalars().all()
    ]


@router.delete("/ats/{integration_id}")
async def delete_ats(
    integration_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(ATSIntegrationConfig).where(ATSIntegrationConfig.id == integration_id))
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    await db.delete(integration)
    await db.flush()
    return {"status": "deleted"}


@router.post("/ats/{integration_id}/sync")
async def sync_ats(
    integration_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(ATSIntegrationConfig).where(ATSIntegrationConfig.id == integration_id))
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    provider = _get_ats_provider(integration.config, integration.provider)
    if not provider:
        raise HTTPException(status_code=400, detail="Unknown provider")
    try:
        candidates = await provider.pull_candidates()
        integration.last_sync_at = datetime.utcnow()
        await db.flush()
        return {"status": "synced", "candidates_pulled": len(candidates)}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/ats/{integration_id}/push/{interview_id}")
async def push_to_ats(
    integration_id: uuid.UUID,
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.models.interview import Interview
    from app.models.candidate import Candidate
    ats_result = await db.execute(select(ATSIntegrationConfig).where(ATSIntegrationConfig.id == integration_id))
    integration = ats_result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    interview_result = await db.execute(select(Interview).where(Interview.id == interview_id))
    interview = interview_result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    candidate_result = await db.execute(select(Candidate).where(Candidate.id == interview.candidate_id))
    candidate = candidate_result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    provider = _get_ats_provider(integration.config, integration.provider)
    if not provider:
        raise HTTPException(status_code=400, detail="Unknown provider")
    try:
        ext_id = await provider.push_candidate(candidate)
        await provider.push_interview(interview, ext_id)
        return {"status": "pushed", "external_candidate_id": ext_id}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
