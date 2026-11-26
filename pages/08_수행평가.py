from pathlib import Path
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="연도별·국적(지역)별 외국인 입국자 현황 (2011~2025)",
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


# CSV 파일이 없는 환경에서도 첫 화면에 통계가 바로 뜨도록 기본 연도별 합계 내장
DEFAULT_YEARLY_DATA = [
    (2011, 8666503),
    (2012, 10121950),
    (2013, 10678333),
    (2014, 14264508),
    (2015, 13359701),
    (2016, 17418307),
    (2017, 13569509),
    (2018, 15630522),
    (2019, 17880503),
    (2020, 2659845),
    (2021, 1044545),
    (2022, 3389007),
    (2023, 11499460),
    (2024, 16968203),
    (2025, 19584382),
]

DEFAULT_2025_TOP10 = [
    ("중국", 5515831),
    ("일본", 3691782),
    ("타이완", 1914732),
    ("미국", 1577117),
    ("베트남", 630493),
    ("필리핀", 629772),
    ("홍콩", 620521),
    ("싱가포르", 400915),
    ("인도네시아", 368863),
    ("태국", 350693),
]


def find_csv_file() -> Path | None:
    here = Path(__file__).resolve().parent
    search_dirs = [
        here,
        here.parent,
        here / "data",
        here.parent / "data",
        Path.cwd(),
        Path.cwd().parent,
    ]
    exact_names = [
        "법무부_3(출입국심사)연도별 국적(지역)별 외국인 입국자 현황_20251231 (1).csv",
        "법무부_3(출입국심사)연도별 국적(지역)별 외국인 입국자 현황_20251231.csv",
    ]

    for directory in search_dirs:
        if not directory.exists():
            continue
        for name in exact_names:
            target = directory / name
            if target.is_file():
                return target

    for directory in search_dirs:
        if not directory.exists():
            continue
        for csv_file in sorted(directory.glob("*.csv")):
            if "입국자" in csv_file.name or "법무부" in csv_file.name:
                return csv_file

    return None


@st.cache_data
def load_csv_df(source) -> pd.DataFrame:
    for enc in ["cp949", "euc-kr", "utf-8-sig", "utf-8"]:
        try:
            raw = pd.read_csv(source, encoding=enc)
            raw.columns = [str(c).strip() for c in raw.columns]

            year_col = next((c for c in ["년", "연도"] if c in raw.columns), None)
            country_col = next(
                (c for c in ["국적지역", "국적(지역)", "국적"] if c in raw.columns),
                None,
            )
            count_col = next(
                (c for c in ["입국자수", "입국자 수(명)", "입국자 수"] if c in raw.columns),
                None,
            )

            if not (year_col and country_col and count_col):
                continue

            cleaned = pd.DataFrame(
                {
                    "년": pd.to_numeric(raw[year_col], errors="coerce"),
                    "국적지역": raw[country_col].astype(str).str.strip(),
                    "입국자수": pd.to_numeric(
                        raw[count_col]
                        .astype(str)
                        .str.replace(",", "", regex=False)
                        .str.strip(),
                        errors="coerce",
                    ),
                }
            ).dropna(subset=["년", "국적지역", "입국자수"])

            cleaned["년"] = cleaned["년"].astype(int)
            cleaned["입국자수"] = cleaned["입국자수"].astype(int)

            if not cleaned.empty:
                return cleaned
        except Exception:
            continue

    return pd.DataFrame(columns=["년", "국적지역", "입국자수"])


def build_fallback_df() -> pd.DataFrame:
    rows = [{"년": yr, "국적지역": "전체합계", "입국자수": cnt} for yr, cnt in DEFAULT_YEARLY_DATA]
    for nat, cnt in DEFAULT_2025_TOP10:
        rows.append({"년": 2025, "국적지역": nat, "입국자수": cnt})
    return pd.DataFrame(rows)


st.title("✈️ 연도별·국적(지역)별 외국인 입국자 현황 (2011~2025)")
st.caption("법무부 출입국심사 통계 데이터 기반 인터랙티브 분석 대시보드")

uploaded_file = st.sidebar.file_uploader("다른 CSV 파일로 교체 (선택)", type=["csv"])
found_csv = find_csv_file()

if uploaded_file is not None:
    df = load_csv_df(uploaded_file)
    source_label = f"업로드 파일: {uploaded_file.name}"
elif found_csv is not None:
    loaded = load_csv_df(found_csv)
    if not loaded.empty:
        df = loaded
        source_label = f"저장소 CSV 연결됨: {found_csv.name}"
    else:
        df = build_fallback_df()
        source_label = "내장 통계 데이터 표시 중"
else:
    df = build_fallback_df()
    source_label = "내장 통계 데이터 표시 중 (CSV 업로드 시 전체 국적 반영)"

st.sidebar.info(source_label)

