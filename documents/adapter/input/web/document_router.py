import os
from fastapi import APIRouter, Depends, HTTPException

from documents.adapter.input.web.request.register_document_request import RegisterDocumentRequest
from account.adapter.input.web.session_helper import get_current_user
from documents.application.usecase.document_usecase import DocumentUseCase

from documents_multi_agents.application.usecase.document_multi_agent_usecase import DocumentMultiAgentsUseCase

documents_router = APIRouter(tags=["documents"])
document_usecase = DocumentUseCase.get_instance()
document_multi_agenter_usecase = DocumentMultiAgentsUseCase.get_instance()

@documents_router.post("/register")
async def register_document(payload: RegisterDocumentRequest, session_id: str = Depends(get_current_user)):
    print("[DEBUG] Registering document for user session_id:", session_id)

    try:
        s3_url = os.getenv("AWS_S3_URL") + "/" + payload.s3_key
        agents = await document_multi_agenter_usecase.analyze_document(session_id, s3_url, "Summarize the content")
        parsed_text = agents.parsed_text
        summaries = {
            "bullet": agents.bullet_summary,
            "abstract": agents.abstract_summary,
            "casual": agents.casual_summary,
            "final": agents.final_summary
        }
        answer = agents.answer
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # doc = document_usecase.register_document(session_id, payload.file_name, payload.file_value)
    # return {
    #     "session_id": doc.session_id,
    #     "file_key": doc.file_key,
    #     "file_value": doc.file_value,
    #     "period": doc.period
    # }
