from fastapi import APIRouter, HTTPException

from account.adapter.input.web.response.account_response import AccountResponse
from account.application.usecase.account_usecase import AccountUseCase

account_router = APIRouter()
usecase = AccountUseCase().get_instance()

@account_router.get("/{oauth_type}/{oauth_id}", response_model=AccountResponse)
def get_account_by_oauth_id(oauth_type: str, oauth_id: str):
    account = usecase.get_account_by_oauth_id(oauth_type, oauth_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountResponse(
        session_id=account.session_id,
        oauth_id=account.oauth_id,
        oauth_type=account.oauth_type,
        nickname=account.nickname,
        name=account.name,
        profile_image=account.profile_image,
        email=account.email,
        phone_number=account.phone_number,
        active_status=account.active_status,
        updated_at=account.updated_at,
        created_at=account.created_at,
        role_id=account.role_id
    )

@account_router.delete("/{oauth_type}/{oauth_id}")
def delete_account_by_oauth_id(oauth_type: str, oauth_id: str):
    return usecase.delete_account_by_oauth_id(oauth_type, oauth_id)