from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    doc_url: str
    question: str
