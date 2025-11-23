from config.redis_config import get_redis
from documents.application.port.document_repository_port import DocumentRepositoryPort
from documents.domain.document import Document

redis_client = get_redis()
class DocumentRepositoryImpl(DocumentRepositoryPort):
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

    def save(self, document: Document) -> Document:

        key = document.session_id
        # Hash 구조로 계속 누적 저장
        redis_client.hset(
            key,
            document.file_key,
            document.file_value
        )

        redis_client.expire(key, 24 * 60 * 60)

        return document