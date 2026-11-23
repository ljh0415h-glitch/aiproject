import glob
import os
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="외국인 입국자 현황 대시보드 (2011~2025)",
    page_icon="✈️",
    layout="wide",
)


def set_korean_font():
    candidates = ["NanumGothic", "Malgun Gothic", "AppleGothic", "Noto Sans CJK JP"]
    available = {f.name for f in fm.fontManager.ttflist}
    for font in candidates:
        if font in available:
            plt.rcParams["font.family"] = font
            break
    plt.rcParams["axes.unicode_minus"] = False


set_korean_font()


@st.cache_data
def load_data(file_or_path):
    for enc in ["utf-8-sig", "utf-8", "cp949", "euc-kr"]:
        try:
            df = pd.read_csv(file_or_path, encoding=enc)
            df.columns = [str(c).strip() for c in df.columns]

            year_col = next((c for c in ["년", "연도"] if c in df.columns), df.columns[0])
            country_col = next(
                (c for c in ["국적지역", "국적(지역)", "국적"] if c in df.columns),
                df.columns[1],
            )
            count_col = next(
                (c for c in ["입국자수", "입국자 수(명)", "입국자 수"] if c in df.columns),
                df.columns[2],
            )

            clean_df = pd.DataFrame(
                {
                    "년": pd.to_numeric(df[year_col], errors="coerce"),
                    "국적지역": df[country_col].astype(str).str.strip(),
                    "입국자수": pd.to_numeric(
                        df[count_col].astype(str).str.replace(",", "", regex=False),
                        errors="coerce",
                    ),
                }
            ).dropna(subset=["년", "국적지역", "입국자수"])

            clean_df["년"] = clean_df["년"].astype(int)
            clean_df["입국자수"] = clean_df["입국자수"].astype(int)
            return clean_df
        except Exception:
            continue
    raise ValueError("CSV 파일을 읽을 수 없습니다. 인코딩 또는 형식을 확인해 주세요.")


def find_repo_csv():
    preferred = [
        "법무부_3(출입국심사)연도별 국적(지역)별 외국인 입국자 현황_20251231 (1).csv",
        "법무부_3(출입국심사)연도별 국적(지역)별 외국인 입국자 현황_20251231.csv",
    ]
    for path in preferred:
        if os.path.exists(path):
            return path

    csv_files = sorted(glob.glob("*.csv"))
    return csv_files[0] if csv_files else None


st.title("✈️ 연도별·국적(지역)별 외국인 입국자 현황 (2011~2025)")
st.caption("법무부 출입국심사 통계 데이터 기반 인터랙티브 분석 대시보드")

auto_file = find_repo_csv()
uploaded_file = st.sidebar.file_uploader("CSV 파일 업로드 (선택)", type=["csv"])

if uploaded_file is not None:
    df = load_data(uploaded_file)
elif auto_file is not None:
    st.sidebar.success(f"자동 연결된 파일: `{auto_file}`")
    df = load_data(auto_file)
else:
    st.warning("레포지토리에 기본 CSV 파일이 없어요. 왼쪽 사이드바에서 CSV 파일을 업로드해 주세요.")
    st.stop()

st.sidebar.header("🔎 조회 옵션")
min_year, max_year = int(df["년"].min()), int(df["년"].max())
year_range = st.sidebar.slider(
    "분석 연도 범위",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
)

filtered_df = df[(df["년"] >= year_range[0]) & (df["년"] <= year_range[1])]

yearly_total = filtered_df.groupby("년", as_index=False)["입국자수"].sum().sort_values("년")
total_entries = int(filtered_df["입국자수"].sum())
latest_year = int(yearly_total["년"].iloc[-1])
latest_entries = int(yearly_total["입국자수"].iloc[-1])
top_country_latest = (
    filtered_df[filtered_df["년"] == latest_year]
    .sort_values("입국자수", ascending=False)
    .iloc[0]
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("선택 기간 누적 입국자", f"{total_entries:,}명")
col2.metric(f"{latest_year}년 전체 입국자", f"{latest_entries:,}명")
col3.metric(f"{latest_year}년 최다 입국 국적", f"{top_country_latest['국적지역']}")
col4.metric(f"{latest_year}년 1위 국적 입국자", f"{int(top_country_latest['입국자수']):,}명")

st.divider()

tab1, tab2, tab3 = st.tabs(["📈 연도별 전체 추이", "🏆 국적별 순위 비교", "📄 원본 데이터 및 다운로드"])

with tab1:
    st.subheader("연도별 전체 외국인 입국자 수 추이 (단위: 만 명)")
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(
        yearly_total["년"],
        yearly_total["입국자수"] / 10000,
        marker="o",
        linewidth=2.2,
        color="#2563eb",
    )
    ax.set
