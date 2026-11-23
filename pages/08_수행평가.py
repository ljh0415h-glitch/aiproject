import glob
import os
import pandas as pd
import streamlit as st


def find_csv_file():
    candidates = [
        "법무부_3(출입국심사)연도별 국적(지역)별 외국인 입국자 현황_20251231 (1).csv",
        "법무부_3(출입국심사)연도별 국적(지역)별 외국인 입국자 현황_20251231.csv",
        "../법무부_3(출입국심사)연도별 국적(지역)별 외국인 입국자 현황_20251231 (1).csv",
        "../법무부_3(출입국심사)연도별 국적(지역)별 외국인 입국자 현황_20251231.csv",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path

    found = sorted(glob.glob("*.csv") + glob.glob("../*.csv") + glob.glob("../**/*.csv", recursive=True))
    return found[0] if found else None


@st.cache_data
def load_data(source):
    for enc in ["utf-8-sig", "utf-8", "cp949", "euc-kr"]:
        try:
            df = pd.read_csv(source, encoding=enc)
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
            if not clean_df.empty:
                return clean_df
        except Exception:
            continue
    return pd.DataFrame(columns=["년", "국적지역", "입국자수"])


auto_csv = find_csv_file()
uploaded_file = st.sidebar.file_uploader("CSV 파일 업로드 (선택)", type=["csv"])

if uploaded_file is not None:
    df = load_data(uploaded_file)
elif auto_csv is not None:
    df = load_data(auto_csv)
else:
    st.warning("CSV 파일을 찾을 수 없습니다. 왼쪽 사이드바에서 CSV 파일을 업로드해 주세요.")
    st.stop()

if df.empty or df["년"].dropna().empty:
    st.warning("유효한 연도 데이터가 없습니다. CSV 파일 내용을 확인해 주세요.")
    st.stop()

# 기존 93번째 줄 부근 (이제 안전하게 실행됨)
min_year, max_year = int(df["년"].min()), int(df["년"].max())
