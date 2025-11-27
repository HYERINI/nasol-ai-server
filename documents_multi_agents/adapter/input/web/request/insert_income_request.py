from pydantic import BaseModel
from typing import Dict, Literal

class InsertDocumentRequest(BaseModel):
    document_type: Literal["income", "expense"]
    data: Dict[str, str]