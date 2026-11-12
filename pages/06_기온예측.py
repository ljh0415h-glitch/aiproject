import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go

# 페이지 기본 설정
st.set_page_config(page_title="기온 예측 대시보드", page_icon="🌡️", layout="wide")

st.title("🌡️ 월별 평균기온 추이 및 선형회귀 기온 예측")
st.markdown("과거 기온 데이터를 바탕으로 **선형회귀(Linear Regression)** 알고리즘을 학습시켜 미래의 특정 연도·월 평균기온을 예측합니다.")

# 1. 데이터 불러오기 및 전처리 함수
@st.cache_data
def load_data():
    # 인코딩 자동 처리 (cp949 또는 utf-8)
    for enc in ['cp949', 'utf-8', 'euc-kr']:
        try:
            df = pd.read_csv('temperature.csv', encoding=enc)
            break
        except Exception:
            continue

    # 월 영문 약자 매핑
    month_map = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }

    # 'Oct-07' 형태에서 월(Month)과 4자리 연도(Year) 정확히 복원
    # 데이터에 1907년~1926년과 2007년~2026년이 모두 존재하므로 순서 기반으로 연도 구분
    parsed = df['일시'].str.split('-', expand=True)
    df['Month'] = parsed[0].map(month_map)
    yy = parsed[1].astype(int)

    years = []
    century = 1900
    prev_yy = None
    for y in yy:
        # 99 -> 00으로 넘어갈 때 2000년대로 전환
        if prev_yy is not None and prev_yy == 99 and y == 0:
            century = 2000
        years.append(century + y)
        prev_yy = y

    df['Year'] = years
    # 평균기온 결측치(예: 1950년대 일부 누락 데이터) 제거
    df = df.dropna(subset=['평균기온(℃)']).copy()
    return df

df = load_data()

# 2. 사이드바 사용자 입력
st.sidebar.header("🔍 예측 조건 설정")
selected_month = st.sidebar.selectbox(
    "예측할 월(Month)을 선택하세요",
    options=list(range(1, 13)),
    index=7,  # 기본값: 8월
    format_func=lambda x: f"{x}월"
)

target_year = st.sidebar.number_input(
    "예측할 연도(Year)를 입력하세요",
    min_value=2027,
    max_value=2150,
    value=2035,
    step=1
)

# 3. 선택한 월 데이터 필터링 및 선형회귀 모델 학습
month_df = df[df['Month'] == selected_month].sort_values('Year')

X = month_df[['Year']].values          # 독립변수 (연도)
y = month_df['평균기온(℃)'].values      # 종속변수 (평균기온)

model = LinearRegression()
model.fit(X, y)

# 입력한 예측 연도의 기온 예측
predicted_temp = model.predict([[target_year]])[0]
slope = model.coef_[0]          # 기울기 (연간 기온 변화량)
intercept = model.intercept_    # y절편
r_squared = model.score(X, y)   # 결정계수 (R²)

# 회귀선(추세선)을 그리기 위한 연도 배열 생성 (과거 시작 연도 ~ 예측 연도)
min_year = int(month_df['Year'].min())
line_years = np.arange(min_year, target_year + 1).reshape(-1, 1)
line_temps = model.predict(line_years)

# 4. 핵심 결과 요약 카드 출력
col1, col2, col3 = st.columns(3)
col1.metric(
    label=f"🎯 {target_year}년 {selected_month}월 예측 평균기온",
    value=f"{predicted_temp:.2f} ℃"
)
col2.metric(
    label="📈 연간 평균 기온 상승률 (기울기)",
    value=f"{slope:+.4f} ℃/년",
    delta=f"10년당 {slope*10:+.2f} ℃ 변화"
)
col3.metric(
    label="📊 최근 관측 기온 대비 차이",
    value=f"{predicted_temp - y[-1]:+.2f} ℃",
    delta=f"{int(month_df['Year'].max())}년({y[-1]:.1f}℃) 기준"
)

# 5. Plotly 인터랙티브 그래프 시각화 (작동 원리가 한눈에 보이도록 구성)
fig = go.Figure()

# (1) 과거 실제 평균기온 데이터 (산점도 + 연도별 연결선)
fig.add_trace(go.Scatter(
    x=month_df['Year'],
    y=month_df['평균기온(℃)'],
    mode='lines+markers',
    name=f'과거 실제 {selected_month}월 평균기온 ({min_year}~{int(month_df["Year"].max())})',
    line=dict(color='rgba(100, 149, 237, 0.45)', width=1.5),
    marker=dict(color='#1f77b4', size=6),
    hovertemplate='%{x}년: %{y:.1f}℃<extra></extra>'
))

