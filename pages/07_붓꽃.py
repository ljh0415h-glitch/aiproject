import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
import os

# 1. 폰트 깨짐 방지를 위한 맷플롯립 설정 (마이너스 기호 깨짐 방지)
plt.rcParams['axes.unicode_minus'] = False

# 페이지 설정
st.set_page_config(page_title="Iris Species Prediction Dashboard", page_icon="🌸", layout="wide")

st.title("🌸 붓꽃(Iris) 품종 예측 및 분류 알고리즘 비교 대시보드")
st.markdown("꽃잎의 길이와 너비를 입력하고 **다양한 분류 알고리즘**을 선택하여 품종 예측 결과와 시각화 차이를 비교해 보세요.")

# 2. 안전한 데이터 로드 및 전처리
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
            temp_df = pd.read_csv(file_path, encoding=enc)
            if '품종' in temp_df.columns or '꽃잎 길이' in temp_df.columns:
                df = temp_df
                break
        except Exception:
            continue
            
    if df is None:
        try:
            df = pd.read_csv(file_path, encoding='cp949', errors='ignore')
        except:
            st.error("❌ 파일 인코딩 오류가 발생했습니다. '저장.csv' 파일을 확인해주세요.")
            st.stop()
        
    return df

df = load_data()

# 데이터셋 특징 최소/최대값 확인
petal_len_min, petal_len_max = float(df['꽃잎 길이'].min()), float(df['꽃잎 길이'].max())
petal_wid_min, petal_wid_max = float(df['꽃이 너비'].min()), float(df['꽃이 너비'].max())

# 3. 사이드바 사용자 입력 및 알고리즘 선택
st.sidebar.header("🔍 예측 설정 및 입력")

algo_option = st.sidebar.selectbox(
    "사용할 분류 알고리즘 선택",
    options=[
        "KNN (K-Nearest Neighbors)",
        "Random Forest (랜덤 포레스트)",
        "SVM (서포트 벡터 머신)"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**💡 입력 가능 범위 안내**")
st.sidebar.markdown(f"- **꽃잎 길이:** `{petal_len_min} cm ~ {petal_len_max} cm`")
st.sidebar.markdown(f"- **꽃잎 너비:** `{petal_wid_min} cm ~ {petal_wid_max} cm`")
st.sidebar.markdown("---")

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

# 4. 모델 학습 및 선택된 알고리즘 적용
X = df[['꽃잎 길이', '꽃이 너비']].values
y = df['품종'].values

if "KNN" in algo_option:
    model = KNeighborsClassifier(n_neighbors=5)
    algo_name = "KNN (K-Nearest Neighbors)"
    algo_desc = """
    * **작동 원리:** 새로운 데이터 주변에서 가장 가까운 $K$개(기본 5개)의 이웃 데이터를 찾아 다수결 방식으로 품종을 결정합니다.
    * **특징:** 직관적이며 데이터의 지역적 분포를 잘 반영합니다.
    """
elif "Random Forest" in algo_option:
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    algo_name = "Random Forest (랜덤 포레스트)"
    algo_desc = """
    * **작동 원리:** 수많은 의사결정 트리(Decision Tree)를 앙상블(집합)로 구성하여 각 트리가 예측한 결과의 다수결(투표)로 최종 품종을 분류합니다.
    * **특징:** 과적합에 강하고 비선형적인 데이터 경계를 정교하게 학습합니다.
    """
else:
    model = SVC(kernel='rbf', C=1, probability=True, random_state=42)
    algo_name = "SVM (서포트 벡터 머신)"
    algo_desc = """
    * **작동 원리:** 데이터들을 공간상에 두고, 각 품종 간의 경계(초평면, Hyperplane)를 최대 마진으로 나누는 결정 경계를 찾습니다. (RBF 커널 사용)
    * **특징:** 클래스 간의 경계가 복잡할 때 뛰어난 분류 성능을 보여줍니다.
    """

model.fit(X, y)

# 사용자 입력값 예측
user_input = np.array([[user_petal_length, user_petal_width]])
predicted_species = model.predict(user_input)[0]

# 5. 결과 요약 카드 출력
st.subheader("🎯 예측 결과 요약")
col1, col2, col3 = st.columns(3)
col1.metric(label="선택한 알고리즘", value=algo_option.split("(")[0].strip())
col2.metric(label="추정 품종 (Species)", value=f"✨ {predicted_species}")
col3.metric(label="입력 특성값", value=f"길이: {user_petal_length}cm / 너비: {user_petal_width}cm")

# 6. 시각화 (서버 폰트 깨짐 원천 차단을 위해 영문 축 및 레이블 사용)
st.divider()
st.subheader("📊 품종별 분포 및 사용자 입력 위치 시각화")
st.markdown("그래프 안의 **초록색 별(★)**은 사용자가 입력한 데이터 위치입니다. 선택한 머신러닝 알고리즘이 이 위치를 어떤 품종 영역으로 판단하는지 확인할 수 있습니다.")

fig, ax = plt.subplots(figsize=(10, 6))

sns.scatterplot(
    data=df,
    x='꽃잎 길이',
    y='꽃이 너비',
    hue='품종',
    style='품종',
    s=75,
    palette='Set2',
    ax=ax
)

# 사용자 입력 위치 표시
ax.scatter(
    [user_petal_length],
    [user_petal_width],
    color='limegreen',
    marker='*',
    s=350,
    edgecolor='black',
    linewidth=1.5,
    label=f'User Input ({predicted_species})',
    zorder=5
)

ax.set_title(f"Iris Species Distribution & Prediction using {algo_option.split('(')[0]}", fontsize=14, fontweight='bold')
ax.set_xlabel("Petal Length (cm)", fontsize=12)
ax.set_ylabel("Petal Width (cm)", fontsize=12)
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
st.pyplot(fig)

# 7. 알고리즘 설명 섹션
st.divider()
st.subheader(f"📘 선택된 알고리즘 설명: {algo_name}")
st.markdown(algo_desc)

st.info("💡 **팁:** 사이드바에서 알고리즘을 **KNN**, **Random Forest**, **SVM**으로 번갈아 선택해보세요. 알고리즘에 따라 분류 기준과 예측 성향이 어떻게 달라지는지 비교할 수 있습니다!")
