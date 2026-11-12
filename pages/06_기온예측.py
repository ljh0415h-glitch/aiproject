import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
import plotly.graph_objects as go

# 페이지 기본 설정
st.set_page_config(page_title="기온 예측 대시보드", page_icon="📈", layout="wide")

st.title("🌡️ 회귀 알고리즘별 월별 평균기온 예측 대시보드")
st.markdown("과거 기온 데이터를 바탕으로 **선형회귀**, **랜덤 포레스트**, **서포트 벡터 머신(SVR)** 알고리즘을 안전하게 구동하여 미래 기온을 예측합니다.")

# 1. 안전한 데이터 불러오기 및 전처리 함수
@st.cache_data
def load_data():
    df = None
    for enc in ['cp949', 'utf-8', 'euc-kr', 'latin1']:
        try:
            df = pd.read_csv('temperature.csv', encoding=enc)
            break
        except Exception:
            continue
            
    if df is None:
        st.error("❌ 'temperature.csv' 파일을 불러오지 못했습니다. 파일명을 확인해주세요.")
        st.stop()

    month_map = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }

    try:
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
    except Exception as e:
        st.error(f"❌ 데이터 전처리 중 오류가 발생했습니다: {e}")
        st.stop()

    df = df.dropna(subset=['평균기온(℃)']).copy()
    df['평균기온(℃)'] = pd.to_numeric(df['평균기온(℃)'], errors='coerce')
    df = df.dropna(subset=['평균기온(℃)'])
    
    return df

df = load_data()

# 2. 사이드바 사용자 입력
st.sidebar.header("🔍 예측 조건 설정")

algo_option = st.sidebar.selectbox(
    "사용할 회귀 알고리즘을 선택하세요",
    options=[
        "선형회귀 (Linear Regression)", 
        "랜덤 포레스트 회귀 (Random Forest)", 
        "서포트 벡터 머신 (SVR)"
    ]
)

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

# 3. 데이터 필터링
month_df = df[df['Month'] == selected_month].sort_values('Year')

if month_df.empty:
    st.warning(f"⚠️ {selected_month}월에 해당하는 데이터가 존재하지 않습니다.")
    st.stop()

X = month_df[['Year']].values
y = month_df['평균기온(℃)'].values

min_year = int(month_df['Year'].min())
max_year_data = int(month_df['Year'].max())
all_years = np.arange(min_year, target_year + 1).reshape(-1, 1)

# 4. 알고리즘 모델 학습 및 안전 예측
try:
    if "선형회귀" in algo_option:
        model = LinearRegression()
        model.fit(X, y)
        predicted_temp = float(model.predict([[target_year]])[0])
        pred_curve = model.predict(all_years)
        
        slope = model.coef_[0]
        intercept = model.intercept_
        algo_name = "선형회귀 (Linear Regression)"
        algo_desc = (
            f"* **작동 원리:** 데이터의 전반적인 추세를 가장 잘 대변하는 **하나의 직선($y = ax + b$)**을 그립니다. "
            f"최소제곱법을 이용해 오차의 합이 최소가 되는 기울기({slope:.4f})와 절편을 찾습니다.\n"
            "* **특징:** 장기적인 온난화 트렌드나 일정한 증가·감소 경향을 파악하기에 직관적이고 강력합니다."
        )

    elif "랜덤 포레스트" in algo_option:
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        predicted_temp = float(model.predict([[target_year]])[0])
        pred_curve = model.predict(all_years)
        
        algo_name = "랜덤 포레스트 회귀 (Random Forest)"
        algo_desc = (
            "* **작동 원리:** 수많은 **결정 트리(Decision Tree)**를 앙상블로 구성하여 각 트리가 낸 예측값들의 **평균**을 산출합니다.\n"
            "* **특징:** 데이터의 비선형적 패턴과 과거의 국소적인 변동을 유연하게 반영합니다."
        )

    else:  # SVR
        scaler_x = StandardScaler()
        scaler_y = StandardScaler()
        
        X_scaled = scaler_x.fit_transform(X)
        y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()
        
        svr_model = SVR(kernel='rbf', C=100, gamma=0.1, epsilon=0.1)
        svr_model.fit(X_scaled, y_scaled)
        
        X_all_scaled = scaler_x.transform
        
