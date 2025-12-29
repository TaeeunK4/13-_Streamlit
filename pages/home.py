# =============================================================================
# 광고 데이터 정보 페이지
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import os
from pathlib import Path
import altair as alt


# =============================================================================
# 1. CSS 설정
# =============================================================================
CARD_STYLE = """
padding:16px;
border-radius:12px;
box-shadow: 0 4px 12px rgba(0,0,0,0.1);
background-color:#ffffff;
margin-bottom:16px;
"""

TITLE_STYLE = "margin-bottom:8px; color:#333;"
VALUE_STYLE = "margin:0; color:#111; font-size:24px; font-weight:bold;"

st.markdown("""
<style>

/* ==============================
   3D 카드 스타일 (메인 컨테이너용)
============================== */
.card-3d {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 20px;
    width: 100%;
    box-shadow:
        0 4px 8px rgba(0,0,0,0.04),
        0 12px 24px rgba(0,0,0,0.08);
    border: 1px solid #F1F3F5;
}

/* ==============================
   KPI 카드 스타일
============================== */
.kpi-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 18px 20px;
    width: 100%;
    box-shadow:
        0 4px 10px rgba(0,0,0,0.05),
        0 12px 28px rgba(0,0,0,0.08);
    border: 1px solid #E5E7EB;
}

.kpi-title {
    font-size: 14px;
    color: #6B7280;
    margin-bottom: 6px;
}

.kpi-value {
    font-size: 26px;
    font-weight: 700;
    color: #111827;
}

.kpi-sub {
    font-size: 12px;
    color: #9CA3AF;
    margin-top: 4px;
}


# 클러스터 분석차트의 CSS
div[data-testid="stVerticalBlockBorderWrapper"] > div { 
    background: #FFFFFF;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.04), 0 12px 24px rgba(0,0,0,0.08);
    border: 1px solid #F1F3F5;

}
    
.chart-title {
    font-size: 20px;
    font-weight: bold;
    color: #333;
    margin-bottom: 15px;
}

</style>
""", unsafe_allow_html=True)


## ============================================================================
# 2. 제목 설정
## ============================================================================
st.markdown(
    """
    <h2 style="margin-top: -30px; margin-bottom: 10px;">📊 광고 데이터 정보</h2>
    """,
    unsafe_allow_html=True
)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)


# =============================================================================
# 3. 데이터 로드
# =============================================================================
# 3.1 경로 저장 및 데이터 캐싱
file_id = '1qjs2a461V2T_Da4I0lAQuLoGhJGA7bRN'
img_id = '13qhExXzYvumab9oZVeVDib-48ITarQBF'
csv_url = f'https://drive.google.com/uc?id={file_id}'
img_url = f'https://drive.google.com/uc?id={img_id}'

@st.cache_data
def load_data():
    try:
        return pd.read_csv(csv_url, encoding='euc-kr')
    except Exception as e:
        st.error(f"파일을 읽는 도중 오류가 발생했습니다. 구글 드라이브 공유 설정이 '링크가 있는 모든 사용자'로 되어 있는지 확인해주세요. 에러 내용: {e}")
        return None

mapping_df = load_data()

if mapping_df is not None:
    numeric_cols = ['rpt_time_turn', 'CVR']

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
            
            df[col] = df[col].fillna(0)

# 3.2 session_state 및 기본값 설정
industry = st.session_state.get('selected_industry', "음식")
os_input = st.session_state.get('selected_os', "Web")
month = st.session_state.get('selected_month', "1Q")


# =============================================================================
# 4.데이터 필터링
# =============================================================================
# 4.1 문자열 정리(공백 제거 + 소문자 변환)
mapping_df['ads_industry'] = mapping_df['ads_industry'].astype(str).str.strip()
mapping_df['ads_os_type'] = mapping_df['ads_os_type'].astype(str).str.strip().str.lower()
mapping_df['ads_month'] = mapping_df['ads_month'].astype(str).str.strip()

industry_clean = industry.strip()
os_input_clean = os_input.strip().lower()
month_clean = month.strip()

# 4.2 사용자 필터링
result_row = mapping_df[
    (mapping_df['ads_industry'] == industry_clean) &
    (mapping_df['ads_os_type'] == os_input_clean) &
    (mapping_df['ads_month'] == month_clean) &
    (mapping_df['Cluster'].notna())
]

# 4.3 클러스터 추출 및 예외 처리
if not result_row.empty:
    cluster_num = int(result_row['Cluster'].values[0]) 
    st.session_state['cluster_num'] = cluster_num
else:
    # 3등분 컬럼으로 가운데 정렬
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(img_url, width=500)
        # HTML로 가운데 정렬 + 줄바꿈
        st.markdown("""
            <div style="color: gray; text-align: center; margin-top: 10px;">
                찾으시는 조합의 데이터가 부족합니다.<br>
                다른 조건을 선택해 주세요.
            </div>
        """, unsafe_allow_html=True)
    st.stop()
    
cluster_num = int(cluster_num)

