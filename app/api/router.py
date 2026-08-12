from fastapi import APIRouter

from app.modules.auth.module import router as auth_router, webhook_router as auth_webhook_router
from app.modules.ticket_management.module import attachments_router, comments_router, router as ticket_management_router
from app.modules.audit.module import router as audit_router
from app.modules.notifications.module import router as notifications_router, sse_router as notifications_sse_router
from app.modules.analytics.module import router as analytics_router
from app.modules.knowledge_base.module import router as knowledge_base_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(auth_webhook_router)
api_router.include_router(ticket_management_router)
api_router.include_router(comments_router)
api_router.include_router(attachments_router)
api_router.include_router(audit_router)
api_router.include_router(notifications_router)
api_router.include_router(notifications_sse_router)
api_router.include_router(analytics_router)
api_router.include_router(knowledge_base_router)
