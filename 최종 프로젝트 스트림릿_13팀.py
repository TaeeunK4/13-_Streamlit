import streamlit as st
import base64
from io import BytesIO
from PIL import Image
from pathlib import Path
import requests

# =========================================================
# 1. 파일 지정
# =========================================================
cursor_file_id = '1c3p8hltAy8cGXFJpxKX5PM29E30H7MPX'  
target_width = 32


# =========================================================
# 2. 이미지 처리 함수 (PNG 리사이징 및 Base64 변환)
# =========================================================
@st.cache_data
def get_drive_resized_png_b64(file_id, new_width):
    """
    구글 드라이브 ID를 받아 이미지를 다운로드하고,
    비율을 유지하며 리사이징한 뒤 Base64 문자열로 반환
    """
    try:
        url = f'https://drive.google.com/uc?id={file_id}'
        
        response = requests.get(url)
        response.raise_for_status()
        
        img = Image.open(BytesIO(response.content))
        
        # 혹시 모를 호환성 문제 방지를 위해 RGBA(투명 배경 지원) 모드로 변환
        img = img.convert("RGBA")

        # 이미지 비율 유지하며 리사이징 크기 계산
        w_percent = (new_width / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        
        # 고품질 리사이징 (LANCZOS 필터 사용)
        resized_img = img.resize((new_width, h_size), Image.Resampling.LANCZOS)
        
        # 메모리 버퍼에 PNG 형식으로 저장
        buffer = BytesIO()
        resized_img.save(buffer, format="PNG")
        
        # Base64로 인코딩해서 문자열로 반환
        return base64.b64encode(buffer.getvalue()).decode()
    except Exception as e:
        # 에러 발생 시 호출한 곳에서 처리하도록 다시 던지거나 None 반환
        raise Exception(f"이미지 처리 실패: {e}")

try:
    cursor_b64 = get_drive_resized_png_b64(cursor_file_id, target_width)

    if cursor_b64:
        hotspot_x = 0
        hotspot_y = 0
        
        cursor_css_value = f'url("data:image/png;base64,{cursor_b64}") {hotspot_x} {hotspot_y}, auto !important'

        st.markdown(f"""
        <style>
        /* 전체 페이지 적용 */
        * {{
            cursor: {cursor_css_value};
        }}
        
        /* 사이드바 영역 강제 적용 */
        section[data-testid="stSidebar"] * {{
            cursor: {cursor_css_value};
        }}
        
        /* 버튼, 입력창 등 인터랙티브 요소 강제 적용 */
        button, select, input, textarea, label, a, div[data-testid="stMetricValue"] {{
            cursor: {cursor_css_value};
        }}
        </style>
        """, unsafe_allow_html=True)

except Exception as e:
    # 네트워크 에러 등을 잡기 위해 포괄적인 예외 처리
    st.error(f"🚨 커서 설정 중 오류 발생: {e}")


# =============================================================================
# 4. 앱 전체 설정
# =============================================================================
st.markdown(
    """
    <!-- 구글 폰트 불러오기 -->
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans&display=swap" rel="stylesheet">
    <style>
        /* 전체 앱 폰트 변경 */
        html, body, [class*="css"] {
            font-family: 'Noto Sans', sans-serif;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    /* 사이드바 실제 컨텐츠 영역 */
    section[data-testid="stSidebar"] > div {
        background: linear-gradient(
            230deg,
            #FFFFFF 0%,
            #FFF1F2 50%,
            #E9353E 100%
        ) !important;

        border-right: 1px solid #E5E7EB;
    }

    /* 사이드바 글자 색 */
    section[data-testid="stSidebar"] * {
        color: #111827;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 기본 페이지 지정
st.set_page_config(
    page_title="광고 추천 시스템",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# 5. Session State 초기값 설정
# =============================================================================
if 'selected_industry' not in st.session_state:
    st.session_state['selected_industry'] = "음식"
if 'selected_os' not in st.session_state:
    st.session_state['selected_os'] = "Web"
if 'selected_month' not in st.session_state:
    st.session_state['selected_month'] = "1Q"


# =============================================================================
# 6. 페이지 정의 (st.Page)
# =============================================================================
home_page = st.Page(
    page="pages/home.py", 
    title="광고 데이터 정보",
    icon="📊",
    default=True
)

viz_page = st.Page(
    page="pages/TOP_3.py", 
    title="광고 추천 모델",
    icon="🔍"
)

info_page = st.Page(
    page="pages/information.py",
    title="대시보드 소개",
    icon="📋"
)


# =============================================================================
# 7. 네비게이션 구성
# =============================================================================
pg = st.navigation({
    "메인": [home_page, viz_page],
    "더보기": [info_page]
})


# =============================================================================
# 8. 공통 사이드바
# =============================================================================
with st.sidebar:
    st.header("🔍 광고 옵션 선택")

    st.selectbox(
        "산업군", 
        ["음식", "쇼핑/커머스","게임", "금융/보험", "건강/운동", "생활/유틸리티", "엔터테인먼트","법", "교육/학습"], 
        key='selected_industry'
    )
    
    st.selectbox(
        "OS 환경", 
        ["Web","Android", "iOS"], 
        key='selected_os'
    )
    
    st.selectbox(
        "분기 타입", 
        ["1Q", "2Q", "3Q", "4Q"], 
        key='selected_month'
    )
    

# =============================================================================
# 9. 실행
# =============================================================================
pg.run()