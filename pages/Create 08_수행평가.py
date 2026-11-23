import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# 페이지 기본 설정
st.set_page_config(
    page_title="외국인 입국자 현황 대시보드 (2011~2025)",
    page_icon="✈️",
    layout="wide"
)

# 한글 폰트 설정 (리눅스/Streamlit Cloud 및 로컬 환경 대응)
def set_korean_font():
    candidates = ["NanumGothic", "Malgun Gothic", "AppleGothic", "Noto Sans CJK JP"]
    available = {f.name for f in fm.fontManager.ttflist}
    for font in candidates:
        if font in available:
            plt.rcParams["font.family"] = font
            break
    plt.rcParams["axes.unicode_minus"] = False

set_korean_font()

# CSV 파일 로드 (인코딩 자동 처리 + 캐싱)
@st.cache_data
def load_data(file_or_path):
    for enc in ["utf-8-sig", "utf-8", "cp949"]:
        try:
            df = pd.read_csv(file_or_path, encoding=enc)
            df.columns = [c.strip() for c in df.columns]
            df["년"] = pd.to_numeric(df["년"], errors="coerce")
            df["입국자수"] = pd.to_numeric(df["입국자수"], errors="coerce")
            df = df.dropna(subset=["년", "국적지역", "입국자수"]).copy()
            df["년"] = df["년"].astype(int)
            df["입국자수"] = df["입국자수"].astype(int)
            df["국적지역"] = df["국적지역"].astype(str).str.strip()
            return df
        except Exception:
            continue
    raise ValueError("CSV 파일을 읽을 수 없습니다. 인코딩 또는 형식을 확인해 주세요.")

st.title("✈️ 연도별·국적(지역)별 외국인 입국자 현황 (2011~2025)")
st.caption("법무부 출입국심사 통계 데이터 기반 인터랙티브 분석 대시보드")

default_file = "법무부_3(출입국심사)연도별 국적(지역)별 외국인 입국자 현황_20251231.csv"
uploaded_file = st.sidebar.file_uploader("CSV 파일 업로드 (선택)", type=["csv"])

if uploaded_file is not None:
    df = load_data(uploaded_file)
elif os.path.exists(default_file):
    df = load_data(default_file)
else:
    st.warning("레포지토리에 기본 CSV 파일이 없어요. 왼쪽 사이드바에서 CSV 파일을 업로드해 주세요.")
    st.stop()

# 사이드바 필터
st.sidebar.header("🔎 조회 옵션")
min_year, max_year = int(df["년"].min()), int(df["년"].max())
year_range = st.sidebar.slider(
    "분석 연도 범위",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

filtered_df = df[(df["년"] >= year_range[0]) & (df["년"] <= year_range[1])]

# 상단 핵심 지표(KPI)
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

# 탭 구성
tab1, tab2, tab3 = st.tabs(["📈 연도별 전체 추이", "🏆 국적별 순위 비교", "📄 원본 데이터 및 다운로드"])

with tab1:
    st.subheader("연도별 전체 외국인 입국자 수 추이 (단위: 만 명)")
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(yearly_total["년"], yearly_total["입국자수"] / 10000, marker="o", linewidth=2.2, color="#2563eb")
    ax.set_xticks(yearly_total["년"])
    ax.tick_params(axis="x", rotation=45)
    ax.set_ylabel("입국자 수 (만 명)")
    ax.grid(True, linestyle="--", alpha=0.5)
    for _, row in yearly_total.iterrows():
        val = row["입국자수"] / 10000
        ax.annotate(
            f"{val:,.0f}",
            (row["년"], val),
            textcoords="offset points",
            xytext=(0, 7),
            ha="center",
            fontsize=8
        )
    plt.tight_layout()
    st.pyplot(fig)
    st.dataframe(
        yearly_total.assign(**{"입국자수(명)": yearly_total["입국자수"].map(lambda x: f"{x:,}")})[["년", "입국자수(명)"]],
        use_container_width=True,
        hide_index=True
    )

with tab2:
    c1, c2 = st.columns([1, 2])
    with c1:
        selected_year = st.selectbox("기준 연도 선택", options=sorted(filtered_df["년"].unique(), reverse=True))
        top_n = st.slider("상위 N개국 표시", min_value=5, max_value=30, value=10)

    year_rank = (
        filtered_df[filtered_df["년"] == selected_year]
        .sort_values("입국자수", ascending=False)
        .head(top_n)
        .sort_values("입국자수", ascending=True)
    )

    with c2:
        st.subheader(f"{selected_year}년 국적(지역)별 입국자 상위 {top_n}개국 (단위: 만 명)")
        fig2, ax2 = plt.subplots(figsize=(9, 5))
        bars = ax2.barh(year_rank["국적지역"], year_rank["입국자수"] / 10000, color="#0d9488")
        ax2.set_xlabel("입국자 수 (만 명)")
        ax2.grid(True, axis="x", linestyle="--", alpha=0.5)
        for bar in bars:
            w = bar.get_width()
            ax2.annotate(
                f"{w:,.1f}만",
                (w, bar.get_y() + bar.get_height() / 2),
                textcoords="offset points",
                xytext=(4, 0),
                va="center",
                fontsize=8.5
            )
        ax2.set_xlim(0, year_rank["입국자수"].max() / 10000 * 1.15)
        plt.tight_layout()
        st.pyplot(fig2)

    st.subheader("특정 국적(지역) 연도별 추이 비교")
    all_countries = sorted(filtered_df["국적지역"].unique())
    default_countries = [c for c in ["중국", "일본", "타이완", "미국", "베트남"] if c in all_countries]
    picked_countries = st.multiselect("비교할 국적(지역) 선택", options=all_countries, default=default_countries)

    if picked_countries:
        country_pivot = (
            filtered_df[filtered_df["국적지역"].isin(picked_countries)]
            .pivot(index="년", columns="국적지역", values="입국자수")
            .fillna(0)
        )
        st.line_chart(country_pivot)

with tab3:
    search_keyword = st.text_input("국적(지역) 검색", placeholder="예: 중국, 일본, 베트남...")
    table_df = filtered_df.copy()
    if search_keyword.strip():
        table_df = table_df[table_df["국적지역"].str.contains(search_keyword.strip(), case=False, na=False)]

    st.dataframe(table_df.sort_values(["년", "입국자수"], ascending=[False, False]), use_container_width=True, hide_index=True)

    csv_bytes = table_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="필터링된 데이터 CSV 다운로드",
        data=csv_bytes,
        file_name=f"외국인_입국자_필터결과_{year_range[0]}_{year_range[1]}.csv",
        mime="text/csv"
    )
