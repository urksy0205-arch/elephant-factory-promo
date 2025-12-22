# -*- coding: utf-8 -*-
"""
코끼리공장 다국어 홍보물 자동 생성 시스템 v3.0
"""

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from deep_translator import GoogleTranslator
import time
from datetime import datetime
from pathlib import Path
import docx
import PyPDF2
import io
import zipfile
import re

# ============================================
# 페이지 설정
# ============================================

st.set_page_config(
    page_title="코끼리공장 홍보물 생성기",
    page_icon="🐘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# 설정
# ============================================

LANGUAGES = {
    'ko': '한국어 🇰🇷',
    'en': 'English 🇺🇸',
    'ja': '日本語 🇯🇵',
    'zh-CN': '中文(简体) 🇨🇳',
    'vi': 'Tiếng Việt 🇻🇳',
    'ru': 'Русский 🇷🇺',
    'uz': "O'zbek 🇺🇿",
    'si': 'සිංහල 🇱🇰'
}

BRAND_COLOR = '#2B9FD9'
BACKGROUND_COLOR = '#E8F4F8'  # 연한 하늘색 배경
TEXT_COLOR = '#2C3E50'
ACCENT_COLOR = '#FF6B6B'

# ============================================
# CSS 스타일 (연한 하늘색 배경)
# ============================================

st.markdown(f"""
<style>
    /* 전체 배경 */
    .stApp {{
        background-color: {BACKGROUND_COLOR};
    }}
    
    /* 메인 컨텐츠 영역 */
    .main .block-container {{
        background-color: {BACKGROUND_COLOR};
        padding-top: 2rem;
    }}
    
    /* 사이드바 */
    section[data-testid="stSidebar"] {{
        background-color: white;
    }}
    
    /* 헤더 */
    .main-header {{
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, {BRAND_COLOR} 0%, #1E88C7 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    
    /* 버튼 */
    .stButton>button {{
        width: 100%;
        background-color: {BRAND_COLOR};
        color: white;
        font-size: 18px;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        border: none;
        transition: all 0.3s;
    }}
    .stButton>button:hover {{
        background-color: #1E88C7;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}
    
    /* 박스 스타일 */
    .summary-box {{
        padding: 1.5rem;
        background-color: white;
        border-left: 4px solid {BRAND_COLOR};
        border-radius: 5px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    .promo-box {{
        padding: 1.5rem;
        background-color: white;
        border-left: 4px solid #28a745;
        border-radius: 5px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    .original-box {{
        padding: 1.5rem;
        background-color: white;
        border-left: 4px solid #6c757d;
        border-radius: 5px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: white;
        border-radius: 5px;
        padding: 0.5rem;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: {TEXT_COLOR};
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {BRAND_COLOR};
        color: white;
    }}
    
    /* 입력 필드 */
    .stTextArea textarea, .stTextInput input {{
        background-color: white;
    }}
    
    /* 파일 업로더 */
    .stFileUploader {{
        background-color: white;
        padding: 1rem;
        border-radius: 5px;
    }}
</style>
""", unsafe_allow_html=True)

# ============================================
# AI 요약 함수
# ============================================

def extract_key_info(text):
    """공문에서 핵심 정보 추출"""
    info = {
        'title': '',
        'date': '',
        'time': '',
        'location': '',
        'target': '',
        'contact': '',
        'how_to_apply': '',
        'content': ''
    }
    
    lines = text.strip().split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    # 제목 찾기
    for i, line in enumerate(lines[:5]):
        if len(line) > 5 and (
            '안내' in line or '공고' in line or '모집' in line or 
            '프로그램' in line or '교육' in line or i == 0
        ):
            info['title'] = line
            break
    
    # 날짜 찾기
    date_patterns = [
        r'(\d{4})[년.-]\s*(\d{1,2})[월.-]\s*(\d{1,2})일?',
        r'(\d{1,2})[월/]\s*(\d{1,2})일?',
        r'(\d{4})[./]\s*(\d{1,2})[./]\s*(\d{1,2})'
    ]
    
    for line in lines:
        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                info['date'] = match.group(0)
                break
        if info['date']:
            break
    
    # 시간 찾기
    time_patterns = [
        r'(\d{1,2}):(\d{2})',
        r'(\d{1,2})시\s*(\d{1,2})?분?'
    ]
    
    for line in lines:
        for pattern in time_patterns:
            match = re.search(pattern, line)
            if match:
                info['time'] = match.group(0)
                break
        if info['time']:
            break
    
    # 장소 찾기
    location_keywords = ['장소', '위치', '주소', '에서', '교육실', '강당']
    for line in lines:
        for keyword in location_keywords:
            if keyword in line:
                info['location'] = line
                break
        if info['location']:
            break
    
    # 대상 찾기
    target_keywords = ['대상', '참가자', '신청자', '이주민', '외국인']
    for line in lines:
        for keyword in target_keywords:
            if keyword in line:
                info['target'] = line
                break
        if info['target']:
            break
    
    # 연락처 찾기
    contact_patterns = [
        r'0\d{1,2}-\d{3,4}-\d{4}',
        r'\d{3}-\d{4}-\d{4}',
        r'010-\d{4}-\d{4}'
    ]
    
    for line in lines:
        if '연락' in line or '문의' in line or '전화' in line:
            info['contact'] = line
            for pattern in contact_patterns:
                match = re.search(pattern, line)
                if match:
                    info['contact'] = line
                    break
            break
    
    # 신청 방법 찾기
    apply_keywords = ['신청', '접수', '등록', '참여방법']
    for line in lines:
        for keyword in apply_keywords:
            if keyword in line:
                info['how_to_apply'] = line
                break
        if info['how_to_apply']:
            break
    
    # 전체 내용
    info['content'] = '\n'.join(lines)
    
    return info

def create_summary(info):
    """추출된 정보를 요약문으로 변환"""
    summary_parts = []
    
    if info['title']:
        summary_parts.append(f"📢 {info['title']}")
    
    if info['date']:
        summary_parts.append(f"📅 일시: {info['date']}")
    
    if info['time']:
        if not info['date']:
            summary_parts.append(f"🕐 시간: {info['time']}")
        else:
            summary_parts[-1] += f" {info['time']}"
    
    if info['location']:
        summary_parts.append(f"📍 {info['location']}")
    
    if info['target']:
        summary_parts.append(f"👥 {info['target']}")
    
    if info['how_to_apply']:
        summary_parts.append(f"✍️ {info['how_to_apply']}")
    
    if info['contact']:
        summary_parts.append(f"📞 {info['contact']}")
    
    return '\n'.join(summary_parts)

def create_promo_text(info):
    """홍보문 스타일로 변환"""
    promo_parts = []
    
    # 제목
    if info['title']:
        title = info['title'].replace('안내', '').replace('공고', '').strip()
        promo_parts.append(f"🎉 {title} 🎉")
    else:
        promo_parts.append("🎉 코끼리공장에서 알려드립니다! 🎉")
    
    promo_parts.append("")
    
    # 핵심 내용
    content_line = "코끼리공장에서 이주민 여러분을 위한 프로그램을 준비했습니다! 💙"
    
    if '교육' in info['content']:
        content_line = "이주민을 위한 무료 교육 프로그램에 참여하세요! 📚"
    elif '모집' in info['content']:
        content_line = "여러분의 참여를 기다립니다! 함께해요! 🙌"
    elif '행사' in info['content']:
        content_line = "즐거운 행사에 여러분을 초대합니다! 🎊"
    
    promo_parts.append(content_line)
    promo_parts.append("")
    
    # 핵심 정보
    if info['date'] or info['time']:
        date_str = info['date'] if info['date'] else ''
        time_str = info['time'] if info['time'] else ''
        promo_parts.append(f"📅 {date_str} {time_str}".strip())
    
    if info['location']:
        location = info['location'].replace('장소:', '').replace('장소', '').strip()
        promo_parts.append(f"📍 {location}")
    
    promo_parts.append("")
    
    # 참여 유도
    if info['how_to_apply']:
        apply = info['how_to_apply'].replace('신청:', '').replace('신청', '').strip()
        promo_parts.append(f"✅ {apply}")
    else:
        promo_parts.append("✅ 지금 바로 신청하세요!")
    
    if info['contact']:
        promo_parts.append(f"📞 {info['contact']}")
    
    promo_parts.append("")
    promo_parts.append("💙 많은 참여 바랍니다! 💙")
    
    return '\n'.join(promo_parts)

# ============================================
# 파일 읽기 함수
# ============================================

def read_docx(file):
    """워드 파일 읽기"""
    doc = docx.Document(file)
    text = []
    for paragraph in doc.paragraphs:
        text.append(paragraph.text)
    return '\n'.join(text)

def read_pdf(file):
    """PDF 파일 읽기"""
    text = []
    pdf = PyPDF2.PdfReader(file)
    for page in pdf.pages:
        text.append(page.extract_text())
    return '\n'.join(text)

def read_txt(file):
    """텍스트 파일 읽기"""
    return file.read().decode('utf-8')

def translate_text(text, target_lang):
    """텍스트 번역"""
    try:
        if target_lang == 'ko':
            return text
        
        translator = GoogleTranslator(source='ko', target=target_lang)
        return translator.translate(text)
    except Exception as e:
        st.warning(f"번역 실패 ({target_lang}): {str(e)}")
        return text

# ============================================
# 이미지 생성 함수 (공공기관 스타일 심플)
# ============================================

def create_promo_image(title, content, lang_code, size_type='social'):
    """홍보 이미지 생성 (단일)"""
    
    # 크기 설정
    if size_type == 'social':
        width, height = 1080, 1080
    elif size_type == 'cardnews':
        width, height = 1080, 1920
    else:  # a4
        width, height = 2480, 3508
    
    # 배경 생성 (흰색)
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # 상단 파란색 바
    header_height = int(height * 0.12)
    draw.rectangle([(0, 0), (width, header_height)], fill=BRAND_COLOR)
    
    # 로고 추가
    try:
        if Path('logos/logo.png').exists():
            logo = Image.open('logos/logo.png')
            logo_width = int(width * 0.25)
            logo_height = int(logo_width * logo.size[1] / logo.size[0])
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            
            img.paste(logo, (30, int(header_height/2 - logo_height/2)), logo)
    except:
        pass
    
    # 폰트 설정
    try:
        title_font = ImageFont.truetype("malgun.ttf", int(height * 0.045))
        content_font = ImageFont.truetype("malgun.ttf", int(height * 0.022))
    except:
        try:
            title_font = ImageFont.truetype("arial.ttf", int(height * 0.045))
            content_font = ImageFont.truetype("arial.ttf", int(height * 0.022))
        except:
            title_font = ImageFont.load_default()
            content_font = ImageFont.load_default()
    
    # 제목 그리기
    title_y = int(height * 0.22)
    title_clean = re.sub(r'[^\w\s가-힣]', '', title)
    draw.text((50, title_y), title_clean[:50], fill=TEXT_COLOR, font=title_font)
    
    # 내용 그리기
    content_y = int(height * 0.35)
    lines = content.split('\n')[:10]
    
    for i, line in enumerate(lines):
        y = content_y + (i * int(height * 0.035))
        line_clean = re.sub(r'[^\w\s가-힣:/-]', '', line)
        draw.text((50, y), line_clean[:60], fill=TEXT_COLOR, font=content_font)
    
    return img

def create_cardnews(info, lang_code='ko'):
    """카드뉴스 생성 (공공기관 스타일 - 심플)"""
    cards = []
    width, height = 1080, 1920
    
    # 폰트 설정
    try:
        title_font = ImageFont.truetype("malgun.ttf", 70)
        subtitle_font = ImageFont.truetype("malgun.ttf", 50)
        content_font = ImageFont.truetype("malgun.ttf", 45)
        small_font = ImageFont.truetype("malgun.ttf", 35)
    except:
        try:
            title_font = ImageFont.truetype("arial.ttf", 70)
            subtitle_font = ImageFont.truetype("arial.ttf", 50)
            content_font = ImageFont.truetype("arial.ttf", 45)
            small_font = ImageFont.truetype("arial.ttf", 35)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            content_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
    
    # 카드 1: 표지 (심플)
    card1 = Image.new('RGB', (width, height), 'white')
    draw1 = ImageDraw.Draw(card1)
    
    # 상단 바
    draw1.rectangle([(0, 0), (width, 200)], fill=BRAND_COLOR)
    
    # 로고
    try:
        if Path('logos/logo.png').exists():
            logo = Image.open('logos/logo.png')
            logo_width = 250
            logo_height = int(logo_width * logo.size[1] / logo.size[0])
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            card1.paste(logo, (50, int(100 - logo_height/2)), logo)
    except:
        pass
    
    # 제목 (중앙, 크게)
    title_text = info['title'] if info['title'] else "코끼리공장 안내"
    
    # 제목을 여러 줄로 나누기
    title_lines = []
    if len(title_text) > 15:
        words = title_text.split()
        current_line = ""
        for word in words:
            if len(current_line + word) > 15:
                title_lines.append(current_line.strip())
                current_line = word + " "
            else:
                current_line += word + " "
        if current_line:
            title_lines.append(current_line.strip())
    else:
        title_lines = [title_text]
    
    # 제목 그리기
    y_start = height // 2 - (len(title_lines) * 80)
    for i, line in enumerate(title_lines):
        draw1.text((width//2, y_start + (i * 100)), line, fill=TEXT_COLOR, font=title_font, anchor="mm")
    
    # 하단 바
    draw1.rectangle([(0, height-80), (width, height)], fill=BRAND_COLOR)
    
    cards.append(card1)
    
    # 카드 2: 일정/장소 (심플)
    card2 = Image.new('RGB', (width, height), 'white')
    draw2 = ImageDraw.Draw(card2)
    
    # 상단 타이틀
    draw2.rectangle([(0, 0), (width, 150)], fill=BRAND_COLOR)
    draw2.text((width//2, 75), "일정 및 장소", fill='white', font=subtitle_font, anchor="mm")
    
    # 내용
    y_pos = 400
    line_spacing = 150
    
    if info['date']:
        draw2.text((100, y_pos), f"📅  {info['date']}", fill=TEXT_COLOR, font=content_font)
        y_pos += line_spacing
    
    if info['time']:
        draw2.text((100, y_pos), f"🕐  {info['time']}", fill=TEXT_COLOR, font=content_font)
        y_pos += line_spacing
    
    if info['location']:
        loc_text = info['location'].replace('장소:', '').replace('장소', '').strip()
        draw2.text((100, y_pos), f"📍  {loc_text}", fill=TEXT_COLOR, font=content_font)
    
    # 하단
    draw2.rectangle([(0, height-80), (width, height)], fill='#E0E0E0')
    draw2.text((width//2, height-40), "1 / 3", fill=TEXT_COLOR, font=small_font, anchor="mm")
    
    cards.append(card2)
    
    # 카드 3: 신청방법 (심플)
    card3 = Image.new('RGB', (width, height), 'white')
    draw3 = ImageDraw.Draw(card3)
    
    draw3.rectangle([(0, 0), (width, 150)], fill=BRAND_COLOR)
    draw3.text((width//2, 75), "신청 방법", fill='white', font=subtitle_font, anchor="mm")
    
    y_pos = 400
    
    if info['target']:
        target_text = info['target'].replace('대상:', '').replace('대상', '').strip()
        draw3.text((100, y_pos), f"👥  {target_text}", fill=TEXT_COLOR, font=content_font)
        y_pos += 180
    
    if info['how_to_apply']:
        apply_text = info['how_to_apply'].replace('신청:', '').replace('신청', '').strip()
        draw3.text((100, y_pos), f"✍️  {apply_text}", fill=TEXT_COLOR, font=content_font)
    
    draw3.rectangle([(0, height-80), (width, height)], fill='#E0E0E0')
    draw3.text((width//2, height-40), "2 / 3", fill=TEXT_COLOR, font=small_font, anchor="mm")
    
    cards.append(card3)
    
    # 카드 4: 연락처 (심플)
    card4 = Image.new('RGB', (width, height), 'white')
    draw4 = ImageDraw.Draw(card4)
    
    draw4.rectangle([(0, 0), (width, 150)], fill=BRAND_COLOR)
    draw4.text((width//2, 75), "문의", fill='white', font=subtitle_font, anchor="mm")
    
    y_pos = 500
    
    if info['contact']:
        draw4.text((100, y_pos), f"📞  {info['contact']}", fill=TEXT_COLOR, font=content_font)
        y_pos += 200
    
    draw4.text((width//2, y_pos + 100), "많은 참여 바랍니다", fill=BRAND_COLOR, font=subtitle_font, anchor="mm")
    
    # 로고 (하단)
    try:
        if Path('logos/logo.png').exists():
            logo = Image.open('logos/logo.png')
            logo_width = 300
            logo_height = int(logo_width * logo.size[1] / logo.size[0])
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            card4.paste(logo, (width//2 - logo_width//2, height - 450), logo)
    except:
        pass
    
    draw4.rectangle([(0, height-80), (width, height)], fill='#E0E0E0')
    draw4.text((width//2, height-40), "3 / 3", fill=TEXT_COLOR, font=small_font, anchor="mm")
    
    cards.append(card4)
    
    return cards

# ============================================
# 메인 UI
# ============================================

# 헤더
st.markdown("""
<div class="main-header">
    <h1>🐘 코끼리공장 다국어 홍보물 자동 생성기</h1>
    <p>공문을 자동으로 요약하고 홍보문으로 변환한 후 8개 언어로 번역합니다</p>
    <p style="font-size: 14px; margin-top: 10px;">✨ 완전 무료 | AI 자동 요약 | 카드뉴스 생성 | 다국어 번역</p>
</div>
""", unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    
    logo_file = st.file_uploader(
        "로고 업로드 (선택사항)",
        type=['png', 'jpg', 'jpeg'],
        help="홍보물에 들어갈 로고를 업로드하세요"
    )
    
    if logo_file:
        Path('logos').mkdir(exist_ok=True)
        with open('logos/logo.png', 'wb') as f:
            f.write(logo_file.read())
        st.success("✅ 로고 업로드 완료!")
    
    st.markdown("---")
    
    st.markdown("""
    ### ✨ 주요 기능
    - 🎴 **카드뉴스 생성**
    - 🤖 AI 자동 요약
    - 📝 홍보문 자동 생성
    - 🌏 8개 언어 번역
    - 🖼️ 이미지 자동 생성
    
    ### 📋 지원 파일
    - Word (.docx)
    - PDF (.pdf)
    - Text (.txt)
    """)

# 메인 영역
tab1, tab2, tab3 = st.tabs(["📝 공문 입력 & 생성", "💡 예시 보기", "ℹ️ 사용 방법"])

with tab1:
    st.header("1️⃣ 공문 입력")
    
    input_method = st.radio(
        "입력 방식을 선택하세요:",
        ["📁 파일 업로드", "✏️ 직접 입력"],
        horizontal=True
    )
    
    text_content = None
    
    if input_method == "📁 파일 업로드":
        uploaded_file = st.file_uploader(
            "공문 파일을 선택하세요",
            type=['docx', 'pdf', 'txt'],
            help="워드, PDF, 텍스트 파일을 지원합니다"
        )
        
        if uploaded_file:
            with st.spinner("파일을 읽는 중..."):
                try:
                    if uploaded_file.name.endswith('.docx'):
                        text_content = read_docx(uploaded_file)
                    elif uploaded_file.name.endswith('.pdf'):
                        text_content = read_pdf(uploaded_file)
                    elif uploaded_file.name.endswith('.txt'):
                        text_content = read_txt(uploaded_file)
                    
                    st.success(f"✅ 파일 읽기 완료! ({len(text_content)}자)")
                
                except Exception as e:
                    st.error(f"❌ 파일 읽기 실패: {str(e)}")
    
    else:
        text_content = st.text_area(
            "공문 내용을 입력하세요",
            height=300,
            placeholder="""예시:

이주민 한국어 교육 프로그램 안내

일시: 2025년 1월 15일 오후 2시
장소: 코끼리공장 교육실
대상: 이주민 누구나
신청: 전화 또는 방문 접수

코끼리공장에서 이주민을 위한 무료 한국어 교육을 진행합니다.

문의: 052-123-4567
""",
            help="Ctrl+V로 붙여넣기 가능합니다"
        )
    
    if text_content and len(text_content) > 10:
        with st.expander("📄 원문 보기"):
            st.markdown(f'<div class="original-box">{text_content}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.header("2️⃣ AI 자동 요약 및 홍보문 생성")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info("💡 공문을 분석하여 핵심 정보를 추출하고 홍보문으로 변환합니다")
        
        with col2:
            analyze_button = st.button("🤖 분석 시작", type="primary", use_container_width=True)
        
        if analyze_button:
            with st.spinner("🤖 AI가 공문을 분석하고 있습니다..."):
                info = extract_key_info(text_content)
                summary = create_summary(info)
                promo = create_promo_text(info)
                
                st.session_state['original'] = text_content
                st.session_state['summary'] = summary
                st.session_state['promo'] = promo
                st.session_state['info'] = info
            
            st.success("✅ 분석 완료!")
    
    if 'promo' in st.session_state:
        st.markdown("---")
        st.header("📊 분석 결과")
        
        st.subheader("📌 핵심 요약")
        st.markdown(f'<div class="summary-box">{st.session_state["summary"]}</div>', unsafe_allow_html=True)
        
        st.subheader("✨ 생성된 홍보문")
        
        edited_promo = st.text_area(
            "홍보문 (수정 가능)",
            value=st.session_state['promo'],
            height=300,
            help="생성된 홍보문을 수정할 수 있습니다"
        )
        
        st.session_state['promo'] = edited_promo
        
        st.markdown(f'<div class="promo-box">{edited_promo}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.header("3️⃣ 번역 언어 선택")
        
        col1, col2 = st.columns(2)
        
        selected_langs = []
        lang_list = list(LANGUAGES.items())
        
        with col1:
            for i in range(0, len(lang_list), 2):
                lang_code, lang_name = lang_list[i]
                if st.checkbox(lang_name, value=True, key=f"lang_{lang_code}"):
                    selected_langs.append(lang_code)
        
        with col2:
            for i in range(1, len(lang_list), 2):
                if i < len(lang_list):
                    lang_code, lang_name = lang_list[i]
                    if st.checkbox(lang_name, value=True, key=f"lang_{lang_code}"):
                        selected_langs.append(lang_code)
        
        st.header("4️⃣ 이미지 형식 선택")
        
        size_options = st.multiselect(
            "생성할 이미지 형식을 선택하세요",
            ["🎴 카드뉴스 (1080x1920)", "소셜미디어용 (1080x1080)", "A4 인쇄용 (2480x3508)"],
            default=["🎴 카드뉴스 (1080x1920)", "소셜미디어용 (1080x1080)"]
        )
        
        st.header("5️⃣ 최종 생성")
        
        if st.button("🚀 번역 및 이미지 생성 시작!", type="primary", use_container_width=True):
            
            if not selected_langs:
                st.error("❌ 번역할 언어를 최소 1개 이상 선택해주세요")
            elif not size_options:
                st.error("❌ 이미지 형식을 최소 1개 이상 선택해주세요")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                translations = {}
                images = {}
                cardnews_images = {}
                
                has_cardnews = any("카드뉴스" in opt for opt in size_options)
                other_sizes = [opt for opt in size_options if "카드뉴스" not in opt]
                
                total_steps = len(selected_langs) * (1 + len(other_sizes) + (1 if has_cardnews else 0))
                current_step = 0
                
                # 번역
                status_text.text("🌏 번역 중...")
                
                for lang_code in selected_langs:
                    lang_name = LANGUAGES[lang_code]
                    status_text.text(f"🌏 번역 중... {lang_name}")
                    
                    translated = translate_text(edited_promo, lang_code)
                    translations[lang_code] = translated
                    
                    current_step += 1
                    progress_bar.progress(current_step / total_steps)
                    time.sleep(0.5)
                
                # 이미지 생성
                status_text.text("🎨 이미지 생성 중...")
                
                for lang_code, translated_text in translations.items():
                    lang_name = LANGUAGES[lang_code]
                    
                    lines = translated_text.split('\n')
                    title = lines[0][:100] if lines else "공지사항"
                    content = '\n'.join(lines[1:]) if len(lines) > 1 else translated_text
                    
                    images[lang_code] = {}
                    
                    # 카드뉴스 생성
                    if has_cardnews:
                        status_text.text(f"🎴 카드뉴스 생성 중... {lang_name}")
                        try:
                            cards = create_cardnews(st.session_state['info'], lang_code)
                            cardnews_images[lang_code] = cards
                        except Exception as e:
                            st.warning(f"⚠️ {lang_name} 카드뉴스 생성 실패: {str(e)}")
                        
                        current_step += 1
                        progress_bar.progress(current_step / total_steps)
                    
                    # 다른 사이즈 생성
                    for size_option in other_sizes:
                        if "소셜" in size_option:
                            size_type = 'social'
                            size_name = '소셜미디어'
                        else:
                            size_type = 'a4'
                            size_name = 'A4'
                        
                        status_text.text(f"🎨 이미지 생성 중... {lang_name} ({size_name})")
                        
                        try:
                            img = create_promo_image(title, content, lang_code, size_type)
                            
                            img_byte_arr = io.BytesIO()
                            img.save(img_byte_arr, format='PNG')
                            img_byte_arr.seek(0)
                            
                            images[lang_code][size_type] = img_byte_arr.getvalue()
                            
                        except Exception as e:
                            st.warning(f"⚠️ {lang_name} {size_name} 생성 실패: {str(e)}")
                        
                        current_step += 1
                        progress_bar.progress(current_step / total_steps)
                
                progress_bar.progress(1.0)
                status_text.text("✅ 완료!")
                
                st.success("🎉 홍보물 생성 완료!")
                
                st.markdown("---")
                st.header("📥 결과물 다운로드")
                
                lang_tabs = st.tabs([LANGUAGES[lang] for lang in selected_langs])
                
                for idx, lang_code in enumerate(selected_langs):
                    with lang_tabs[idx]:
                        st.subheader(f"📝 번역문")
                        st.text_area(
                            f"{LANGUAGES[lang_code]} 번역 결과",
                            translations[lang_code],
                            height=200,
                            key=f"trans_{lang_code}"
                        )
                        
                        # 카드뉴스 표시
                        if lang_code in cardnews_images:
                            st.subheader("🎴 카드뉴스")
                            
                            card_cols = st.columns(min(len(cardnews_images[lang_code]), 4))
                            for card_idx, card in enumerate(cardnews_images[lang_code]):
                                with card_cols[card_idx % 4]:
                                    card_bytes = io.BytesIO()
                                    card.save(card_bytes, format='PNG')
                                    card_bytes.seek(0)
                                    
                                    st.image(card_bytes.getvalue(), caption=f"카드 {card_idx+1}", use_container_width=True)
                                    
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    filename = f"카드뉴스_{lang_code}_{card_idx+1}_{timestamp}.png"
                                    
                                    st.download_button(
                                        label=f"💾 카드 {card_idx+1}",
                                        data=card_bytes.getvalue(),
                                        file_name=filename,
                                        mime="image/png",
                                        key=f"dl_card_{lang_code}_{card_idx}"
                                    )
                        
                        # 일반 이미지 표시
                        if images.get(lang_code):
                            st.subheader("🖼️ 이미지")
                            
                            cols = st.columns(len(images[lang_code]))
                            
                            for col_idx, (size_type, img_bytes) in enumerate(images[lang_code].items()):
                                size_name = '소셜미디어' if size_type == 'social' else 'A4'
                                
                                with cols[col_idx]:
                                    st.image(img_bytes, caption=f"{size_name}용", use_container_width=True)
                                    
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    filename = f"홍보물_{lang_code}_{size_type}_{timestamp}.png"
                                    
                                    st.download_button(
                                        label=f"💾 {size_name}용",
                                        data=img_bytes,
                                        file_name=filename,
                                        mime="image/png",
                                        key=f"dl_{lang_code}_{size_type}"
                                    )
                
                # 일괄 다운로드
                st.markdown("---")
                st.subheader("📦 전체 다운로드")
                
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    
                    zip_file.writestr("원문.txt", st.session_state['original'].encode('utf-8'))
                    zip_file.writestr("요약.txt", st.session_state['summary'].encode('utf-8'))
                    zip_file.writestr("홍보문_한국어.txt", edited_promo.encode('utf-8'))
                    
                    for lang_code, text in translations.items():
                        if lang_code != 'ko':
                            filename = f"번역문/홍보문_{lang_code}.txt"
                            zip_file.writestr(filename, text.encode('utf-8'))
                    
                    # 카드뉴스 저장
                    for lang_code, cards in cardnews_images.items():
                        for card_idx, card in enumerate(cards):
                            card_bytes = io.BytesIO()
                            card.save(card_bytes, format='PNG')
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"카드뉴스/카드뉴스_{lang_code}_{card_idx+1}_{timestamp}.png"
                            zip_file.writestr(filename, card_bytes.getvalue())
                    
                    # 일반 이미지 저장
                    for lang_code, size_dict in images.items():
                        for size_type, img_bytes in size_dict.items():
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"이미지/홍보물_{lang_code}_{size_type}_{timestamp}.png"
                            zip_file.writestr(filename, img_bytes)
                
                zip_buffer.seek(0)
                
                st.download_button(
                    label="📦 전체 파일 다운로드 (ZIP)",
                    data=zip_buffer,
                    file_name=f"코끼리공장_홍보물_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip"
                )

with tab2:
    st.header("💡 카드뉴스 예시")
    
    st.info("📱 공공기관 스타일의 심플한 카드뉴스 (4장 구성)")
    
    st.markdown("""
    ### 🎴 카드 구성
    
    **1장: 표지**
    - 깔끔한 흰 배경
    - 제목 중앙 배치
    - 상단에 로고
    
    **2장: 일정/장소**
    - 날짜, 시간, 장소 정보
    - 아이콘과 함께 표시
    
    **3장: 신청방법**
    - 대상, 신청 방법
    - 간결하게 정리
    
    **4장: 연락처**
    - 문의처 정보
    - 마무리 멘트
    """)

with tab3:
    st.header("📖 사용 방법")
    
    st.markdown("""
    ### 🎨 디자인 특징
    
    - **웹페이지**: 연한 하늘색 배경 (#E8F4F8)
    - **카드뉴스**: 공공기관 스타일 심플 디자인
    - **컬러**: 코끼리공장 브랜드 컬러 통일
    
    ### 📱 카드뉴스
    
    - 세로형 (1080x1920) 인스타그램/페이스북 최적화
    - 4장 구성: 표지 → 일정 → 신청 → 연락처
    - 각 카드 개별 다운로드 가능
    
    ### ⚠️ 주의사항
    
    - 카드뉴스는 한국어 정보 기준으로 생성
    - 공문은 핵심 정보 위주로 간결하게 작성
    - 완전 무료, 인터넷 연결 필요
    """)

# 푸터
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    🐘 코끼리공장 다국어 홍보물 자동 생성기 v3.0<br>
    ✨ 카드뉴스 기능 | AI 자동 요약 | 완전 무료<br>
    Made with ❤️ for Elephant Factory
</div>
""", unsafe_allow_html=True)
