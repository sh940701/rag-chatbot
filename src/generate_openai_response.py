import logging

import openai
from openai import OpenAI

from src.openai_embedding import load_openai_api_key

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def generate_response(client: OpenAI, faq_answers: list, user_query: str, model: str = "gpt-3.5-turbo") -> str:
    try:
        context = "\n".join([f"FAQ {i + 1}: {ans}" for i, ans in enumerate(faq_answers, 1)])

        prompt = (
            "You are a friendly and helpful Korean chatbot named 'SmartStore Bot'. "
            "When answering the user's question, please speak in a warm and polite tone, "
            "providing sufficient detail and clarity. Refer to the given FAQ context if it is relevant. "
            "If the user asks for a step-by-step procedure, list each step clearly and use friendly language. "
            "If the FAQ doesn't have an answer, politely apologize and suggest alternative actions. "
            "Please provide the answer in Korean. Keep the response concise but not too short—"
            "around 200~300 characters or a few paragraphs is okay. "
            "use line breaks and bullet points to improve readability.\n\n"
            "예시 포맷:\n"
            "1) 첫 번째 단계\n"
            "2) 두 번째 단계\n"
            "3) 세 번째 단계\n\n"
            "End the answer with a short polite closing statement such as '도움이 되셨길 바랍니다. 더 궁금한 점 있으시면 언제든 알려주세요!'.\n\n"
            f"사용자 질문: {user_query}\n\n"
            f"FAQ 내용:\n{context}\n\n"
            "답변:"
        )

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "developer",
                    "content": (
                        "You are a friendly and helpful Korean chatbot named 'SmartStore Bot'. "
                        "You speak in a polite and warm tone, providing thorough explanations. "
                        "If you cannot find relevant info in the FAQ, politely apologize and suggest other possible solutions."
                    )
                },
                {
                    "role": "user",
                    "content": prompt  # 위에서 구성한 prompt 문자열
                }
            ],
            temperature=0.5,
            max_tokens=512,
            top_p=0,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None
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
