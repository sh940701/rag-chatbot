import openai
import os
from dotenv import load_dotenv

load_dotenv()

def load_openai_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
    openai.api_key = api_key

def get_embeddings(texts: list, model: str = "text-embedding-3-small") -> list:
    try:
        response = openai.embeddings.create(input=texts, model=model)
        embeddings = [item.embedding for item in response.data]
        return embeddings
    except Exception as e:
        print(f"Embedding 생성 실패: {e}")
        raise

def test_openapi_embedding():
    test_sentences = [
        "안녕하세요, 스마트스토어에 오신 것을 환영합니다.",
        "스마트스토어 회원가입 절차를 안내해 드리겠습니다."
    ]
    embeddings = get_embeddings(test_sentences)
    print("테스트 Embedding 생성 완료:")
    print(embeddings)

if __name__ == "__main__":
    load_openai_api_key()
    test_openapi_embedding()