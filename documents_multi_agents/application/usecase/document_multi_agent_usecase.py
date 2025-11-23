import asyncio

from documents.infrastructure.repository.document_repository_impl import DocumentRepositoryImpl
from documents_multi_agents.domain.document_agents import DocumentAgents
from documents_multi_agents.infrastructure.external.download_agent import download_document, get_cache_filename
from documents_multi_agents.infrastructure.external.parse_agent import parse_document
from documents_multi_agents.infrastructure.external.summarizers import bullet_summarizer, abstract_summarizer, \
    casual_summarizer, consensus_summarizer, answer_agent

class DocumentMultiAgentsUseCase:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.doc_repo = DocumentRepositoryImpl.get_instance()

        return cls.__instance

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    @staticmethod
    async def analyze_document(doc_id: str, doc_url: str, question: str) -> DocumentAgents:

        print("[DEBUG] Analyzing document:", doc_url)
        agents = DocumentAgents(doc_id=doc_id, doc_url=doc_url)

        # 다운로드
        content = await download_document(doc_url)
        cache_path = get_cache_filename(doc_url)

        # 파싱
        parsed_text = parse_document(content, cache_path)
        agents.update_parsed_text(parsed_text)

        # 병렬 요약
        bullet, abstract, casual = await asyncio.gather(
            bullet_summarizer(parsed_text),
            abstract_summarizer(parsed_text),
            casual_summarizer(parsed_text)
        )

        final_summary = await consensus_summarizer([bullet, abstract, casual])
        answer = await answer_agent(final_summary, question)

        agents.update_summaries(bullet=bullet, abstract=abstract, casual=casual, final=final_summary)
        agents.set_answer(answer)

        return agents
