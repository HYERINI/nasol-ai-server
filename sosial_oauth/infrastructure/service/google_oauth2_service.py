import os
from urllib.parse import urlencode, quote

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError as RequestsConnectionError

from sosial_oauth.adapter.input.web.request.get_access_token_request import GetAccessTokenRequest
from sosial_oauth.adapter.input.web.response.access_token import AccessToken


class GoogleOAuth2Service:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def __init__(self):
        if not hasattr(self, "client_id"):
            self.client_id = self._get_env_var("GOOGLE_CLIENT_ID")

    @staticmethod
    def _get_env_var(key: str) -> str:
        # 환경변수를 읽고 None인 경우 예외를 발생
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Environment variable {key} is not set")
        return value

    @staticmethod
    def get_authorization_url() -> str:
        # Google OAuth 인증 URL을 생성
        scope = "openid email profile"
        
        google_auth_url = GoogleOAuth2Service._get_env_var("GOOGLE_AUTH_URL")
        client_id = GoogleOAuth2Service._get_env_var("GOOGLE_CLIENT_ID")
        redirect_uri = GoogleOAuth2Service._get_env_var("GOOGLE_REDIRECT_URI")
        
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope
        }
        
        query_string = urlencode(params, quote_via=quote)
        return f"{google_auth_url}?{query_string}"

    @staticmethod
    def refresh_access_token(request: GetAccessTokenRequest) -> AccessToken:
        # OAuth 인증 코드를 사용하여 액세스 토큰을 획득
        google_token_url = GoogleOAuth2Service._get_env_var("GOOGLE_TOKEN_URL")
        client_id = GoogleOAuth2Service._get_env_var("GOOGLE_CLIENT_ID")
        client_secret = GoogleOAuth2Service._get_env_var("GOOGLE_CLIENT_SECRET")
        redirect_uri = GoogleOAuth2Service._get_env_var("GOOGLE_REDIRECT_URI")
        
        data = {
            "code": request.code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        
        try:
            resp = requests.post(google_token_url, data=data, timeout=10)
            resp.raise_for_status()
        except Timeout:
            raise Exception("Request to Google OAuth token endpoint timed out")
        except RequestsConnectionError:
            raise Exception("Failed to connect to Google OAuth token endpoint")
        except requests.HTTPError:
            raise Exception(f"Google OAuth token request failed with status {resp.status_code}: {resp.text}")
        except RequestException as e:
            raise Exception(f"Unexpected error during Google OAuth token request: {str(e)}")
        
        try:
            token_data = resp.json()
        except ValueError as e:
            raise Exception(f"Invalid JSON response from Google OAuth token endpoint: {str(e)}")
        
        # 필수 필드 검증
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("Access token is missing in the response from Google OAuth")
        
        return AccessToken(
            access_token=access_token,
            token_type=token_data.get("token_type", "Bearer"),
            expires_in=token_data.get("expires_in"),
            refresh_token=token_data.get("refresh_token")
        )

    @staticmethod
    def fetch_user_profile(access_token: AccessToken) -> dict:
        # 액세스 토큰을 사용하여 사용자 프로필을 조회
        if not access_token or not access_token.access_token:
            raise ValueError("Access token is required to fetch user profile")

        google_userinfo_url = GoogleOAuth2Service._get_env_var("GOOGLE_USERINFO_URL")
        headers = {"Authorization": f"Bearer {access_token.access_token}"}

        try:
            resp = requests.get(google_userinfo_url, headers=headers, timeout=10)
            resp.raise_for_status()
        except Timeout:
            raise Exception("Request to Google userinfo endpoint timed out")
        except RequestsConnectionError:
            raise Exception("Failed to connect to Google userinfo endpoint")
        except requests.HTTPError:
            raise Exception(f"Google userinfo request failed with status {resp.status_code}: {resp.text}")
        except RequestException as e:
            raise Exception(f"Unexpected error during Google userinfo request: {str(e)}")

        try:
            user_profile = resp.json()
        except ValueError as e:
            raise Exception(f"Invalid JSON response from Google userinfo endpoint: {str(e)}")

        return user_profile
