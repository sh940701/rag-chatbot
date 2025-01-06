import logging

import openai
from openai import OpenAI

from src.openai_embedding import load_openai_api_key

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def generate_response(client: OpenAI, faq_answers: list, user_query: str, model: str = "gpt-3.5-turbo") -> str:
    try:
        context = "\n".join([f"FAQ {i + 1}: {ans}" for i, ans in enumerate(faq_answers, 1)])

        prompt = (
            f"아래의 FAQ 답변들을 참고하여, 다음 사용자 질문에 대해 명확하고 친절한 답변을 작성해 주세요.\n\n"
            f"사용자 질문: {user_query}\n\n"
            f"참고할 FAQ 답변들:\n{context}\n\n"
            f"답변:"
        )

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "developer", "content": "당신은 친절하고 도움이 되는 챗봇입니다."},
                {"role": "user", "content": prompt}
            ],

            stop=None,
        )

        generated_answer = response.choices[0].message.content
        logging.info("LLM 응답 생성 완료")
        return generated_answer

    except Exception as e:
        logging.error(f"LLM 응답 생성 실패: {e}")
        raise


if __name__ == "__main__":
    client = load_openai_api_key()
    sample_faq_answers = [
        "스마트스토어 회원가입을 위해서는 네이버 커머스 ID가 필요합니다. 네이버 계정으로 로그인 후, 스마트스토어 센터에서 회원가입 절차를 진행해주세요.",
        "회원가입 절차는 다음과 같습니다: 1. 네이버 계정 로그인 2. 스마트스토어 센터 접속 3. 기본 정보 입력 4. 판매자 등록 완료"
    ]
    user_query = "스마트스토어에 어떻게 회원가입하나요?"
    response = generate_response(client, sample_faq_answers, user_query)
    print(f"LLM 응답: {response}")
