import logging

import openai
from openai import OpenAI

from src.openai_embedding import load_openai_api_key

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def generate_response(
        client: OpenAI,
        faq_answers: list,  # 예: 상위 3개 FAQ의 answer_clean
        related_questions: list,  # 예: 나머지 FAQ의 question_clean
        user_query: str,
        model: str = "gpt-4o-mini"
) -> str:
    """
    한 번의 LLM 호출로,
    - 최종 답변
    - 추천 질문
    을 함께 생성.
    """

    # 1) FAQ 답변 컨텍스트 구성 (상위 3개)
    faq_context = ""
    for i, ans in enumerate(faq_answers):
        faq_context += f"FAQ {i + 1} Answer:\n{ans}\n\n"

    # 2) 추천 질문 컨텍스트 구성 (나머지 2개)
    #    필요하다면 답변도 함께 넘겨줄 수 있지만, 여기서는 질문만 넘긴다고 가정
    recommended_context = ""
    for i, q in enumerate(related_questions):
        recommended_context += f"- {q}\n"

    # 3) 최종 프롬프트 생성
    prompt = (
        "You are a friendly and helpful Korean chatbot named 'SmartStore Bot'. "
        "When answering the user's question, please speak in a warm and polite tone, "
        "providing sufficient detail and clarity. Refer to the given FAQ context if it is relevant. "
        "If the user asks for a step-by-step procedure, list each step clearly and use friendly language. "
        "If the FAQ doesn't have an answer, politely apologize and suggest alternative actions. "
        "Please provide the answer in Korean. Keep the response concise but not too short—"
        "around 200~300 characters or a few paragraphs is okay. "
        "Use line breaks to improve readability, but avoid using Markdown like Bold.\n\n"
        "예시 포맷:\n"
        "1) 첫 번째 작업을 설명합니다.\n"
        "2) 두 번째 작업을 설명합니다.\n"
        "3) 세 번째 작업을 설명합니다.\n\n"
        "End the answer with a short polite closing statement such as '도움이 되셨길 바랍니다. 더 궁금한 점 있으시면 언제든 알려주세요!'.\n\n"

        f"사용자 질문: {user_query}\n\n"
        f"FAQ 답변 정보:\n{faq_context}\n"
        f"연관 질문 후보:\n{recommended_context}\n"

        "아래 형식을 참고하여 답변을 작성하세요:\n"
        "-----\n"
        "답변:\n"
        "(FAQ들을 참조해서 사용자 질문에 대한 답변을 작성)\n\n"
        "추천 질문:\n"
        "(연관 질문 후보 중 2~3개를 자연스럽게 나열)\n"
        "-----\n"
        "답변:"
    )

    # 4) LLM 호출
    try:
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
                    "content": prompt
                }
            ],
            temperature=0.4,
            top_p=0.9,
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
    # response = generate_response(client, sample_faq_answers, user_query)
    # print(f"LLM 응답: {response}")
