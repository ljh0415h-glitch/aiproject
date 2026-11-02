import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="국가별 MBTI 비율 분석", page_icon="📊", layout="wide"
)

st.title("🌍 국가별 MBTI 16형태 분포 비교")
st.markdown(
    "국가를 선택하면 해당 국가의 MBTI 유형별 비율을 순위별 색상(1등 주황색, 나머지 파란색 그라데이션)으로 시각화해 줍니다."
)


# 데이터 로드 함수 (캐싱 적용)
@st.cache_data
def load_data():
  # 업로드해주신 파일명과 동일하게 지정
  df = pd.read_csv("countriesMBTI_16types.csv")
  return df


# 예외 처리를 통한 데이터 로드
try:
  df = load_data()
except FileNotFoundError:
  st.error(
      "⚠️ 'countriesMBTI_16types.csv' 파일을 찾을 수 없습니다. 코드와 같은"
      " 폴더에 데이터 파일을 업로드해 주세요."
  )
  st.stop()

# MBTI 유형 컬럼 리스트
mbti_cols = [
    "INFJ",
    "ISFJ",
    "INTP",
    "ISFP",
    "ENTP",
    "INFP",
    "ENTJ",
    "ISTP",
    "INTJ",
    "ESFP",
    "ESTJ",
    "ENFP",
    "ESTP",
    "ISTJ",
    "ENFJ",
    "ESFJ",
]

# 사이드바에서 국가 선택
st.sidebar.header("🔍 조회 설정")
country_list = sorted(df["Country"].unique())
selected_country = st.sidebar.selectbox(
    "국가를 선택하세요:", country_list, index=country_list.index("South Korea")
    if "South Korea" in country_list
    else 0
)

# 선택된 국가의 데이터 추출 및 정렬 (내림차순)
country_row = df[df["Country"] == selected_country]
mbti_values = country_row[mbti_cols].values.flatten()
mbti_df = pd.DataFrame({"MBTI": mbti_cols, "Ratio": mbti_values})
mbti_df = mbti_df.sort_values(by="Ratio", ascending=False).reset_index(
    drop=True
)

# 화면 레이아웃 구성
col1, col2 = st.columns([2, 1])

with col1:
  st.subheader(f"📍 {selected_country}의 MBTI 분포")

  # 그래프 색상 설정: 1등은 주황색(#ff7f0e), 나머지는 파란색 그라데이션
  colors = []
  n = len(mbti_df)
  for i in range(n):
    if i == 0:
      colors.append("#ff7f0e")  # 1등: 주황색
    else:
      # 파란색 계열에서 순위가 낮아질수록 알파값(투명도)을 주어 흐려지게 표현
      alpha = max(0.2, 1.0 - (i / n) * 0.8)
      colors.append((0.12, 0.47, 0.71, alpha))  # 기본 파란색 기반 그라데이션

  # Matplotlib 그래프 생성
  fig, ax = plt.subplots(figsize=(10, 6))
  bars = ax.bar(
      mbti_df["MBTI"],
      mbti_df["Ratio"] * 100,
      color=colors,
      edgecolor="black",
      linewidth=0.5,
  )

  ax.set_title(
      f"{selected_country} MBTI Distribution (%)", fontsize=14, fontweight="bold"
  )
  ax.set_ylabel("Ratio (%)", fontsize=12)
  ax.set_xlabel("MBTI Type", fontsize=12)
  plt.xticks(rotation=45)
  ax.grid(axis="y", linestyle="--", alpha=0.7)

  # 막대 위에 값 표시
  for bar in bars:
    height = bar.get_height()
    ax.annotate(
        f"{height:.1f}%",
        xy=(bar.get_x() + bar.get_width() / 2, height),
        xytext=(0, 3),  # 3 points vertical offset
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=9,
    )

  st.pyplot(fig)

with col2:
  st.subheader("📋 상세 순위표")
  display_df = mbti_df.copy()
  display_df["Ratio"] = (display_df["Ratio"] * 100).round(2).astype(str) + "%"
  display_df.index = display_df.index + 1
  st.dataframe(display_df, use_container_width=True)