# (2) 선형회귀 추세선 (과거 구간 실선)
past_mask = line_years.flatten() <= month_df['Year'].max()
fig.add_trace(go.Scatter(
    x=line_years.flatten()[past_mask],
    y=line_temps[past_mask],
    mode='lines',
    name='선형회귀 학습 추세선 (최적의 직선)',
    line=dict(color='#ff4b4b', width=3),
    hovertemplate='추세선 (%{x}년): %{y:.2f}℃<extra></extra>'
))

# (3) 미래 외삽 구간 (현재 이후 ~ 예측 연도까지 점선으로 연장)
future_mask = line_years.flatten() >= month_df['Year'].max()
fig.add_trace(go.Scatter(
    x=line_years.flatten()[future_mask],
    y=line_temps[future_mask],
    mode='lines',
    name='미래 예측 연장선 (추세선 연장)',
    line=dict(color='#ff1493', width=3, dash='dash'),
    hovertemplate='예측 연장선 (%{x}년): %{y:.2f}℃<extra></extra>'
))

# (4) 최종 예측 지점 강조 마커
fig.add_trace(go.Scatter(
    x=[target_year],
    y=[predicted_temp],
    mode='markers+text',
    name=f'{target_year}년 예측 기온',
    marker=dict(color='#ff1493', size=14, symbol='star', line=dict(color='black', width=1.5)),
    text=[f"  <b>{target_year}년: {predicted_temp:.2f}℃</b>"],
    textposition="middle right",
    textfont=dict(color='#d6006e', size=13),
    hovertemplate=f'<b>{target_year}년 {selected_month}월 예측</b>: {predicted_temp:.2f}℃<extra></extra>'
))

# 그래프 레이아웃 및 수식 주석 추가
fig.update_layout(
    title=f"<b>[{selected_month}월] 연도별 평균기온 전체 추이 및 {target_year}년 선형회귀 예측</b>",
    xaxis_title="연도 (Year)",
    yaxis_title="평균기온 (℃)",
    hovermode="x unified",
    template="plotly_white",
    height=520,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    annotations=[
        dict(
            x=0.02, y=0.95, xref="paper", yref="paper",
            text=f"<b>학습된 회귀식:</b> 기온 = {slope:.4f} × 연도 + ({intercept:.2f})",
            showarrow=False,
            bgcolor="rgba(255, 240, 245, 0.9)",
            bordercolor="#ff1493",
            borderwidth=1,
            font=dict(size=13, color="#333333")
        )
    ]
)

st.plotly_chart(fig, use_container_width=True)

# 6. 그래프 하단: 선형회귀 알고리즘 작동 원리 설명
st.divider()
st.subheader("📘 선형회귀(Linear Regression) 알고리즘은 어떻게 작동하나요?")

st.markdown(f"""
위 그래프는 **단순 선형회귀(Simple Linear Regression)** 알고리즘이 과거 데이터를 학습해 미래를 예측하는 과정을 시각적으로 보여줍니다.

1. **데이터 학습 (파란색 점들):** 
   {min_year}년부터 {int(month_df['Year'].max())}년까지 관측된 **{selected_month}월의 실제 평균기온**을 좌표평면 위에 찍습니다. 해마다 날씨 변동으로 기온이 오르내리지만, 전체적인 흐름을 파악할 수 있습니다.
2. **최적의 직선 찾기 (빨간색 실선):** 
   선형회귀 알고리즘은 수많은 파란색 점들과 직선 사이의 **오차(잔차)의 제곱합이 가장 작아지는 단 하나의 직선(최소제곱법)**을 수학적으로 계산해 찾아냅니다.
   * **도출된 1차 함수 식:** $y = {slope:.4f}x + ({intercept:.2f})$
   * 여기서 **기울기({slope:.4f})**는 매년 평균기온이 평균적으로 몇 도씩 변하는지를 의미합니다.
3. **미래 기온 예측 (분홍색 점선 & ★ 별표):** 
   과거 데이터에서 찾아낸 직선의 기울기를 그대로 유지한 채 **{target_year}년**까지 직선을 쭉 연장(외삽, Extrapolation)하여, 해당 연도 위치의 직선 높이($y$값)를 읽으면 예측 기온인 **{predicted_temp:.2f}℃**가 도출됩니다.
""")
