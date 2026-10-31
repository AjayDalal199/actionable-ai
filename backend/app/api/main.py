from fastapi import APIRouter

from app.api.routes import (
    chat,
    items,
    knowledge,
    login,
    private,
    tools,
    users,
    utils,
    widget,
    workspaces,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(workspaces.router)
api_router.include_router(knowledge.router)
api_router.include_router(tools.router)
api_router.include_router(chat.router)
api_router.include_router(widget.router)


if settings.FASTAPI_ENV == "development":
    api_router.include_router(private.router)
