from typing import Optional

from account.domain.account import Account
from account.infrastructure.repository.account_repository_impl import AccountRepositoryImpl


class AccountUseCase:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.account_repo = AccountRepositoryImpl.get_instance()
        return cls.__instance

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    async def create_account(self, session_id:str, oauth_id:str, oauth_type: str, nickname: str, name:str, profile_image:str, email:str, phone_number:str, active_status:str, role_id:str):
        account = Account(session_id=session_id, oauth_id=oauth_id, oauth_type=oauth_type, nickname=nickname, name=name, profile_image=profile_image, email=email, phone_number=phone_number, active_status=active_status, role_id=role_id)
        return await self.account_repo.save(account)

    def get_account_by_oauth_id(self, oauth_type:str, oauth_id: str) -> Optional[Account]:
        return self.account_repo.get_by_oauth_id(oauth_type, oauth_id)

    def delete_account_by_oauth_id(self, oauth_type: str, oauth_id: str) -> bool:
        return self.account_repo.delete_account_by_oauth_id(oauth_type, oauth_id)