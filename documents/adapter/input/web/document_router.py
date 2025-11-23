from fastapi import APIRouter, Depends

from documents.adapter.input.web.request.register_document_request import RegisterDocumentRequest
from account.adapter.input.web.session_helper import get_current_user
from documents.application.usecase.document_usecase import DocumentUseCase

documents_router = APIRouter(tags=["documents"])
document_usecase = DocumentUseCase.get_instance()

@documents_router.post("/register")
def register_document(payload: RegisterDocumentRequest, session_id: str = Depends(get_current_user)):
    print("[DEBUG] Registering document for user session_id:", session_id)

    ## TODO: agent 활용하여 aws에 있는 key로 문서를 가져와 분석 진행
    doc = document_usecase.register_document(session_id, payload.file_name, payload.file_value)
    return {
        "session_id": doc.session_id,
        "file_key": doc.file_key,
        "file_value": doc.file_value,
        "period": doc.period
    }
