# src/data_loader.py

import pandas as pd
import re

def load_data(file_path: str) -> pd.DataFrame:
    """
    .pkl 파일을 로드하여 DataFrame으로 반환합니다.
    딕셔너리 형식의 데이터를 질문과 답변으로 변환합니다.
    """
    try:
        data = pd.read_pickle(file_path)
        print("데이터 로드 성공")

        # 딕셔너리를 DataFrame으로 변환
        df = pd.DataFrame(list(data.items()), columns=['question', 'answer'])
        print(f"DataFrame 변환 완료: {df.shape[0]} rows, {df.shape[1]} columns")
        return df

    except Exception as e:
        print(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

def extract_categories(df: pd.DataFrame) -> pd.DataFrame:
    categories = []
    subcategories = []

    # 정규표현식 컴파일
    # 카테고리: 문장 시작의 모든 대괄호 [] 안 내용
    category_pattern = re.compile(r'^\[([^\]]+)\]')
    # 서브카테고리: 문장 끝의 소괄호 () 안 내용
    subcategory_pattern = re.compile(r'\(([^)]+)\)$')

    for q in df['question']:
        # 카테고리 추출: 문장 시작의 모든 대괄호 안 내용
        category_matches = category_pattern.findall(q)
        # findall로 첫 번째 대괄호만 추출하므로 반복문을 사용하여 모든 대괄호 추출
        category_matches = re.findall(r'\[([^\]]+)\]', q)
        if category_matches:
            categories.append(category_matches)
        else:
            categories.append(['Uncategorized'])

        # 서브카테고리 추출: 문장 끝의 소괄호 안 내용
        subcategory_match = subcategory_pattern.search(q)
        if subcategory_match:
            subcategories.append(subcategory_match.group(1))
        else:
            subcategories.append('')

    df['category'] = categories
    df['subcategory'] = subcategories

    return df

def clean_question(text: str) -> str:
    """
    질문 텍스트 정제 함수:
    - 문장 시작의 대괄호 [] 안의 내용 제거
    - 문장 끝의 소괄호 () 안의 내용 제거
    - 중간에 있는 괄호들은 그대로 유지
    - 특수 문자 제거 (필요에 따라 조정)
    - 불필요한 공백 제거
    """
    # 문장 시작의 대괄호 [] 안 내용 제거
    text = re.sub(r'^\[([^\]]+)\]', '', text)
    # 문장 끝의 소괄호 () 안 내용 제거
    text = re.sub(r'\(([^)]+)\)$', '', text)
    # 특수 문자 제거
    text = re.sub(r'[^\w\s]', ' ', text)
    # 불필요한 공백 제거 (연속된 공백을 단일 공백으로 변경)
    text = re.sub(r'\s+', ' ', text)
    # 양쪽 끝의 공백 제거
    text = text.strip()
    return text

def clean_answer(text: str) -> str:
    # 특수 문자 제거
    text = re.sub(r'[^\w\s]', ' ', text)
    # 불필요한 공백 제거 (연속된 공백을 단일 공백으로 변경)
    text = re.sub(r'\s+', ' ', text)
    # 양쪽 끝의 공백 제거
    text = text.strip()
    return text

def basic_preprocessing(df: pd.DataFrame) -> pd.DataFrame:
    """
    기본 전처리 수행 (예: 결측치 확인 및 제거)
    """
    print("기본 전처리 시작")
    initial_shape = df.shape

    # 결측치 확인
    missing = df.isnull().sum()
    print("결측치 현황:\n", missing)

    # 결측치가 있는 행 제거
    df = df.dropna()
    final_shape = df.shape
    print(f"결측치 제거 전: {initial_shape}, 제거 후: {final_shape}")

    return df

def additional_preprocessing(df: pd.DataFrame) -> pd.DataFrame:
    print("카테고리 및 서브카테고리 추출 시작")
    df = extract_categories(df)
    print("카테고리 및 서브카테고리 추출 완료")

    print("텍스트 정제 시작")
    df['question_clean'] = df['question'].apply(clean_question)
    df['answer_clean'] = df['answer'].apply(clean_answer)
    print("텍스트 정제 완료")

    return df

def validate_dataframe(df: pd.DataFrame):
    """
    DataFrame의 유효성을 검사합니다.
    """
    required_columns = ['question', 'answer', 'category', 'subcategory', 'question_clean', 'answer_clean']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"DataFrame에 '{col}' 열이 없습니다.")
    print("DataFrame 유효성 검사 통과")

if __name__ == "__main__":
    data_path = "../data/final_result.pkl"
    df = load_data(data_path)
    if not df.empty:
        df = basic_preprocessing(df)
        df = additional_preprocessing(df)
        validate_dataframe(df)  # 유효성 검사 추가
        # 전처리된 데이터를 저장
        df.to_pickle("../data/preprocessed_data.pkl")
        print("전처리 완료 및 저장")
    else:
        print("DataFrame이 비어 있어 전처리를 수행하지 않습니다.")