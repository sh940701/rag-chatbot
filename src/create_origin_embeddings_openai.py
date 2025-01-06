import pandas as pd
from openai import OpenAI

from openai_embedding import get_embeddings, load_openai_api_key

def load_preprocessed_data(file_path: str) -> pd.DataFrame:
    try:
        df = pd.read_pickle(file_path)
        print(f"데이터 로드 성공: {df.shape[0]} rows")
        return df
    except Exception as e:
        print(f"데이터 로드 실패: {e}")
        raise

def create_embeddings(client: OpenAI, df: pd.DataFrame, output_path: str):
    try:
        print("Embedding 생성 시작...")
        embeddings = get_embeddings(client, df['question_clean'].to_list())

        df['embedding'] = embeddings
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"Embedding 생성 및 저장 완료: {output_path}")
    except Exception as e:
        print(f"Embedding 생성 실패: {e}")
        raise

if __name__ == "__main__":
    client = load_openai_api_key()

    preprocessed_data_path = "../data/preprocessed_data.pkl"
    embedding_output_path = "../data/embeddings_openai.csv"

    df = load_preprocessed_data(preprocessed_data_path)

    create_embeddings(client, df, embedding_output_path)