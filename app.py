import streamlit as st
import ollama
import zlib
import struct
import olefile
import io
import re
from pypdf import PdfReader
from docx import Document

# --- 1. 파일 읽는 함수들 ---

def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    return text

def read_docx(file):
    doc = Document(file)
    text = []
    for paragraph in doc.paragraphs:
        text.append(paragraph.text)
    return "\n".join(text)

def read_hwp(file):
    file_bytes = file.read()
    f = olefile.OleFileIO(io.BytesIO(file_bytes))
    dirs = f.listdir()
    text = ""
    sections = [d for d in dirs if d[0] == "BodyText"]
    
    for section in sections:
        bodytext = f.openstream(section)
        data = bodytext.read()
        unpacked_data = zlib.decompress(data, -15)
        decoded_text = unpacked_data.decode('utf-16-le', errors='ignore')
        
        # 1차 청소: 한글, 영어, 숫자, 기본 특수문자만 남기기
        clean_text = re.sub(r"[^가-힣a-zA-Z0-9\s\.\,\!\?\(\)\-]", " ", decoded_text)
        
        # 2차 청소: 공백 정리
        clean_text = re.sub(r"\s+", " ", clean_text).strip()
        
        text += clean_text + "\n\n"

    return text

# --- 2. AI에게 시키는 함수 (안전장치 추가!) ---
def ask_ai(text, prompt_type):
    # 🔥 [핵심 수정] 텍스트가 너무 길면 AI가 멈춥니다.
    # 앞부분 3000자만 잘라서 보냅니다. (이 정도면 A4 2~3장 분량입니다)
    if len(text) > 3000:
        text = text[:3000] + "..." 
    
    target_model = 'llama3.2' 

    if prompt_type == "요약":
        # 외계어가 섞여 있어도 무시하라는 지시를 추가했습니다.
        system_msg = (
            "너는 공문서 처리 전문가야. "
            "텍스트 중간에 의미 없는 기호나 이상한 글자가 섞여 있다면 무시해. "
            "중요한 내용만 추려서 이해하기 쉽게 3줄로 요약해줘. "
            "반드시 한국어로 답변해."
        )
    elif prompt_type == "번역":
        system_msg = (
            "너는 전문 번역가야. "
            "이상한 기호는 무시하고, 문맥이 통하는 문장 위주로 자연스러운 한국어로 번역해줘."
        )
    
    response = ollama.chat(model=target_model, messages=[
        {'role': 'system', 'content': system_msg},
        {'role': 'user', 'content': text}
    ])
    return response['message']['content']

# --- 3. 화면 구성 ---
st.title("📄 통합 문서 AI 서비스")
st.caption("안전 모드: HWP 파일의 내용이 너무 길면 앞부분만 분석하여 속도를 높입니다.")

uploaded_file = st.file_uploader("문서를 업로드하세요", type=['pdf', 'docx', 'hwp'])

if uploaded_file is not None:
    file_ext = uploaded_file.name.split('.')[-1].lower()
    extracted_text = ""

    try:
        if file_ext == 'pdf':
            extracted_text = read_pdf(uploaded_file)
        elif file_ext == 'docx':
            extracted_text = read_docx(uploaded_file)
        elif file_ext == 'hwp':
            extracted_text = read_hwp(uploaded_file)
            
    except Exception as e:
        st.error(f"오류 발생: {e}")

    if extracted_text and len(extracted_text) > 10:
        # 화면에 보여줄 때는 너무 길면 잘라서 보여주기
        preview_text = extracted_text[:1000] + ("..." if len(extracted_text) > 1000 else "")
        
        st.subheader(f"원문 미리보기 (총 {len(extracted_text)}자)")
        st.text_area("내용 (앞부분)", preview_text, height=200)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📝 AI 요약하기"):
                with st.spinner("분석 중... (이제 1분 안에 끝납니다!)"):
                    try:
                        result = ask_ai(extracted_text, "요약")
                        st.success("요약 완료!")
                        st.write(result)
                    except Exception as e:
                        st.error(f"오류: {e}")

        with col2:
            if st.button("🌐 AI 번역하기"):
                with st.spinner("번역 중..."):
                    try:
                        result = ask_ai(extracted_text, "번역")
                        st.success("번역 완료!")
                        st.write(result)
                    except Exception as e:
                        st.error(f"오류: {e}")
