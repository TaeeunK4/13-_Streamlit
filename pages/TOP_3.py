# =============================================================================
# 광고 추천 모델 페이지
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import platform
import os
from pathlib import Path
import pickle
import itertools
from sklearn.preprocessing import RobustScaler
import altair as alt
from io import BytesIO
import requests


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
    font-size: 32px;
    color: #E85A4F;
    margin-left: 20px;
    font-weight: 650;
    margin-bottom: 15px;
}

.kpi-sub_title {
    font-size: 17px;
    color: #111827;
    margin-left: 20px;
}
        
.kpi-sub_title1 {
    font-size: 17px;
    color: #111827;
    margin-right: 15px;    
    margin-left: 20px;
}
    
.kpi-value {
    font-size: 18px;
    font-weight: 650;
    color: #E85A4F;
}

.kpi-sub {
    font-size: 12px;
    color: #9CA3AF;
    margin-top: 4px;
}

</style>
""", unsafe_allow_html=True)


## ============================================================================
# 2. 제목 설정
## ============================================================================

st.markdown(
    """
    <h2 style="margin-top: -30px;">🔍 광고 추천 모델</h2>
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

# 3.2 session_state 및 기본값 설정
industry = st.session_state.get('selected_industry', "음식")
os_input = st.session_state.get('selected_os', "Web")
month = st.session_state.get('selected_month', "1Q")

# 3.3 매핑 데이터 불러오기
@st.cache_data
def load_mapping_data():
    try:
        return pd.read_csv(csv_url, encoding='euc-kr')
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return None
    
mapping_df = load_mapping_data()


# 3.4 매핑 데이터 전처리
mapping_df['ads_industry'] = mapping_df['ads_industry'].astype(str).str.strip()
mapping_df['ads_os_type'] = mapping_df['ads_os_type'].astype(str).str.strip().str.lower()
mapping_df['ads_month'] = mapping_df['ads_month'].astype(str).str.strip()

industry_clean = industry.strip()
os_input_clean = os_input.strip().lower()
month_clean = month.strip()


## ============================================================================
# 4. 필터링
## ============================================================================
# 4.1 지정값 필터링
result_row = mapping_df[
    (mapping_df['ads_industry'] == industry_clean) &
    (mapping_df['ads_os_type'] == os_input_clean) &
    (mapping_df['ads_month'] == month_clean) &
    (mapping_df['Cluster'].notna())
]

# 4.1 클러스터 조합 찾기 및 session_state 저장
if not result_row.empty:
    cluster_num = int(result_row['Cluster'].values[0])  # 첫 번째 값
    st.session_state['cluster_num'] = cluster_num
    st.success(f"선택하신 조합은 [**{industry}** `|` **{os_input}** `|` **{month}**] 입니다.")
else:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(img_url, width=500)
        st.markdown("""
            <div style="color: gray; text-align: center; margin-top: 10px;">
                찾으시는 조합의 데이터가 부족합니다.<br>
                다른 조건을 선택해 주세요.
            </div>
        """, unsafe_allow_html=True)
    st.stop()

cluster_num = int(cluster_num)


## ============================================================================
# 5. 모델 데이터 로드
## ============================================================================
model_file_ids = {
    0: '1xk0W2wdysnjvHmrtCVHrhO9uJOTRiNEt',
    1: '1m7DOjyXOPRBXq3QFg2V7kZt1pgScytlj',
    2: '1OCsrjlwmgBApqInTt-hcKA9Z5JEPrDzp',
    3: '1q1KByQPLLwbdDDCEV2BcRoXS60CRhB_M'
}


@st.cache_resource
def load_model(cluster_n):
    # 해당 번호의 파일 ID 찾기
    file_id = model_file_ids.get(cluster_n)
    
    if not file_id:
        st.error(f"클러스터 {cluster_n}번에 해당하는 모델 파일 ID가 설정되지 않았습니다.")
        return None

    try:
        url = f"https://drive.google.com/uc?id={file_id}"
        response = requests.get(url)
        response.raise_for_status() # 다운로드 에러 체크

        file_stream = BytesIO(response.content)

        # 3. pickle로 로드
        return pickle.load(file_stream)

    except Exception as e:
        st.error(f"모델 로드 실패 (Cluster {cluster_n}): {e}")
        return None
    
