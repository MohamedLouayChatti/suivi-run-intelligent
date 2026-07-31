from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exceptions import register_exception_handlers
from app.api.router import api_router
from app.lifespan import lifespan
from app.shared.config.settings import get_settings


app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)

settings = get_settings()
app.add_middleware(
	CORSMiddleware,
	allow_origins=settings.cors_allowed_origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(api_router)
