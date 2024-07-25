import httpx

from common.config import settings
from common.schema import APIResponse


def get_auth_headers():
    return {"X-API-Key": settings.WEB_API_KEY}


def get_endpoint(endpoint: str):
    return f"{settings.WEB_API_URL}/{endpoint}"


async def register_user(phone_number: str, telegram_user_id: str):
    if not phone_number.startswith("+"):
        phone_number = f"+{phone_number}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                get_endpoint("auth/register-telegram"),
                headers=get_auth_headers(),
                json={
                    "phone_number": phone_number,
                    "telegram_user_id": telegram_user_id,
                },
            )
            response.raise_for_status()
            res = APIResponse(**response.json())
            return res
    except httpx.HTTPStatusError as e:
        return APIResponse(
            error=f"HTTP error: {e.response.status_code} - {e.response.text}"
        )
    except httpx.RequestError as e:
        return APIResponse(error=f"Request error: {str(e)}")
    except ValueError as e:
        return APIResponse(error=f"Invalid response format: {str(e)}")
    except Exception as e:
        return APIResponse(error=f"Unexpected error: {str(e)}")
