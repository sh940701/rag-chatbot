import logging
import pandas as pd

from src.openai_embedding import load_openai_api_key
from src.vector_db import initialize_chroma, create_collection, load_embeddings_from_csv
from src.create_query_embedding_openai import create_query_embedding

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def search_faq(collection, query_embedding: list, top_k: int = 5):
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=['metadatas', 'documents']
        )
        return results
    except Exception as e:
        logging.error(f"FAQ 검색 실패: {e}")
        raise

def get_answers_from_results(results, df: pd.DataFrame):
    answers = []
    for i in range(len(results['documents'][0])):
        question = results['documents'][0][i]
        answer = df.loc[df['question_clean'] == question, 'answer_clean'].values
        if len(answer) > 0:
            answers.append(answer[0])
        else:
            answers.append("해당 질문에 대한 답변을 찾을 수 없습니다.")
    return answers

def main():
    client = load_openai_api_key()

    chroma_client = initialize_chroma()

    try:
        collection = create_collection(chroma_client)
        logging.info(f"컬렉션 '{collection}' 로드 완료")
    except Exception as e:
        logging.error(f"컬렉션을 찾을 수 없습니다: {e}")
        return

    embedding_csv_path = "../data/embeddings_openai.csv"
    df_embeddings = load_embeddings_from_csv(embedding_csv_path)

    user_query = input("질문을 입력하세요: ")

    query_embedding = create_query_embedding(client, user_query)

    results = search_faq(collection, query_embedding, top_k=5)

    answers = get_answers_from_results(results, df_embeddings)

    print("\n검색된 FAQ 답변:")
    for idx, answer in enumerate(answers, 1):
        print(f"{idx}. {answer}")

if __name__ == "__main__":
    main()
