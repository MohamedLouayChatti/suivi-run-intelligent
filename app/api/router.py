from fastapi import APIRouter

from app.modules.ticket_management.module import attachments_router, comments_router, router as ticket_management_router

api_router = APIRouter()
api_router.include_router(ticket_management_router)
api_router.include_router(comments_router)
api_router.include_router(attachments_router)
