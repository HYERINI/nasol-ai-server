from fastapi import APIRouter, Depends, UploadFile, HTTPException, Form, Response
from openai import OpenAI
from pypdf import PdfReader
import asyncio
import io
import re
from typing import List, Dict

from starlette import status

from config.redis_config import get_redis
from account.adapter.input.web.session_helper import get_current_user

documents_multi_agents_router = APIRouter(tags=["documents_multi_agents_router"])
redis_client = get_redis()
client = OpenAI()


# -----------------------
# PDF 텍스트 추출
# -----------------------
def extract_text_from_pdf_clean(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        texts = []
        for page in reader.pages:
            t = page.extract_text() or ""
            t = re.sub(r'\s+', ' ', t)  # 공백 정리
            t = re.sub(r'\d+\s*$', '', t)  # 페이지 번호 제거 (행 끝 숫자)
            if t.strip():
                texts.append(t.strip())
        return "\n".join(texts)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF parsing error: {str(e)}")


# -----------------------
# 텍스트 청킹
# -----------------------
def chunk_text(text: str, chunk_size=3500, overlap=300) -> List[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks, cur = [], ""
    for p in paragraphs:
        if len(cur) + len(p) <= chunk_size:
            cur += " " + p
        else:
            chunks.append(cur.strip())
            cur = p
    if cur:
        chunks.append(cur.strip())
    return chunks


# -----------------------
# GPT 호출 래퍼 (기존)
# -----------------------
async def ask_gpt(prompt: str, max_tokens=500):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda:
    client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0
    ).choices[0].message.content
                                      )


# -----------------------
# QA 에이전트 (요약 기반)
# -----------------------
async def qa_on_document(document: str, question: str) -> str:
    prompt = f"""
다음은 문서 자료이다. 이 문서 내의 정보만 사용하여 질문에 답해라.

요약:
{document}

질문:
{question}

규칙:
- 추론하지 말고 문서 내에서만 답을 찾아라.
- 없으면 "문서에 해당 정보 없음"이라고 답해라.
"""
    return (await ask_gpt(prompt, max_tokens=300)).strip()


# -----------------------
# QA 에이전트 (요약 기반)
# -----------------------
async def assets_on_document(document: str, question: str) -> str:
    prompt = f"""
다음은 문서 본문이다. 이 문서 내의 정보만 사용하여 질문에 답해라.

본문:
{document}

질문:
{question}

규칙:
- 주어진 문서 본문의 자료를 토대로 한국의 비슷한 소득수준의 재무정보를 분석하여 가이드가 될 수 있는 포토폴리오 자료를 제출하라. 
- 웹 검색을 사용하여 현재 소득 수준에 대한 포토폴리오 자료, 소득 수준이 10% 상승되었을 때, 20% 상승되었을 때에 대한 미래 예측 자료를 함께 제출하라.
"""
    return (await ask_gpt(prompt, max_tokens=2500)).strip()

# -----------------------
# API 엔드포인트
# -----------------------
@documents_multi_agents_router.post("/analyze")
async def analyze_document(file: UploadFile, type_of_doc: str = Form(...), session_id: str = Depends(get_current_user)):
    try:
        content = await file.read()
        if not content:
            raise HTTPException(400, "Empty file upload")

        text = extract_text_from_pdf_clean(content)
        if not text:
            raise HTTPException(400, "No text extracted")

        # 2. QA (요약 기반)
        answer = await qa_on_document(text,
                                      "PDF의 항목과 금액을 급여 : 얼마 비과세소득계 : 얼마 비과세식대 : 얼마 형태로 모든 항목들을 key:value 형태로 요약해줘 예시로 든 항목만 하는게 아니라 모든 금액 항목들을 모두 다.")

        pattern = re.compile(r'([가-힣\w\s]+)\s*:\s*([\d,]+)')

        print(session_id)
        try:

            for match in pattern.finditer(answer):
                field, value = match.groups()
                # 쉼표 제거하고 Redis에 저장
                redis_client.hset(
                    session_id,
                    f"{type_of_doc}:{field.strip()}",
                    value.replace(",", "").strip()
                )
        except Exception as e:
            print("[ERROR] Failed to save to Redis:", str(e))
        redis_client.expire(session_id, 24 * 60 * 60)

    except Exception as e:
        raise HTTPException(500, f"{type(e).__name__}: {str(e)}")

    return Response(status_code=status.HTTP_200_OK)


# -----------------------
# API 엔드포인트
# -----------------------
@documents_multi_agents_router.get("/future-assets")
async def analyze_document(session_id: str = Depends(get_current_user)):
    try:

        content = redis_client.hgetall(session_id)
        income_data = {
            k.split("income:", 1)[1]: v
            for k, v in content.items()
            if k.startswith("income:")
        }
        print("DEBUG] Income_data:", income_data)

        income_str = ", ".join(
            f"{k.split('income:', 1)[1]}: {v}"
            for k, v in content.items()
            if k.startswith("income:")
        )

        print("[DEBUG] Income Data:", income_str)
        answer = await assets_on_document(income_str,
                                      "현재 내 원천징수영수증 자료야. 이 자료를 토대로 앞으로의 내 미래 자산에 대한 재무 컨설팅을 듣고 싶어. "
                                      "어떤 방식으로 자산을 분배하면 좋을지, 세액을 줄이는 방법은 있을지. 현재의 소득수준이 10%증가했을 때, 20% 증가했을 때를 대비한 미래 예측 시뮬레이션도 있으면 좋겠어. "
                                      "참고 자료는 한국의 비슷한 소득 수준을 가진 사람들에 대한 재무 데이터를 통해서 진행해줘")


        print("[DEBUG] Answer: " , answer)

        return answer
    except Exception as e:
        raise HTTPException(500, f"{type(e).__name__}: {str(e)}")
