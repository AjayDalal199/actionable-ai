from fastapi import APIRouter, Depends, HTTPException
from pydantic.networks import EmailStr
from redis.exceptions import RedisError

from app.api.deps import get_current_active_superuser
from app.core.redis import ping_redis
from app.models import Message
from app.utils import generate_test_email, send_email

router = APIRouter(prefix="/utils", tags=["utils"])


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/health-check/")
async def health_check() -> bool:
    try:
        await ping_redis()
    except RedisError, OSError, TimeoutError:
        raise HTTPException(status_code=503, detail="Redis unavailable") from None
    return True
