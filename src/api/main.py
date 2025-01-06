import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
import logging

from src.create_query_embedding_openai import create_query_embedding
from src.generate_openai_response import generate_response
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

class ResponseModel(BaseModel):
    response: str

# lifespan 핸들러
@asynccontextmanager
async def lifespan(app: FastAPI):
    global chroma_client, collection, df_embeddings, client
    # OpenAI API 키 로드
    client = load_openai_api_key()
    logging.info("OpenAI API 키 로드 완료")

    # Chroma 클라이언트 초기화
    db_path: str = "../../data/chroma_db"
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
    embedding_csv_path = "../../data/embeddings_openai.csv"
    df_embeddings = load_embeddings_from_csv(embedding_csv_path)
    logging.info("Embedding 데이터 로드 완료")

    yield

app = FastAPI(
    title="SmartStore FAQ Chatbot API",
    description="A Retrieval-Augmented Generation (RAG) based chatbot for Naver Smart Store FAQs.",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/chat", response_model=ResponseModel)
def chat(query_request: QueryRequest):
    user_query = query_request.query
    if not user_query:
        raise HTTPException(status_code=400, detail="질문이 비어 있습니다.")

    try:
        # 질의 Embedding 생성
        query_embedding = create_query_embedding(client, user_query)
        logging.info("질의 Embedding 생성 완료")

        # 유사한 FAQ 검색
        results = search_faq(collection, query_embedding)
        logging.info("유사한 FAQ 검색 완료")

        # 답변 추출
        answers = get_answers_from_results(results, df_embeddings)
        logging.info("답변 추출 완료")

        # LLM을 사용하여 최종 응답 생성
        llm_response = generate_response(client, answers, user_query)
        logging.info("LLM 응답 생성 완료")

        return ResponseModel(response=llm_response)

    except Exception as e:
        logging.error(f"챗봇 응답 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="챗봇 응답 생성에 실패했습니다.")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)