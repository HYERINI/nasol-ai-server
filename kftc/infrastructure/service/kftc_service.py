import os
import requests

class KftcService:
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


    @staticmethod
    def _get_env_var(key: str) -> str:
        # 환경변수를 읽고 None인 경우 예외를 발생
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Environment variable {key} is not set")
        return value

    @staticmethod
    def get_card_transactions(access_token: str, from_date: str, to_date: str):
        url = "https://openapi.openbanking.or.kr/v2.0/card/approval_list"
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "user_seq_no": "USER_SEQ_NO_FROM_AUTH",
            "from_date": from_date,
            "to_date": to_date
        }
        resp = requests.post(url, json=payload, headers=headers)
        return resp.json()

    def get_access_token(auth_code: str):
        url = "https://openapi.openbanking.or.kr/oauth/2.0/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": KftcService._get_env_var("CLIENT_ID"),
            "client_secret": KftcService._get_env_var("CLIENT_SECRET"),
            "code": auth_code,
            "redirect_uri": KftcService._get_env_var("REDIRECT_URI")
        }
        resp = requests.post(url, data=data)
        return resp.json()  # access_token, refresh_token 등 포함