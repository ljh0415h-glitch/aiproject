import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# -----------------------------------------------------------------------------
# 1. 페이지 및 한글 폰트 설정 (한글 깨짐 완벽 방지)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="대전광역시 인구 구조 분석", layout="wide")

@st.cache_resource
def init_korean_font():
    """Streamlit Cloud(Linux) 및 로컬 환경에서 한글 폰트를 강제 설정합니다."""
    nanum_font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
    
    if os.path.exists(nanum_font_path):
        font_prop = fm.FontProperties(fname=nanum_font_path)
        font_name = font_prop.get_name()
        plt.rc('font', family=font_name)
    else:
        import platform
        sys_name = platform.system()
        if sys_name == 'Windows':
            plt.rc('font', family='Malgun Gothic')
        elif sys_name == 'Darwin':
            plt.rc('font', family='AppleGothic')
            
    plt.rc('axes', unicode_minus=False)

init_korean_font()

# -----------------------------------------------------------------------------
# 2. 데이터 로드 및 전처리 (상위 폴더 참조)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    file_path_xlsx = os.path.join(os.path.dirname(__file__), '..', 'population.xlsx')
    file_path_csv = os.path.join(os.path.dirname(__file__), '..', 'population.csv')
    
    if os.path.exists(file_path_xlsx):
        df_raw = pd.read_excel(file_path_xlsx)
    elif os.path.exists(file_path_csv):
        df_raw = pd.read_csv(file_path_csv, encoding='utf-8-sig')
    else:
        if os.path.exists('population.xlsx'):
            df_raw = pd.read_excel('population.xlsx')
        elif os.path.exists('population.csv'):
            df_raw = pd.read_csv('population.csv', encoding='utf-8-sig')
        else:
            st.error("상위 폴더에 'population.xlsx' 또는 'population.csv' 파일이 없습니다.")
            st.stop()
            
    year_row = df_raw.iloc[0].ffill()
    gender_row = df_raw.iloc[1].ffill()
    detail_row = df_raw.iloc[2]
    
    new_cols = []
    for y, g, d in zip(year_row, gender_row, detail_row):
        if pd.isna(y) and pd.isna(g):
            new_cols.append(str(d).strip())
        else:
            new_cols.append(f"{str(y).strip()}_{str(g).strip()}_{str(d).strip()}")
            
    df = df_raw.iloc[3:].copy()
    df.columns = new_cols
    
    for col in df.columns:
        if col not in ['행정기관코드', '행정기관']:
            df[col] = df[col].astype(str).str.replace(',', '').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    df['행정기관'] = df['행정기관'].astype(str).str.strip()
    return df

df = load_data()

# -----------------------------------------------------------------------------
# 3. 사이드바 메뉴 및 조건 선택
# -----------------------------------------------------------------------------
st.title("📈 대전광역시 연령별 인구수 분석 대시보드")

st.sidebar.header("⚙️ 분석 메뉴 선택")
menu = st.sidebar.radio("원하는 분석을 선택하세요", [
    "1. 행정구별 연령대 인구 (꺾은선)", 
    "2. 연령대별 최다 인구 행정구 (막대)",
    "3. [추가] 연도별 인구 증감 비교"
], key="main_menu_radio")

# 공통 폰트 설정용 변수
nanum_font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
if os.path.exists(nanum_font_path):
    label_font = fm.FontProperties(fname=nanum_font_path, size=12)
    title_font = fm.FontProperties(fname=nanum_font_path, size=14)
else:
    label_font = None
    title_font = None

age_bins = ['0~9세', '10~19세', '20~29세', '30~39세', '40~49세', 
            '50~59세', '60~69세', '70~79세', '80~89세', '90~99세', '100세 이상']

