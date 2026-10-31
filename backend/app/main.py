from pathlib import Path

import sentry_sdk
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.widget_cors import WidgetCorsMiddleware

FRONTEND_DIR = Path(__file__).parent / "frontend"
WIDGET_JS = Path(__file__).parent / "widget" / "widget.js"
WIDGET_HOST = Path(__file__).parent / "static" / "widget-host.html"


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.FASTAPI_ENV != "development":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_HOST],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/widget.js", include_in_schema=False, tags=["widget"])
def widget_script() -> FileResponse:
    if not WIDGET_JS.is_file():
        raise HTTPException(status_code=404, detail="Widget script is not built")
    return FileResponse(WIDGET_JS, media_type="text/javascript")


@app.get("/examples/host", include_in_schema=False, tags=["widget"])
def widget_host() -> HTMLResponse:
    return HTMLResponse(WIDGET_HOST.read_text(encoding="utf-8"))


app.frontend("/", directory=FRONTEND_DIR)
app.add_middleware(WidgetCorsMiddleware, api_prefix=settings.API_V1_STR)
