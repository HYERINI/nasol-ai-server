import uuid
import httpx

from fastapi import APIRouter, Request, Cookie, Header
from fastapi.responses import RedirectResponse, JSONResponse

from config.redis_config import get_redis
from sosial_oauth.application.usecase.google_oauth2_usecase import GoogleOAuth2UseCase
from util.log.log import Log
from util.cache.ai_cache import AICache
from util.security.crsf import generate_csrf_token, verify_csrf_token, CSRF_COOKIE_NAME

# Singleton 방식으로 변경
authentication_router = APIRouter()
usecase = GoogleOAuth2UseCase().get_instance()
redis_client = get_redis()
logger = Log.get_logger()

@authentication_router.get("/google")
async def redirect_to_google():
    url = usecase.get_authorization_url()
    logger.info(f"Redirecting to Google: {url}")
    return RedirectResponse(url)

@authentication_router.post("/logout")
async def logout_to_google(request: Request, session_id: str | None = Cookie(None), x_csrf_token: str | None = Header(None)):

    logger.info("Logout called")
    logger.info("Request headers: %s", request.headers)

    # CSRF 검증
    verify_csrf_token(request, x_csrf_token)

    if not session_id:
        logger.debug("No session_id received. Returning logged_out: False")
        response = JSONResponse({"logged_in": False})
        response.delete_cookie(key="session_id")
        return response

    exists = redis_client.exists(session_id)
    logger.debug("Redis has session_id? %s", exists)

    if exists:
        # 🔥 사용자 세션 데이터 삭제 전에 캐시도 함께 삭제
        logger.info(f"Invalidating cache for session: {session_id}")
        invalidated_count = AICache.invalidate_user_cache(session_id)
        logger.info(f"Invalidated {invalidated_count} cache entries")

        # 세션 데이터 삭제
        redis_client.delete(session_id)
        logger.debug("Redis session deleted: %s", redis_client.exists(session_id))

    # 쿠키 삭제와 함께 응답 반환
    response = JSONResponse({"logged_out": bool(exists)})
    response.delete_cookie(key="session_id")
    logger.debug("Cookie deleted from response")
    return response

@authentication_router.get("/google/redirect")
async def process_google_redirect(
        code: str | None = None,
        state: str | None = None,
        error: str | None = None
):
    # Google OAuth 에러 처리 (access_denied 등)
    if error:
        logger.error(f"Google OAuth error: {error}")
        return RedirectResponse("http://localhost:3000")
    logger.debug("google/redirect called")

    # session_id 생성
    session_id = str(uuid.uuid4())
    logger.debug("Generated session_id")

    # code -> access token
    access_token, session_id = await usecase.login_and_fetch_user(state or "", code, session_id)

    logger.debug("Access token fetched")
    r = httpx.get("https://oauth2.googleapis.com/tokeninfo", params={"access_token": access_token.access_token})
    logger.debug(f"Tokeninfo fetched from Google text: {r.text}, status: {r.status_code}")

    # Redis에 session 저장 (1시간 TTL)
    redis_client.hset(
        session_id,
        "USER_TOKEN",
        access_token.access_token,
    )
    redis_client.expire(session_id, 24 * 60 * 60)
    logger.debug("Session saved in Redis: %s", redis_client.exists(session_id))

    # CSRF 토큰 생성
    csrf_token = generate_csrf_token()
    print("[DEBUG] csrf_token:", csrf_token)

    # 브라우저 쿠키 발급
    response = RedirectResponse("http://localhost:3000")
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=86400  # 🔥 24시간으로 변경 (Redis TTL과 동일)
    )

    # CSRF 토큰 쿠키 발급
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,  # JS에서 읽어서 헤더에 넣을 수 있도록 False
        secure=True,
        samesite="strict",
        max_age=3600
    )

    logger.debug("Cookie set in RedirectResponse directly")
    return response


@authentication_router.get("/status")
async def auth_status(request: Request, session_id: str | None = Cookie(None)):
    logger.info("/status called")

    # 모든 요청 헤더 출력
    logger.info("Request headers: %s", request.headers)

    # 쿠키 확인
    logger.debug("Received session_id cookie")

    if not session_id:
        logger.debug("No session_id received. Returning logged_in: False")
        return {"logged_in": False}

    exists = redis_client.exists(session_id)
    logger.debug("Redis session exists: %s", exists)

    return {"logged_in": bool(exists)}
