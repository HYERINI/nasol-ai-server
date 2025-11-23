from abc import ABC, abstractmethod

from documents.domain.document import Document


class DocumentRepositoryPort(ABC):
    @abstractmethod
    def save(self, document: Document) -> Document:
        pass