# '전체합계' 더미 행이 섞여 있는 경우 연도별 합계 계산 시 중복 방지
has_real_countries = (df["국적지역"] != "전체합계").any()
yearly_base = df[df["국적지역"] == "전체합계"] if (not has_real_countries and "전체합계" in df["국적지역"].values) else df
country_df = df[df["국적지역"] != "전체합계"].copy()

st.sidebar.header("🔎 조회 옵션")
min_year, max_year = int(yearly_base["년"].min()), int(yearly_base["년"].max())
year_range = st.sidebar.slider(
    "분석 연도 범위",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
)

filtered_yearly = yearly_base[
    (yearly_base["년"] >= year_range[0]) & (yearly_base["년"] <= year_range[1])
].copy()
filtered_country = country_df[
    (country_df["년"] >= year_range[0]) & (country_df["년"] <= year_range[1])
].copy()

yearly_total = (
    filtered_yearly.groupby("년", as_index=False)["입국자수"].sum().sort_values("년")
)
total_entries = int(yearly_total["입국자수"].sum())
latest_year = int(yearly_total["년"].iloc[-1])
latest_entries = int(yearly_total["입국자수"].iloc[-1])

latest_countries = filtered_country[filtered_country["년"] == latest_year].sort_values(
    "입국자수", ascending=False
)
top1_name = str(latest_countries.iloc[0]["국적지역"]) if not latest_countries.empty else "중국"
top1_count = int(latest_countries.iloc[0]["입국자수"]) if not latest_countries.empty else 5515831

col1, col2, col3, col4 = st.columns(4)
col1.metric("선택 기간 누적 입국자", f"{total_entries:,}명")
col2.metric(f"{latest_year}년 전체 입국자", f"{latest_entries:,}명")
col3.metric(f"{latest_year}년 최다 입국 국적", top1_name)
col4.metric(f"{latest_year}년 1위 국적 입국자", f"{top1_count:,}명")

st.divider()

tab1, tab2, tab3 = st.tabs(
    ["📈 연도별 전체 추이", "🏆 국적별 순위 비교", "📄 데이터 조회 및 다운로드"]
)

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
            fontsize=8,
        )
    plt.tight_layout()
    st.pyplot(fig)

    display_yr = yearly_total.copy()
    display_yr["전년 대비 증감(명)"] = display_yr["입국자수"].diff()
    st.dataframe(display_yr, use_container_width=True, hide_index=True)

with tab2:
    if filtered_country.empty:
        st.info("국적별 상세 데이터를 보려면 CSV 파일을 연결해 주세요.")
    else:
        c1, c2 = st.columns([1, 2])
        available_years = sorted(filtered_country["년"].unique(), reverse=True)
        with c1:
            selected_year = st.selectbox("기준 연도 선택", options=available_years)
            max_n = min(25, len(filtered_country[filtered_country["년"] == selected_year]))
            top_n = st.slider("상위 N개국 표시", min_value=3, max_value=max(3, max_n), value=min(10, max(3, max_n)))

        year_rank = (
            filtered_country[filtered_country["년"] == selected_year]
            .sort_values("입국자수", ascending=False)
            .head(top_n)
            .sort_values("입국자수", ascending=True)
        )

        with c2:
            st.subheader(f"{selected_year}년 국적(지역)별 입국자 상위 {len(year_rank)}개국 (단위: 만 명)")
            fig2, ax2 = plt.subplots(figsize=(9, 4.8))
            bars = ax2.barh(
                year_rank["국적지역"], year_rank["입국자수"] / 10000, color="#0d9488"
            )
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
                    fontsize=8.5,
                )
            ax2.set_xlim(0, year_rank["입국자수"].max() / 10000 * 1.15)
            plt.tight_layout()
            st.pyplot(fig2)

        st.subheader("특정 국적(지역) 연도별 추이 비교")
        all_countries = sorted(filtered_country["국적지역"].unique())
        default_picks = [c for c in ["중국", "일본", "타이완", "미국", "베트남"] if c in all_countries]
        picked = st.multiselect("비교할 국적(지역) 선택", options=all_countries, default=default_picks)
        if picked:
            pivot_df = (
                filtered_country[filtered_country["국적지역"].isin(picked)]
                .pivot_table(index="년", columns="국적지역", values="입국자수", aggfunc="sum", fill_value=0)
            )
            st.line_chart(pivot_df)

with tab3:
    keyword = st.text_input("국적(지역) 검색", placeholder="예: 중국, 일본, 타이완")
    table_df = filtered_country if not filtered_country.empty else filtered_yearly
    view_df = table_df.sort_values(["년", "입국자수"], ascending=[False, False]).copy()
    if keyword.strip() and "국적지역" in view_df.columns:
        view_df = view_df[
            view_df["국적지역"].str.contains(keyword.strip(), case=False, na=False)
        ]

    st.dataframe(view_df, use_container_width=True, hide_index=True)
    st.download_button(
        label="조회 결과 CSV 다운로드",
        data=view_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"외국인_입국자_{year_range[0]}_{year_range[1]}.csv",
        mime="text/csv",
    )
    
