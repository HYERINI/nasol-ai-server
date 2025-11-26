from fastapi import APIRouter

from datetime import datetime

from kftc.infrastructure.service.kftc_service import KftcService

kftc_router = APIRouter()
get_access_token = KftcService().get_instance()
get_card_transactions = KftcService().get_instance()

@kftc_router.get("/redirect")
def auth_callback(code: str):
    token_data = get_access_token(code)
    # DB에 token 저장 가능
    return token_data

@kftc_router.get("/cards")
def read_cards(from_date: str, to_date: str):
    # 예시: access_token DB에서 가져오기
    access_token = "USER_ACCESS_TOKEN"
    result = get_card_transactions(access_token, from_date, to_date)

    transactions = []
    for item in result.get("card_list", []):
        approved_at=datetime.strptime(item["approved_at"], "%Y%m%d%H%M%S"),
        amount=int(item["amount"]),
        merchant=item["merchant_name"],
        card_name=item["card_name"]
        transactions.append((approved_at, amount, merchant, card_name))
        print(f"approved_at={approved_at}, amount={amount}, merchant={merchant}, card_name={card_name}")
    return transactions
