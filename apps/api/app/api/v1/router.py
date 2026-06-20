"""V1 API router — aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.candidates import router as candidates_router
from app.api.v1.interviews import router as interviews_router
from app.api.v1.questions import router as questions_router
from app.api.v1.events import router as events_router
from app.api.v1.reports import router as reports_router
from app.api.v1.coaching import router as coaching_router
from app.api.v1.replay import router as replay_router
from app.api.v1.copilot import router as copilot_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.jd import router as jd_router
from app.api.v1.admin import router as admin_router
from app.api.v1.audit import router as audit_router
from app.api.v1.export import router as export_router
from app.api.v1.banks import router as banks_router
from app.api.v1.templates import router as templates_router
from app.api.v1.coding import router as coding_router
from app.api.v1.portal import router as portal_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.search import router as search_router
from app.api.v1.gdpr import router as gdpr_router
from app.api.v1.scheduling import router as scheduling_router
from app.api.v1.bulk import router as bulk_router
from app.api.v1.proctoring import router as proctoring_router
from app.api.v1.plagiarism import router as plagiarism_router
from app.api.v1.branding import router as branding_router
from app.api.v1.dev import router as dev_router
from app.api.v1.screening import router as screening_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.auth_google import router as auth_google_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.feature_flags import router as feature_flags_router
from app.api.v1.health import router as health_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(auth_google_router)
api_router.include_router(candidates_router)
api_router.include_router(interviews_router)
api_router.include_router(questions_router)
api_router.include_router(events_router)
api_router.include_router(reports_router)
api_router.include_router(coaching_router)
api_router.include_router(replay_router)
api_router.include_router(copilot_router)
api_router.include_router(analytics_router)
api_router.include_router(jd_router)
api_router.include_router(admin_router)
api_router.include_router(audit_router)
api_router.include_router(export_router)
api_router.include_router(banks_router)
api_router.include_router(templates_router)
api_router.include_router(coding_router)
api_router.include_router(portal_router)
api_router.include_router(webhooks_router)
api_router.include_router(organizations_router)
api_router.include_router(search_router)
api_router.include_router(gdpr_router)
api_router.include_router(scheduling_router)
api_router.include_router(bulk_router)
api_router.include_router(proctoring_router)
api_router.include_router(plagiarism_router)
api_router.include_router(branding_router)
api_router.include_router(dev_router)
api_router.include_router(screening_router)
api_router.include_router(integrations_router)
api_router.include_router(notifications_router)
api_router.include_router(feature_flags_router)
api_router.include_router(health_router)
