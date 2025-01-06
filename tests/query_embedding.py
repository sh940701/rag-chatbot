import logging

from src.openai_embedding import load_openai_api_key, get_embeddings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_query_embedding(query: str) -> list:
    return get_embeddings([query])[0]


if __name__ == '__main__':
    load_openai_api_key()
    sample_query = "스마트스토어 회원가입 절차를 알고 싶어요."
    embedding = create_query_embedding(sample_query)
    print(f"쿼리 Embedding: {embedding}")
