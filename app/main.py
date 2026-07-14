from fastapi import FastAPI

from app.api.exceptions import register_exception_handlers
from app.api.router import api_router
from app.lifespan import lifespan


app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)
app.include_router(api_router)