# 5.2 해당 클러스터 불러오기    
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

# 5.4 함수 호출 및 저장
model = load_model(cluster_num)
df = load_df(cluster_num)


# =============================================================================
# 6. 예측 함수 및 TOP 리스트
# =============================================================================
@st.cache_resource
def prediction_TOP_3(df, _model):
    unique_conditions = df[['ads_shape', 'mda_idx', 'ads_time']].drop_duplicates()
    pred_cvr_log = _model['CVR'].predict(unique_conditions)
    pred_cvr = np.expm1(pred_cvr_log)
    pred_cpa_log = _model['CPA'].predict(unique_conditions)
    pred_cpa = np.expm1(pred_cpa_log)
    result_df = unique_conditions.copy()
    result_df['Pred_CVR'] = pred_cvr
    result_df['Pred_CPA'] = pred_cpa
    result_df['mda_idx'] = result_df['mda_idx'].astype(str)
    count_df = df.groupby(['ads_shape', 'mda_idx', 'ads_time']).size().reset_index(name='Data_Count')
    count_df['mda_idx'] = count_df['mda_idx'].astype(str)
    result_df = pd.merge(
        result_df,
        count_df,
        on=['ads_shape', 'mda_idx', 'ads_time'],
        how='left'
    )
    result_df['Data_Count'] = result_df['Data_Count'].fillna(0)
    result_df = result_df[result_df['Data_Count'] >= 20].copy()
    scaler = RobustScaler()
    scaled_vals = scaler.fit_transform(result_df[['Pred_CVR', 'Pred_CPA']])
    result_df['CVR_scaled'] = scaled_vals[:, 0]
    result_df['CPA_scaled'] = scaled_vals[:, 1]
    result_df['score'] = result_df['CVR_scaled'] + (1 - result_df['CPA_scaled'])
    top_10 = result_df.sort_values('score', ascending=False).head(10).copy()
    top = result_df.sort_values('score', ascending=False).head(3).copy()
    top['rank_label'] = [1,2,3]
    top1 = top[top['rank_label']==1].reset_index(drop=True)
    top2 = top[top['rank_label']==2].reset_index(drop=True)
    top3 = top[top['rank_label']==3].reset_index(drop=True)
    
    return top1, top2, top3, top, top_10
top1, top2, top3, top, top_10 = prediction_TOP_3(df, model)

 
# =============================================================================
# 7. TOP_3 출력
# =============================================================================
col1, col2, col3 = st.columns(3)

# 7.1 TOP_1
with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">TOP 1<span style='color:gray; font-size:18px; margin-left: 6px;'> [효율 점수 : {top1['score'].values[0]:.2f}] </span> </div>
        <div>
                <span class="kpi-sub_title1">수행 방식</span>
                <span class="kpi-value">
                <span style="color:black; font-weight:350;">:</span> {top1['ads_shape'].values[0]}</span>
        <div>
                <span class="kpi-sub_title">매체 플랫폼 :</span>
                <span class="kpi-value">{top1['mda_idx'].values[0]}</span>
            </div>
        <div>
                <span class="kpi-sub_title">시작 시간대 :</span>
                <span class="kpi-value">{top1['ads_time'].values[0]}</span>
            </div>
        <div class="kpi-sub">&nbsp;</div>
    </div>
    """, unsafe_allow_html=True
    )

# 7.2 TOP_2
with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">TOP 2<span style='color:gray; font-size:18px; margin-left: 6px;'> [효율 점수 : {top2['score'].values[0]:.2f}] </span> </div>
        <div>
                <span class="kpi-sub_title1">수행 방식</span>
                <span class="kpi-value">
                <span style="color:black; font-weight:350;">:</span> {top2['ads_shape'].values[0]}</span>
        <div>
                <span class="kpi-sub_title">매체 플랫폼 :</span>
                <span class="kpi-value">{top2['mda_idx'].values[0]}</span>
            </div>
        <div>
                <span class="kpi-sub_title">시작 시간대 :</span>
                <span class="kpi-value">{top2['ads_time'].values[0]}</span>
            </div>
        <div class="kpi-sub">&nbsp;</div>
    </div>
    """, unsafe_allow_html=True
    )

