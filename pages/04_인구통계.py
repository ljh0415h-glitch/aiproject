import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# -----------------------------------------------------------------------------
# 1. 페이지 및 한글 폰트 설정 (Streamlit Cloud 환경 대응)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="대전광역시 인구 구조 분석", layout="wide")

@st.cache_resource
def init_korean_font():
    """Streamlit Cloud(Linux) 및 로컬 환경에서 한글 폰트를 설정합니다."""
    nanum_font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
    
    if os.path.exists(nanum_font_path):
        font_prop = fm.FontProperties(fname=nanum_font_path)
        plt.rc('font', family=font_prop.get_name())
    else:
        # Windows / Mac 로컬 테스트용 기본 폰트 설정
        import platform
        if platform.system() == 'Windows':
            plt.rc('font', family='Malgun Gothic')
        elif platform.system() == 'Darwin':
            plt.rc('font', family='AppleGothic')
            
    plt.rc('axes', unicode_minus=False)

init_korean_font()

# -----------------------------------------------------------------------------
# 2. 데이터 로드 및 전처리 (상위 폴더 참조 경로 적용)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # 현재 파일은 pages/ 안에 있으므로, 상위 폴더의 데이터 파일 경로 지정
    # 엑셀 파일인 경우:
    file_path_xlsx = os.path.join(os.path.dirname(__file__), '..', 'population.xlsx')
    # CSV 파일인 경우 (사용하시는 확장자에 맞춰 자동 대응):
    file_path_csv = os.path.join(os.path.dirname(__file__), '..', 'population.csv')
    
    if os.path.exists(file_path_xlsx):
        df_raw = pd.read_excel(file_path_xlsx)
    elif os.path.exists(file_path_csv):
        df_raw = pd.read_csv(file_path_csv, encoding='utf-8-sig')
    else:
        # 파일이 없을 경우 현재 디렉토리 기준 탐색 시도
        if os.path.exists('population.xlsx'):
            df_raw = pd.read_excel('population.xlsx')
        elif os.path.exists('population.csv'):
            df_raw = pd.read_csv('population.csv', encoding='utf-8-sig')
        else:
            st.error("상위 폴더 또는 현재 폴더에 'population.xlsx' 또는 'population.csv' 파일이 존재하지 않습니다.")
            st.stop()
            
    # 상단 3개 행 전처리 (연도, 성별, 구분)
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
    
    # 수치형 변환
    for col in df.columns:
        if col not in ['행정기관코드', '행정기관']:
            df[col] = df[col].astype(str).str.replace(',', '').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    df['행정기관'] = df['행정기관'].astype(str).str.strip()
    return df

df = load_data()

# -----------------------------------------------------------------------------
# 3. 사이드바 조건 선택 (행정구, 성별, 연도)
# -----------------------------------------------------------------------------
st.title("📈 대전광역시 연령별 인구수 분석")

st.sidebar.header("⚙️ 분석 조건 선택")

# 행정구 선택
region_list = df['행정기관'].unique().tolist()
selected_region = st.sidebar.selectbox("행정구 선택", region_list)

# 성별 선택
gender_map = {"전체(계)": "계", "남성": "남", "여성": "여"}
selected_gender_label = st.sidebar.radio("성별 선택", list(gender_map.keys()))
selected_gender = gender_map[selected_gender_label]

# 연도 선택
selected_year = st.sidebar.radio("연도 선택", ["2024년", "2025년"])

# -----------------------------------------------------------------------------
# 4. 선택 조건 데이터 추출
# -----------------------------------------------------------------------------
age_bins = ['0~9세', '10~19세', '20~29세', '30~39세', '40~49세', 
            '50~59세', '60~69세', '70~79세', '80~89세', '90~99세', '100세 이상']

region_row = df[df['행정기관'] == selected_region].iloc[0]

population_values = []
for age in age_bins:
    col_name = f"{selected_year}_{selected_gender}_{age}"
    if col_name in region_row:
        population_values.append(region_row[col_name])
    else:
        population_values.append(0)

# -----------------------------------------------------------------------------
# 5. 핫핑크 꺾은선 그래프 시각화 (눈금 및 격자 설정)
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 6))

