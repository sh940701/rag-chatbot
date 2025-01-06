import logging

from src.create_query_embedding_openai import create_query_embedding
from src.generate_openai_response import generate_response
from src.openai_embedding import load_openai_api_key
from src.search_faq import search_faq, get_answers_from_results
from src.vector_db import initialize_chroma, create_collection, load_embeddings_from_csv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    client = load_openai_api_key()

    chroma_client = initialize_chroma()

    collection_name = "faq_embeddings"
    try:
        collection = create_collection(chroma_client, collection_name)
        logging.info(f"컬렉션 '{collection_name}' 로드 완료")
    except Exception as e:
        logging.error(f"컬렉션 '{collection_name}'을(를) 찾을 수 없습니다: {e}")
        return

    embedding_csv_path = "../data/embeddings_openai.csv"
    df_embeddings = load_embeddings_from_csv(embedding_csv_path)
    while True:
        user_query = input("\n질문을 입력하세요 (종료하려면 'exit' 입력): ")
        if user_query.lower() == 'exit':
            print("챗봇을 종료합니다.")
            break

        # 질의 Embedding 생성
        query_embedding = create_query_embedding(client, user_query)

        # 유사한 FAQ 검색
        results = search_faq(collection, query_embedding, top_k=3)

        # 답변 추출
        answers = get_answers_from_results(results, df_embeddings)

        # LLM을 사용하여 최종 응답 생성
        llm_response = generate_response(client, answers, user_query)

        # 응답 출력
        print("\n챗봇 응답:")
        print(llm_response)

if __name__ == '__main__':
    main()