# 7.3 TOP_3
with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">TOP 3<span style='color:gray; font-size:18px; margin-left: 6px;'> [효율 점수 : {top3['score'].values[0]:.2f}] </span> </div>
        <div>
                <span class="kpi-sub_title1">수행 방식</span>
                <span class="kpi-value">
                <span style="color:black; font-weight:350;">:</span> {top3['ads_shape'].values[0]}</span>
        <div>
                <span class="kpi-sub_title">매체 플랫폼 :</span>
                <span class="kpi-value">{top3['mda_idx'].values[0]}</span>
            </div>
        <div>
                <span class="kpi-sub_title">시작 시간대 :</span>
                <span class="kpi-value">{top3['ads_time'].values[0]}</span>
            </div>
        <div class="kpi-sub">&nbsp;</div>
    </div>
    """, unsafe_allow_html=True
    )

st.divider()


# =============================================================================
# 8. 예산안
# =============================================================================
st.subheader("광고 예산안 배분")


# 8.1 도넛 차트
top_chart = top.copy()
rank_order = ['TOP 1', 'TOP 2', 'TOP 3']
color_range = ['#FF6C6C', '#4CA8FF', '#56D97D']

# 8.2 수식 계산(예산 분배 방법)
total_score = top_chart['score'].sum()
top_chart['rate_val'] = (top_chart['score'] / total_score) * 100 
top_chart['rate_val'] = top_chart['rate_val'].round(1)
top_chart['rate_str'] = top_chart['rate_val'].astype(str) + "%"
top_chart['rank_label'] = [f'TOP {i+1}' for i in range(len(top_chart))]

# 8.3 차트 및 범례 생성
base = alt.Chart(top_chart).encode(
    theta=alt.Theta("rate_val", stack=True) 
)

pie = base.mark_arc(outerRadius=110, innerRadius=65).encode(
    color=alt.Color("rank_label", 
                    scale=alt.Scale(domain=rank_order, range=color_range),
                    sort=rank_order,
                    legend=alt.Legend(
                        orient='none',       
                        legendX=48,           
                        legendY=20,          
                        direction='vertical', 
                        title=None,             
                        labelFontSize=16,       
                        symbolType='circle'     
                    )),
    order=alt.Order("rank_label", sort="ascending"), 
    tooltip=["rank_label", "rate_str"] 
)

# 8.4 도넛 위에 라벨
text = base.mark_text(radius=155, fontSize=24).encode(
    text=alt.Text("rate_str"),
    order=alt.Order("rank_label", sort="ascending"),
    color=alt.value("black")  
)

chart = (pie + text).properties(
    height=350
)

st.altair_chart(chart, use_container_width=True)

st.divider()


# =============================================================================
# 9. TOP_10
# =============================================================================
st.subheader("TOP 10")
tab1, tab2 = st.tabs(["광고 형태 추천","추가 설명"])

# 9.1 TOP_15 표
with tab1:
    stats_df = top_10
    st.dataframe(stats_df, width='stretch', height='stretch')

# 9.2 추가 설명
with tab2:
    st.write("🔍 계산 과정")
    st.markdown("""
    <div><p> 광고 효율 점수(Efficiency)를 기준으로 상위 광고 캠페인 추천</p>
            <p style= 'color:gray; margin:2px 0;'>* 광고 효율 점수: CVR + (1-CPA)</p>
            <p style= 'color:gray; margin:2px 0;'>* CVR은 성능지표라 높을수록 효과적</p>
            <p style= 'color:gray; margin:2px 0;'>* CPA는 클릭당 비용이라 낮을수록 효율적</p>
            <p style= 'color:gray; margin:2px 0;'>→  <b>즉, 광고 효율 점수가 높을수록</b> 👍🏻</p>
    </div>          
    """, unsafe_allow_html=True)