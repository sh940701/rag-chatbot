import ast

import chromadb
import pandas as pd


def initialize_chroma(db_path: str = "../data/chroma_db") -> chromadb.Client:
    client = chromadb.PersistentClient(path=db_path)
    return client


def create_collection(client: chromadb.Client, collection_name: str = "faq_embeddings"):
    if collection_name not in client.list_collections():
        collection = client.create_collection(name=collection_name)
    else:
        collection = client.get_collection(name=collection_name)
    return collection


def load_embeddings_from_csv(file_path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(file_path)
        print(f"Embedding 데이터 로드 성공: {df.shape[0]} rows")
        return df
    except Exception as e:
        print(f"Embedding 데이터 로드 실패: {e}")
        raise


def insert_embeddings(collection, df: pd.DataFrame):
    try:
        if isinstance(df['embedding'][0], str):
            df['embedding'] = df['embedding'].apply(ast.literal_eval)
        embeddings = df['embedding'].tolist()
        ids = df.index.astype(str).to_list()
        metadatas = df[['question_clean', 'category', 'subcategory']].to_dict(orient='records')
        collection.add(
            documents=df['question_clean'].tolist(),
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        print("Embedding 데이터베이스에 삽입 완료")
    except Exception as e:
        print(f"Embedding 데이터베이스 삽입 실패: {e}")
        raise


if __name__ == "__main__":
    embedding_csv_path = "../data/embeddings_openai.csv"

    client = initialize_chroma()

    collection = create_collection(client)

    df_embeddings = load_embeddings_from_csv(embedding_csv_path)

    insert_embeddings(collection, df_embeddings)


    print("Chroma 데이터베이스 저장 완료")
