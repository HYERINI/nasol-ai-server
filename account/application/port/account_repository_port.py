from abc import ABC, abstractmethod
from typing import Optional

from account.domain.account import Account


class AccountRepositoryPort(ABC):

    @abstractmethod
    def get_by_oauth_id(self, oauth_type: str, user_oauth_id: str) -> Optional[Account]:
        pass