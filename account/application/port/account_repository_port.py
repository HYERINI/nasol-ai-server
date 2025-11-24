from abc import ABC, abstractmethod
from typing import Optional

from account.domain.account import Account


class AccountRepositoryPort(ABC):

    @abstractmethod
    def get_account_by_oauth_id(self, session_id:str, oauth_type: str, user_oauth_id: str) -> Optional[Account]:
        pass

    @abstractmethod
    def get_account_by_session_id(self, session_id: str) -> Optional[Account]:
        pass

    @abstractmethod
    def delete_account_by_oauth_id(self, oauth_type: str, oauth_id: str) -> bool:
        pass