# 4.4 클러스터 파일 불러오기
@st.cache_data  
def load_df(cluster_n):
    cluster_file_ids = {
        0: '1poNHLx01sXmQ4EtkiE2FAL3doTdug-uX',
        1: '13eitQekyZ09qQGN7j3iaEq6YFR0vO9lh',
        2: '1Qeix85DvhQVQ5YRSa0vXRNoq_Xvmlp6Z',
        3: '1a8zYLAlXn8rXOGfASiyueRAE0FuFpxCU'
    }
    file_id = cluster_file_ids.get(cluster_n)

    if file_id:
        try:
            url = f'https://drive.google.com/uc?id={file_id}'
            return pd.read_csv(url, encoding='utf-8', index_col=0)
            
        except Exception as e:
            st.error(f"클러스터 {cluster_n} 파일을 불러오는 중 오류 발생: {e}")
            return None
    else:
        st.error(f"클러스터 {cluster_n}번에 해당하는 파일 ID 설정이 없습니다.")
        return None

filtered_df = load_df(cluster_num)


# =============================================================================
# 5. KPI
# =============================================================================
# 5.1 기초 프레임 구축
col1, col2, col3 = st.columns(3)

if not filtered_df.empty:
    cpa_value = filtered_df['CPA'].mean()
    cvr_value = filtered_df['CVR'].mean()*100
    display_cpa = f"{int(cpa_value):,}원"
    display_cvr = f"{cvr_value:.2f}%"
    time_turn_value = filtered_df['rpt_time_turn'].mean()
else:
    display_cpa = "-"
    display_cvr = "-"
    time_turn_value = "-"

try:
    temp_val = str(time_turn_value).replace(',', '').strip()
    
    if temp_val == '' or temp_val in ['-', 'None', 'nan', 'NaT']:
        safe_time_value = 0.0
    else:
        safe_time_value = float(temp_val)
except:
    safe_time_value = 0.0

col1, col2, col3 = st.columns(3, gap="small")

# 5.2 지표 설정
with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">TURN</div>
        <div class="kpi-value">{safe_time_value:.2f}</div>
        <div class="kpi-sub">전환 수 평균</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">CVR</div>
        <div class="kpi-value">{display_cvr}</div>
        <div class="kpi-sub">전환율 평균</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">CPA</div>
        <div class="kpi-value">{display_cpa}</div>
        <div class="kpi-sub">전환당 비용</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()


# =============================================================================
# 6. 클러스터 분포 차트
# =============================================================================
with st.container():
    st.markdown('<div class="full-width-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">📊 클러스터 분석 차트</div>', unsafe_allow_html=True)

    if 'cluster_num' in st.session_state and mapping_df is not None:
        c_num = st.session_state['cluster_num']
        
        target_df = mapping_df[mapping_df['Cluster'] == c_num].copy()

        if not target_df.empty:
            # (1) 산업군
            df_ind = target_df['ads_industry'].value_counts().reset_index()
            df_ind.columns = ['Label', 'Count']
            df_ind['Category'] = '산업군'

            # (2) OS
            df_os = target_df['ads_os_type'].value_counts().reset_index()
            df_os.columns = ['Label', 'Count']
            df_os['Category'] = 'OS'

            # (3) 분기
            def get_quarter(m):
                try: return f"{(int(str(m).replace('월',''))-1)//3 + 1}Q"
                except: return m
            
            target_df['quarter_conv'] = target_df['ads_month'].apply(get_quarter)
            df_qt = target_df['quarter_conv'].value_counts().reset_index()
            df_qt.columns = ['Label', 'Count']
            df_qt['Category'] = '분기'

            # (4) 데이터 합치기
            final_chart_df = pd.concat([df_ind, df_os, df_qt])

            # (5) 차트 생성
            chart = alt.Chart(final_chart_df).mark_bar(
                cornerRadiusTopLeft=5, 
                cornerRadiusTopRight=5
            ).encode(
                x=alt.X('Label', sort=None, title=None, axis=alt.Axis(labelAngle=0)), 
                y=alt.Y('Count', title='빈도수'),
                color=alt.Color('Category', title='구분', 
                                scale=alt.Scale(range=['#FF6C6C', '#4CA8FF', '#56D97D'])),
                tooltip=['Category', 'Label', 'Count']
            ).properties(
                height=300,
                width='container' 
            ).configure_axis(
                grid=False,
                labelFontSize=12
            ).configure_view(
                strokeWidth=0
            )
            
            st.altair_chart(chart, use_container_width=True)
        
        else:
            st.info("차트를 표시할 데이터가 없습니다.")
            
    else:
        st.warning("클러스터 정보나 매핑 데이터를 불러올 수 없습니다.")

    st.markdown('</div>', unsafe_allow_html=True)



st.text("") # 여백
st.text("") # 여백
st.text("") # 여백


# =============================================================================
# 7. 기술 통계
# =============================================================================
st.subheader("기술 통계")

tab1, tab2 = st.tabs(["요약 통계", "상관관계"])

with tab1:
    st.write("**필터링된 데이터의 기술 통계량**")
    stats_df = filtered_df.describe()
    st.dataframe(stats_df, width='stretch')

with tab2:
    st.write("**변수 간 상관관계**")
    numeric_cols = filtered_df.select_dtypes(include=[np.number]).columns
    corr_matrix = filtered_df[numeric_cols].corr()
    st.dataframe(
        corr_matrix.style.background_gradient(cmap='RdYlBu', vmin=-1, vmax=1),
        width='stretch'

    )



