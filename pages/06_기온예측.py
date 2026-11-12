import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
import plotly.graph_objects as go
import os

st.set_page_config(page_title="기온 예측 대시보드", page_icon="📈", layout="wide")

st.title("🌡️ 회귀 알고리즘별 월별 평균기온 예측 대시보드")
st.markdown("과거 기온 데이터를 바탕으로 선형회귀, 랜덤 포레스트, 서포트 벡터 머신(SVR) 알고리즘을 구동하여 미래 기온을 예측합니다.")

@st.cache_data
def load_data():
    possible_files = ['temperature.csv', 'temperature (1).csv', './temperature.csv']
    file_path = None
    for f in possible_files:
        if os.path.exists(f):
            file_path = f
            break
            
    if file_path is None:
        for f in os.listdir('.'):
            if f.endswith('.csv'):
                file_path = f
                break

    if file_path is None:
        st.error("temperature.csv 파일을 찾을 수 없습니다.")
        st.stop()

    df = None
    for enc in ['cp949', 'utf-8', 'euc-kr']:
        try:
            df = pd.read_csv(file_path, encoding=enc)
            break
        except Exception:
            continue
            
    if df is None:
        st.error("파일 인코딩 오류가 발생했습니다.")
        st.stop()

    month_map = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }

    parsed = df['일시'].str.split('-', expand=True)
    df['Month'] = parsed[0].map(month_map)
    yy = parsed[1].astype(int)

    years = []
    century = 1900
    prev_yy = None
    for y in yy:
        if prev_yy is not None and prev_yy == 99 and y == 0:
            century = 2000
        years.append(century + y)
        prev_yy = y

    df['Year'] = years
    df = df.dropna(subset=['평균기온(℃)']).copy()
    df['평균기온(℃)'] = pd.to_numeric(df['평균기온(℃)'], errors='coerce')
    df = df.dropna(subset=['평균기온(℃)'])
    
    return df

df = load_data()

st.sidebar.header("예측 조건 설정")

algo_option = st.sidebar.selectbox(
    "사용할 회귀 알고리즘을 선택하세요",
    [
        "선형회귀 (Linear Regression)", 
        "랜덤 포레스트 회귀 (Random Forest)", 
        "서포트 벡터 머신 (SVR)"
    ]
)

selected_month = st.sidebar.selectbox(
    "예측할 월을 선택하세요",
    list(range(1, 13)),
    index=7
)

target_year = st.sidebar.number_input(
    "예측할 연도를 입력하세요",
    min_value=2027,
    max_value=2150,
    value=2035,
    step=1
)

month_df = df[df['Month'] == selected_month].sort_values('Year')

if month_df.empty:
    st.warning("선택한 월에 해당하는 데이터가 없습니다.")
    st.stop()

X = month_df[['Year']].values
y = month_df['평균기온(℃)'].values

min_year = int(month_df['Year'].min())
max_year_data = int(month_df['Year'].max())
all_years = np.arange(min_year, target_year + 1).reshape(-1, 1)

if "선형회귀" in algo_option:
    model = LinearRegression()
    model.fit(X, y)
    predicted_temp = float(model.predict([[target_year]])[0])
    pred_curve = model.predict(all_years)
    slope = model.coef_[0]
    intercept = model.intercept_
    algo_name = "선형회귀 (Linear Regression)"
    algo_desc = "데이터의 전반적인 추세를 나타내는 하나의 직선(y = ax + b)을 최소제곱법으로 그립니다."

elif "랜덤 포레스트" in algo_option:
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    predicted_temp = float(model.predict([[target_year]])[0])
    pred_curve = model.predict(all_years)
    algo_name = "랜덤 포레스트 회귀 (Random Forest)"
    algo_desc = "수많은 결정 트리의 예측값 평균을 산출하여 비선형 패턴을 반영합니다."

else:
    scaler_x = StandardScaler()
    scaler_y = StandardScaler()
    X_scaled = scaler_x.fit_transform(X)
    y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()
    
    svr_model = SVR(kernel='rbf', C=100, gamma=0.1, epsilon=0.1)
    svr_model.fit(X_scaled, y_scaled)
    
    X_all_scaled = scaler_x.transform(all_years)
    pred_scaled = svr_model.predict(X_all_scaled)
    pred_curve = scaler_y.inverse_transform(pred_scaled.reshape(-1, 1)).ravel()
    predicted_temp = float(pred_curve[-1])
    algo_name = "서포트 벡터 머신 (SVR)"
    algo_desc = "RBF 커널을 사용하여 복잡한 곡선 형태의 비선형 관계를 정교하게 학습합니다."

col1, col2, col3 = st.columns(3)
col1.metric(f"{target_year}년 {selected_month}월 예측 기온", f"{predicted_temp:.2f} ℃")
col2.metric("선택된 알고리즘", algo_option.split("(")[0].strip())
col3.metric("기준 연도 대비 차이", f"{predicted_temp - y[-1]:+.2f} ℃")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=month_df['Year'], y=month_df['평균기온(℃)'],
    mode='lines+markers', name='과거 실제 기온'
))

past_mask = all_years.flatten() <= max_year_data
fig.add_trace(go.Scatter(
    x=all_years.flatten()[past_mask], y=pred_curve[past_mask],
    mode='lines', name='모델 학습선', line=dict(color='red', width=3)
))

future_mask = all_years.flatten() >= max_year_data
fig.add_trace(go.Scatter(
    x=all_years.flatten()[future_mask], y=pred_curve[future_mask],
    mode='lines', name='미래 예측선', line=dict(color='deeppink', width=3, dash='dash')
))

fig.add_trace(go.Scatter(
    x=[target_year], y=[predicted_temp],
    mode='markers+text', name='예측 지점',
    marker=dict(color='deeppink', size=14, symbol='star'),
    text=[f"{target_year}년: {predicted_temp:.2f}℃"], textposition="top center"
))

fig.update_layout(title=f"{selected_month}월 기온 예측 그래프", template="plotly_white", height=500)
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader(f"알고리즘 설명: {algo_name}")
st.write(algo_desc)
