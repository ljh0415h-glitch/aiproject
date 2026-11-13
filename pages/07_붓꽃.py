import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.neighbors import KNeighborsClassifier
import os

# 페이지 설정
st.set_page_config(page_title="붓꽃(Iris) 품종 예측기", page_icon="🌸", layout="wide")

st.title("🌸 붓꽃(Iris) 품종 예측 및 분류 시각화 대시보드")
st.markdown("꽃잎의 길이와 너비를 입력하면 가장 널리 쓰이는 **KNN(K-Nearest Neighbors) 분류 알고리즘**을 통해 어떤 품종인지 예측하고 시각적으로 보여줍니다.")

# 1. 데이터 로드 및 전처리
@st.cache_data
def load_data():
    possible_files = ['저장.csv', './저장.csv']
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
        st.error("❌ '저장.csv' 파일을 찾을 수 없습니다. GitHub 저장소에 파일을 업로드해주세요.")
        st.stop()

    df = None
    for enc in ['cp949', 'utf-8', 'euc-kr']:
        try:
            df = pd.read_csv(file_path, encoding=enc)
            break
        except Exception:
            continue
            
    if df is None:
        st.error("❌ 파일 인코딩 오류가 발생했습니다.")
        st.stop()
        
    return df

df = load_data()

# 데이터셋의 꽃잎 길이, 너비 최소/최대값 확인 (사용자 안내용)
petal_len_min, petal_len_max = float(df['꽃잎 길이'].min()), float(df['꽃잎 길이'].max())
petal_wid_min, petal_wid_max = float(df['꽃이 너비'].min()), float(df['꽃이 너비'].max())

# 2. 사이드바 사용자 입력
st.sidebar.header("🔍 붓꽃 특징 입력")
st.sidebar.markdown(f"**💡 입력 가능 범위 안내**")
st.sidebar.markdown(* **꽃잎 길이:** `{petal_len_min} cm ~ {petal_len_max} cm`")
st.sidebar.markdown(f"* **꽃잎 너비:** `{petal_wid_min} cm ~ {petal_wid_max} cm`")
st.sidebar.divider()

user_petal_length = st.sidebar.slider(
    "꽃잎 길이 (Petal Length, cm)",
    min_value=petal_len_min,
    max_value=petal_len_max,
    value=3.8,
    step=0.1
)

user_petal_width = st.sidebar.slider(
    "꽃잎 너비 (Petal Width, cm)",
    min_value=petal_wid_min,
    max_value=petal_wid_max,
    value=1.2,
    step=0.1
)

# 3. 모델 학습 (KNN 알고리즘 사용)
# 가로축: 꽃잎 길이, 세로축: 꽃잎 너비
X = df[['꽃잎 길이', '꽃이 너비']].values
y = df['품종'].values

# 가장 널리 쓰이는 분류 알고리즘 중 하나인 KNN (K=5 설정)
knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(X, y)

# 사용자 입력값 예측
user_input = np.array([[user_petal_length, user_petal_width]])
predicted_species = knn.predict(user_input)[0]

# 예측 확률(이웃들의 비율) 계산
probabilities = knn.predict_proba(user_input)[0]
classes = knn.classes_

# 4. 결과 요약 카드 출력
st.subheader("🎯 예측 결과")
col1, col2 = st.columns(2)
col1.metric(
    label="추정 품종 (Species)",
    value=f"✨ {predicted_species}"
)
col2.metric(
    label="입력한 특성값",
    value=f"꽃잎 길이: {user_petal_length}cm / 너비: {user_petal_width}cm"
)

# 5. 시각화 (가로축: 꽃잎 길이, 세로축: 꽃잎 너비)
st.divider()
st.subheader("📊 품종별 분포 및 사용자 입력값 시각화")
st.markdown("그래프 속 **초록색 별(★)**은 사용자가 입력한 데이터 위치입니다. KNN 알고리즘이 주변의 가장 가까운 5개의 이웃 데이터를 참고하여 다수결 방식으로 품종을 분류하는 원리를 확인할 수 있습니다.")

fig, ax = plt.subplots(figsize=(10, 6))

# Seaborn을 이용한 품종별 산점도 시각화
sns.scatterplot(
    data=df,
    x='꽃잎 길이',
    y='꽃이 너비',
    hue='품종',
    style='품종',
    s=70,
    palette='Set2',
    ax=ax
)

# 사용자가 입력한 값을 초록색 별로 표시
ax.scatter(
    [user_petal_length],
    [user_petal_width],
    color='limegreen',
    marker='*',
    s=300,
    edgecolor='black',
    linewidth=1.5,
    label=f'사용자 입력 ({predicted_species})',
    zorder=5
)

ax.set_title("꽃잎 길이와 너비에 따른 붓꽃 품종 분포 및 예측 위치", fontsize=14, fontweight='bold')
ax.set_xlabel("꽃잎 길이 (cm)", fontsize=12)
ax.set_ylabel("꽃이 너비 (cm)", fontsize=12)
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
st.pyplot(fig)

# 6. 알고리즘 작동 원리 설명
st.divider()
st.subheader("📘 KNN (K-Nearest Neighbors) 분류 알고리즘이란?")
st.markdown(f"""
* **작동 원리:** 새로운 데이터가 들어왔을 때, 2차원 공간(꽃잎 길이-너비 좌표평면)에서 **가장 가까운 거리에 있는 이웃 데이터 $K$개(여기서는 5개)**를 찾습니다.
* **분류 방식:** 가까운 5개의 이웃 중 가장 많이 분포하는 품종으로 최종 결론을 내립니다.
* **현재 입력값 분석:** 사용자가 입력하신 길이(`{user_petal_length}cm`), 너비(`{user_petal_width}cm`) 위치 주변의 데이터 특성을 반영하여 최종적으로 **`{predicted_species}`**(으)로 판정되었습니다.
""")