# 핫핑크 (#FF69B4) 꺾은선 그래프 그리기
ax.plot(age_bins, population_values, marker='o', color='#FF69B4', linewidth=2.5, markersize=7)

# 타이틀 및 축 레이블 설정
ax.set_title(f"[{selected_region}] {selected_year} {selected_gender_label} 연령대별 인구 수", fontsize=15, pad=15)
ax.set_xlabel("나이 (연령대)", fontsize=12, labelpad=10)
ax.set_ylabel("인구수 (명)", fontsize=12, labelpad=10)

# 가로축(X축) 10살 단위 눈금 설정
ax.set_xticks(range(len(age_bins)))
ax.set_xticklabels(age_bins, rotation=30)

# 세로축(Y축) 10만 단위 구분선 설정
max_pop = max(population_values) if population_values else 100000
y_max_limit = max(100000, (int(max_pop // 100000) + 2) * 100000)
ax.set_yticks(range(0, y_max_limit, 100000))

# Y축 숫자 10만 단위(쉼표 표기) 지정 및 눈금 구분선(Grid) 추가
ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
ax.grid(True, linestyle='--', alpha=0.6, color='gray')

# 그래프 출력
st.pyplot(fig)

# 하단 데이터 요약 표
with st.expander("📊 선택된 데이터 수치 확인하기"):
    summary_df = pd.DataFrame({"연령대": age_bins, "인구수": population_values})
    summary_df["인구수"] = summary_df["인구수"].apply(lambda x: f"{int(x):,} 명")
    st.dataframe(summary_df.T)
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
    # Linux 서버(Streamlit Cloud) 경로
    nanum_font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
    
    if os.path.exists(nanum_font_path):
        font_prop = fm.FontProperties(fname=nanum_font_path)
        font_name = font_prop.get_name()
        plt.rc('font', family=font_name)
    else:
        # 로컬 환경 (Windows / Mac)
        import platform
        sys_name = platform.system()
        if sys_name == 'Windows':
            plt.rc('font', family='Malgun Gothic')
        elif sys_name == 'Darwin':
            plt.rc('font', family='AppleGothic')
            
    # 마이너스 기호 깨짐 방지
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
# 3. 사이드바 조건 선택
# -----------------------------------------------------------------------------
st.title("📈 대전광역시 연령별 인구수 분석")

st.sidebar.header("⚙️ 분석 조건 선택")

region_list = df['행정기관'].unique().tolist()
selected_region = st.sidebar.selectbox("행정구 선택", region_list)

gender_map = {"전체(계)": "계", "남성": "남", "여성": "여"}
selected_gender_label = st.sidebar.radio("성별 선택", list(gender_map.keys()))
selected_gender = gender_map[selected_gender_label]

selected_year = st.sidebar.radio("연도 선택", ["2024년", "2025년"])

# -----------------------------------------------------------------------------
# 4. 데이터 추출
# -----------------------------------------------------------------------------
age_bins = ['0~9세', '10~19세', '20~29세', '30~39세', '40~49세', 
            '50~59세', '60~69세', '70~79세', '80~89세', '90~99세', '100세 이상']

region_row = df[df['행정기관'] == selected_region].iloc[0]

population_values = []
for age in age_bins:
    col_name = f"{selected_year}_{selected_gender}_{age}"
    if col_name in region_row:
        population_values.append(region_row[col_name])
    else:
        population_values.append(0)

# -----------------------------------------------------------------------------
# 5. 핫핑크 꺾은선 그래프 시각화 (폰트 직접 적용)
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 6))

# 핫핑크 (#FF69B4) 꺾은선 그래프
ax.plot(age_bins, population_values, marker='o', color='#FF69B4', linewidth=2.5, markersize=7)

# 폰트 객체 직접 지정 (그래프 내 글자 깨짐 완전 방지)
nanum_font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
if os.path.exists(nanum_font_path):
    label_font = fm.FontProperties(fname=nanum_font_path, size=12)
    title_font = fm.FontProperties(fname=nanum_font_path, size=15)
else:
    label_font = None
    title_font = None

ax.set_title(f"[{selected_region}] {selected_year} {selected_gender_label} 연령대별 인구 수", fontproperties=title_font, pad=15)
ax.set_xlabel("나이 (연령대)", fontproperties=label_font, labelpad=10)
ax.set_ylabel("인구수 (명)", fontproperties=label_font, labelpad=10)

ax.set_xticks(range(len(age_bins)))
ax.set_xticklabels(age_bins, rotation=30)

max_pop = max(population_values) if population_values else 100000
y_max_limit = max(100000, (int(max_pop // 100000) + 2) * 100000)
ax.set_yticks(range(0, y_max_limit, 100000))

ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
ax.grid(True, linestyle='--', alpha=0.6, color='gray')

st.pyplot(fig)

with st.expander("📊 선택된 데이터 수치 확인하기"):
    summary_df = pd.DataFrame({"연령대": age_bins, "인구수": population_values})
    summary_df["인구수"] = summary_df["인구수"].apply(lambda x: f"{int(x):,} 명")
    st.dataframe(summary_df.T)
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
# 3. 사이드바 조건 선택 (고유 key 추가로 중복 에러 방지)
# -----------------------------------------------------------------------------
st.title("📈 대전광역시 연령별 인구수 분석")

st.sidebar.header("⚙️ 분석 조건 선택")

region_list = df['행정기관'].unique().tolist()
selected_region = st.sidebar.selectbox("행정구 선택", region_list, key="pop_region_select")

gender_map = {"전체(계)": "계", "남성": "남", "여성": "여"}
selected_gender_label = st.sidebar.radio("성별 선택", list(gender_map.keys()), key="pop_gender_radio")
selected_gender = gender_map[selected_gender_label]

selected_year = st.sidebar.radio("연도 선택", ["2024년", "2025년"], key="pop_year_radio")

# -----------------------------------------------------------------------------
# 4. 데이터 추출
# -----------------------------------------------------------------------------
age_bins = ['0~9세', '10~19세', '20~29세', '30~39세', '40~49세', 
            '50~59세', '60~69세', '70~79세', '80~89세', '90~99세', '100세 이상']

region_row = df[df['행정기관'] == selected_region].iloc[0]

population_values = []
for age in age_bins:
    col_name = f"{selected_year}_{selected_gender}_{age}"
    if col_name in region_row:
        population_values.append(region_row[col_name])
    else:
        population_values.append(0)

# -----------------------------------------------------------------------------
# 5. 핫핑크 꺾은선 그래프 시각화 (폰트 직접 적용)
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 6))

# 핫핑크 (#FF69B4) 꺾은선 그래프
ax.plot(age_bins, population_values, marker='o', color='#FF69B4', linewidth=2.5, markersize=7)

# 폰트 객체 직접 지정 (그래프 내 글자 깨짐 완전 방지)
nanum_font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
if os.path.exists(nanum_font_path):
    label_font = fm.FontProperties(fname=nanum_font_path, size=12)
    title_font = fm.FontProperties(fname=nanum_font_path, size=15)
else:
    label_font = None
    title_font = None

ax.set_title(f"[{selected_region}] {selected_year} {selected_gender_label} 연령대별 인구 수", fontproperties=title_font, pad=15)
ax.set_xlabel("나이 (연령대)", fontproperties=label_font, labelpad=10)
ax.set_ylabel("인구수 (명)", fontproperties=label_font, labelpad=10)

ax.set_xticks(range(len(age_bins)))
ax.set_xticklabels(age_bins, rotation=30)

max_pop = max(population_values) if population_values else 100000
y_max_limit = max(100000, (int(max_pop // 100000) + 2) * 100000)
ax.set_yticks(range(0, y_max_limit, 100000))

ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
ax.grid(True, linestyle='--', alpha=0.6, color='gray')

st.pyplot(fig)

with st.expander("📊 선택된 데이터 수치 확인하기"):
    summary_df = pd.DataFrame({"연령대": age_bins, "인구수": population_values})
    summary_df["인구수"] = summary_df["인구수"].apply(lambda x: f"{int(x):,} 명")
    st.dataframe(summary_df.T)