# -----------------------------------------------------------------------------
# [기능 1] 행정구별 연령대 인구 꺾은선 그래프 (남: 핑크, 여: 초록)
# -----------------------------------------------------------------------------
if menu == "1. 행정구별 연령대 인구 (꺾은선)":
    st.subheader("📊 행정구 및 성별 연령대별 인구수 꺾은선 그래프")
    
    st.sidebar.markdown("---")
    selected_region = st.sidebar.selectbox("행정구 선택", df['행정기관'].unique().tolist(), key="menu1_region")
    selected_year = st.sidebar.radio("연도 선택", ["2024년", "2025년"], key="menu1_year")
    
    region_row = df[df['행정기관'] == selected_region].iloc[0]
    
    # 남녀 데이터 각각 추출
    male_vals = [region_row[f"{selected_year}_남_{age}"] for age in age_bins]
    female_vals = [region_row[f"{selected_year}_여_{age}"] for age in age_bins]
    
    fig, ax = plt.subplots(figsize=(11, 6))
    
    # 남성: 핑크색 (#FF69B4), 여성: 초록색 (#2ECC71) 적용
    ax.plot(age_bins, male_vals, marker='o', color='#FF69B4', linewidth=2.5, markersize=7, label='남성')
    ax.plot(age_bins, female_vals, marker='s', color='#2ECC71', linewidth=2.5, markersize=7, label='여성')
    
    ax.set_title(f"[{selected_region}] {selected_year} 성별 연령대별 인구 분포", fontproperties=title_font, pad=15)
    ax.set_xlabel("나이 (연령대)", fontproperties=label_font, labelpad=10)
    ax.set_ylabel("인구수 (명)", fontproperties=label_font, labelpad=10)
    
    ax.set_xticks(range(len(age_bins)))
    ax.set_xticklabels(age_bins, rotation=30)
    
    # Y축 10만 단위 눈금 설정
    all_vals = male_vals + female_vals
    max_pop = max(all_vals) if all_vals else 100000
    y_max_limit = max(100000, (int(max_pop // 100000) + 2) * 100000)
    ax.set_yticks(range(0, y_max_limit, 100000))
    
    ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    ax.grid(True, linestyle='--', alpha=0.6, color='gray')
    ax.legend()
    
    st.pyplot(fig)
    
    with st.expander("📊 상세 수치 표로 보기"):
        summary_df = pd.DataFrame({"연령대": age_bins, "남성 인구수": male_vals, "여성 인구수": female_vals})
        st.dataframe(summary_df)

# -----------------------------------------------------------------------------
# [기능 2] 특정 연령대에서 인구가 가장 많은 행정구 막대 그래프
# -----------------------------------------------------------------------------
elif menu == "2. 연령대별 최다 인구 행정구 (막대)":
    st.subheader("📊 연령대별 자치구 인구 비교 및 순위 (막대 그래프)")
    
    st.sidebar.markdown("---")
    selected_age = st.sidebar.selectbox("조회할 연령대 선택", age_bins, key="menu2_age")
    selected_gender_lbl = st.sidebar.radio("성별", ["계(전체)", "남성", "여성"], key="menu2_gender")
    selected_year = st.sidebar.radio("연도 선택", ["2024년", "2025년"], key="menu2_year")
    
    gender_code = "계" if "계" in selected_gender_lbl else ("남" if "남성" in selected_gender_lbl else "여")
    
    # 자치구별(대전광역시 전체 제외한 5개 구) 데이터 추출
    sub_df = df[df['행정기관'] != '대전광역시'].copy()
    col_name = f"{selected_year}_{gender_code}_{selected_age}"
    
    regions = sub_df['행정기관'].tolist()
    populations = sub_df[col_name].tolist()
    
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(regions, populations, color='#3498DB', width=0.5)
    
    # 가장 인구가 많은 구를 강조하기 위해 색상 변경
    if populations:
        max_idx = populations.index(max(populations))
        bars[max_idx].set_color('#E74C3C') # 최다 인구 지역은 빨간색 강조
        
    ax.set_title(f"[{selected_year}] {selected_age} ({selected_gender_lbl}) 자치구별 인구 현황", fontproperties=title_font, pad=15)
    ax.set_xlabel("행정구", fontproperties=label_font, labelpad=10)
    ax.set_ylabel("인구수 (명)", fontproperties=label_font, labelpad=10)
    
    ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    ax.grid(axis='y', linestyle='--', alpha=0.6, color='gray')
    
    st.pyplot(fig)
    
    top_region = regions[populations.index(max(populations))] if populations else ""
    st.success(f"🏆 **{selected_age}** ({selected_gender_lbl}) 기준 인구가 가장 많은 행정구는 **{top_region}**입니다!")

# -----------------------------------------------------------------------------
# [기능 3] 추가 기능: 연도별(2024 vs 2025) 총인구 증감 비교
# -----------------------------------------------------------------------------
elif menu == "3. [추가] 연도별 인구 증감 비교":
    st.subheader("📈 2024년 대비 2025년 행정구별 총인구 증감 비교")
    
    sub_df = df[df['행정기관'] != '대전광역시'].copy()
    
    regions = sub_df['행정기관'].tolist()
    pop_2024 = sub_df['2024년_계_총 인구수'].tolist()
    pop_2025 = sub_df['2025년_계_총 인구수'].tolist()
    
    diffs = [p25 - p24 for p24, p25 in zip(pop_2024, pop_2025)]
    
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ['#2ECC71' if d >= 0 else '#E74C3C' for d in diffs]
    
    bars = ax.bar(regions, diffs, color=colors, width=0.5)
    ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
    
    ax.set_title("대전광역시 자치구별 1년간 인구 증감량 (2024 → 2025)", fontproperties=title_font, pad=15)
    ax.set_xlabel("행정구", fontproperties=label_font, labelpad=10)
    ax.set_ylabel("인구 증감수 (명)", fontproperties=label_font, labelpad=10)
    
    ax.grid(axis='y', linestyle='--', alpha=0.6, color='gray')
    st.pyplot(fig)
    
    # 표 형태 제공
    diff_df = pd.DataFrame({
        "행정구": regions,
        "2024년 총인구": pop_2024,
        "2025년 총인구": pop_2025,
        "증감수": diffs
    })
    st.dataframe(diff_df)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# -----------------------------------------------------------------------------
# 1. 페이지 및 한글 폰트 강제 설정 (글자 깨짐 완벽 방지)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="대전광역시 인구 구조 분석", layout="wide")

def setup_korean_font():
    """Linux(Streamlit Cloud) 및 로컬 환경에서 폰트를 등록하고 기본 설정합니다."""
    nanum_font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
    
    if os.path.exists(nanum_font_path):
        # 폰트 파일 직접 등록
        fm.fontManager.addfont(nanum_font_path)
        font_prop = fm.FontProperties(fname=nanum_font_path)
        font_name = font_prop.get_name()
        
        # 맷플롯립 기본 폰트 패밀리 지정
        plt.rcParams['font.family'] = font_name
    else:
        # 로컬 환경 (Windows / Mac)
        import platform
        sys_name = platform.system()
        if sys_name == 'Windows':
            plt.rcParams['font.family'] = 'Malgun Gothic'
        elif sys_name == 'Darwin':
            plt.rcParams['font.family'] = 'AppleGothic'
            
    # 마이너스(-) 기호 깨짐 방지
    plt.rcParams['axes.unicode_minus'] = False

setup_korean_font()

# -----------------------------------------------------------------------------
# 2. 데이터 로드 및 전처리 (상위 폴더 참조)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    file_path_xlsx = os.path.join(os.path.dirname(__file__), '..', 'population.xlsx')
    file_path_csv = os.path.join(os.path.dirname(__file__), '..', 'population.csv')
    
    if os.path.exists(file_path_xlsx):
        df_raw = pd.read_excel(file_path_xlsx)
    elif os.path.exists(file_path_csv):
        df_raw = pd.read_csv(file_path_csv, encoding='utf-8-sig')
    else:
        if os.path.exists('population.xlsx'):
            df_raw = pd.read_excel('population.xlsx')
        elif os.path.exists('population.csv'):
            df_raw = pd.read_csv('population.csv', encoding='utf-8-sig')
        else:
            st.error("상위 폴더에 'population.xlsx' 또는 'population.csv' 파일이 없습니다.")
            st.stop()
            
    year_row = df_raw.iloc[0].ffill()
    gender_row = df_raw.iloc[1].ffill()
    detail_row = df_raw.iloc[2]
    
    new_cols = []
    for y, g, d in zip(year_row, gender_row, detail_row):
        if pd.isna(y) and pd.isna(g):
            new_cols.append(str(d).strip())
        else:
            new_cols.append(f"{str(y).strip()}_{str(g).strip()}_{str(d).strip()}")
            
    df = df_raw.iloc[3:].copy()
    df.columns = new_cols
    
    for col in df.columns:
        if col not in ['행정기관코드', '행정기관']:
            df[col] = df[col].astype(str).str.replace(',', '').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    df['행정기관'] = df['행정기관'].astype(str).str.strip()
    return df

df = load_data()

# -----------------------------------------------------------------------------
# 3. 사이드바 메뉴 선택
# -----------------------------------------------------------------------------
st.title("📈 대전광역시 연령별 인구수 분석 대시보드")

st.sidebar.header("⚙️ 분석 메뉴 선택")
menu = st.sidebar.radio(
    "원하는 분석을 선택하세요", 
    [
        "1. 행정구별 연령대 인구 (꺾은선)", 
        "2. 연령대별 최다 인구 행정구 (막대)",
        "3. 연도별 인구 증감 비교"
    ], 
    key="main_menu_navigation_radio"
)

age_bins = ['0~9세', '10~19세', '20~29세', '30~39세', '40~49세', 
            '50~59세', '60~69세', '70~79세', '80~89세', '90~99세', '100세 이상']

# -----------------------------------------------------------------------------
# [기능 1] 행정구별 연령대 인구 꺾은선 그래프 (남: 핑크, 여: 초록)
# -----------------------------------------------------------------------------
if menu == "1. 행정구별 연령대 인구 (꺾은선)":
    st.subheader("📊 행정구 및 성별 연령대별 인구수 꺾은선 그래프")
    
    st.sidebar.markdown("---")
    selected_region = st.sidebar.selectbox("조회할 행정구 선택", df['행정기관'].unique().tolist(), key="menu1_region_selectbox")
    selected_year = st.sidebar.radio("조회할 연도 선택", ["2024년", "2025년"], key="menu1_year_radio")
    
    region_row = df[df['행정기관'] == selected_region].iloc[0]
    
    male_vals = [region_row[f"{selected_year}_남_{age}"] for age in age_bins]
    female_vals = [region_row[f"{selected_year}_여_{age}"] for age in age_bins]
    
    fig, ax = plt.subplots(figsize=(11, 6))
    
    # 남성: 핑크색 (#FF69B4), 여성: 초록색 (#2ECC71)
    ax.plot(age_bins, male_vals, marker='o', color='#FF69B4', linewidth=2.5, markersize=7, label='남성')
    ax.plot(age_bins, female_vals, marker='s', color='#2ECC71', linewidth=2.5, markersize=7, label='여성')
    
    ax.set_title(f"[{selected_region}] {selected_year} 성별 연령대별 인구 분포", fontsize=14, pad=15)
    ax.set_xlabel("나이 (연령대)", fontsize=12, labelpad=10)
    ax.set_ylabel("인구수 (명)", fontsize=12, labelpad=10)
    
    ax.set_xticks(range(len(age_bins)))
    ax.set_xticklabels(age_bins, rotation=30)
    
    all_vals = male_vals + female_vals
    max_pop = max(all_vals) if all_vals else 100000
    y_max_limit = max(100000, (int(max_pop // 100000) + 2) * 100000)
    ax.set_yticks(range(0, y_max_limit, 100000))
    
    ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    ax.grid(True, linestyle='--', alpha=0.6, color='gray')
    ax.legend()
    
    st.pyplot(fig)
    
    with st.expander("📊 상세 수치 표로 보기"):
        summary_df = pd.DataFrame({"연령대": age_bins, "남성 인구수": male_vals, "여성 인구수": female_vals})
        st.dataframe(summary_df)

# -----------------------------------------------------------------------------
# [기능 2] 특정 연령대에서 인구가 가장 많은 행정구 막대 그래프
# -----------------------------------------------------------------------------
elif menu == "2. 연령대별 최다 인구 행정구 (막대)":
    st.subheader("📊 연령대별 자치구 인구 비교 및 순위 (막대 그래프)")
    
    st.sidebar.markdown("---")
    selected_age = st.sidebar.selectbox("분석할 연령대 선택", age_bins, key="menu2_age_selectbox")
    selected_gender_lbl = st.sidebar.radio("성별 구분", ["계(전체)", "남성", "여성"], key="menu2_gender_radio")
    selected_year = st.sidebar.radio("기준 연도 선택", ["2024년", "2025년"], key="menu2_year_radio")
    
    gender_code = "계" if "계" in selected_gender_lbl else ("남" if "남성" in selected_gender_lbl else "여")
    
    sub_df = df[df['행정기관'] != '대전광역시'].copy()
    col_name = f"{selected_year}_{gender_code}_{selected_age}"
    
    regions = sub_df['행정기관'].tolist()
    populations = sub_df[col_name].tolist()
    
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(regions, populations, color='#3498DB', width=0.5)
    
    if populations:
        max_idx = populations.index(max(populations))
        bars[max_idx].set_color('#E74C3C') # 최다 인구 지역은 빨간색 강조
        
    ax.set_title(f"[{selected_year}] {selected_age} ({selected_gender_lbl}) 자치구별 인구 현황", fontsize=14, pad=15)
    ax.set_xlabel("행정구", fontsize=12, labelpad=10)
    ax.set_ylabel("인구수 (명)", fontsize=12, labelpad=10)
    
    ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    ax.grid(axis='y', linestyle='--', alpha=0.6, color='gray')
    
    st.pyplot(fig)
    
    top_region = regions[populations.index(max(populations))] if populations else ""
    st.success(f"🏆 **{selected_age}** ({selected_gender_lbl}) 기준 인구가 가장 많은 행정구는 **{top_region}**입니다!")

# -----------------------------------------------------------------------------
# [기능 3] 연도별 인구 증감 비교
# -----------------------------------------------------------------------------
elif menu == "3. 연도별 인구 증감 비교":
    st.subheader("📈 2024년 대비 2025년 행정구별 총인구 증감 비교")
    
    sub_df = df[df['행정기관'] != '대전광역시'].copy()
    
    regions = sub_df['행정기관'].tolist()
    pop_2024
