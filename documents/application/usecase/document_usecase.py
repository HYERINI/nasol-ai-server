from documents.domain.document import Document
from documents.infrastructure.repository.document_repository_impl import DocumentRepositoryImpl


class DocumentUseCase:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.document_repo = DocumentRepositoryImpl.get_instance()
        return cls.__instance

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def register_document(self, session_id:str, file_key: str, file_value: str) -> Document:
        doc = Document(session_id, file_key, file_value)
        return self.document_repo.save(doc)