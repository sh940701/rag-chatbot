import asyncio
import json

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from openai import Stream
from pydantic import BaseModel
from contextlib import asynccontextmanager
import logging

from src.create_query_embedding_openai import create_query_embedding
from src.generate_openai_response import generate_response_sse
from src.openai_embedding import load_openai_api_key
from src.search_faq import search_faq, get_answers_from_results
from src.vector_db import initialize_chroma, load_embeddings_from_csv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

chroma_client = None
collection = None
df_embeddings = None
client = None


# Pydantic 모델 정의
class QueryRequest(BaseModel):
    query: str


# class ResponseModel(BaseModel):
#     response: str


# lifespan 핸들러
@asynccontextmanager
async def lifespan(app: FastAPI):
    global chroma_client, collection, df_embeddings, client
    # OpenAI API 키 로드
    client = load_openai_api_key()
    logging.info("OpenAI API 키 로드 완료")

    # Chroma 클라이언트 초기화
    db_path: str = "data/chroma_db"
    chroma_client = initialize_chroma(db_path)
    logging.info("ChromaDB 클라이언트 초기화 완료")

    # 컬렉션 로드
    collection_name = "faq_embeddings"
    try:
        collection = chroma_client.get_collection(name=collection_name)
        logging.info(f"컬렉션 '{collection_name}' 로드 완료")
    except Exception as e:
        logging.error(f"컬렉션 '{collection_name}'을(를) 찾을 수 없습니다: {e}")
        raise e

    # Embedding 데이터 로드
    embedding_csv_path = "data/embeddings_openai.csv"
    df_embeddings = load_embeddings_from_csv(embedding_csv_path)
    logging.info("Embedding 데이터 로드 완료")

    yield


app = FastAPI(
    title="SmartStore FAQ Chatbot API",
    description="A Retrieval-Augmented Generation (RAG) based chatbot for Naver Smart Store FAQs.",
    version="1.0.0",
    lifespan=lifespan
)

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

templates = Jinja2Templates(directory="./templates")
app.mount("/static", StaticFiles(directory="./static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def get_chat(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/chat")
async def chat(query: str):
    user_query = query
    if not user_query:
        raise HTTPException(status_code=400, detail="질문이 비어 있습니다.")

    try:
        # 1) 사용자 입력을 임베딩
        query_embedding = create_query_embedding(client, user_query)

        # 2) FAQ 검색 → top_k=5개
        results = search_faq(collection, query_embedding, top_k=5)
        logging.info("유사한 FAQ 검색 완료")

        distances = results.get('distances', [1.0])
        # print(distances)
        min_distance = min(distances[0])
        threshold = 1.0

        if min_distance > threshold:
            # 유사도 점수가 낮아 연관성이 없는 경우
            logging.info(f"FAQ 유사도 점수 낮음 (min_distance={min_distance}), LLM 호출 생략")

            def generate_error():
                yield f"data: {json.dumps({'status': 'processing', 'data': '질문과 관련된 FAQ가 없습니다. 다시 시도해 주세요.'}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'status': 'complete', 'data': 'Stream finished'}, ensure_ascii=False)}\n\n"

            return StreamingResponse(generate_error(), media_type="text/event-stream")

        # 3) 상위 3개는 답변용, 나머지 2개는 추천 질문용
        top_3_results = {
            'documents': [results['documents'][0][:3]],
            'metadatas': [results['metadatas'][0][:3]]
        }
        # 나머지 2개
        recommended_results = {
            'documents': [results['documents'][0][3:]],
            'metadatas': [results['metadatas'][0][3:]]
        }

        # 4) 실제 답변 text 추출
        answers_for_llm = get_answers_from_results(top_3_results, df_embeddings)
        logging.info("FAQ 답변 추출 완료")

        # 5) 추천 질문 text 추출
        recommended_questions = [doc for doc in recommended_results['documents'][0]]

        faq_context = ""
        for i, ans in enumerate(answers_for_llm):
            faq_context += f"FAQ {i + 1} Answer:\n{ans}\n\n"

        # 추천 질문 컨텍스트 구성
        recommended_context = ""
        for i, q in enumerate(recommended_questions):
            recommended_context += f"- {q}\n"

        return StreamingResponse(generate_response_sse(client, user_query, faq_context, recommended_context),
                                 media_type="text/event-stream")


    except Exception as e:
        logging.error(f"챗봇 응답 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="챗봇 응답 생성에 실패했습니다.")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
