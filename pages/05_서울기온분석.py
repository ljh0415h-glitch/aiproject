import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 한글 폰트 강제 적용 (글자 깨짐 방지)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="월별 기온 분석 대시보드", layout="wide")

def setup_korean_font():
    """Linux(Streamlit Cloud) 및 로컬 환경에서 한글 폰트를 설정합니다."""
    nanum_font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
    
    if os.path.exists(nanum_font_path):
        fm.fontManager.addfont(nanum_font_path)
        font_prop = fm.FontProperties(fname=nanum_font_path)
        plt.rcParams['font.family'] = font_prop.get_name()
    else:
        import platform
        sys_name = platform.system()
        if sys_name == 'Windows':
            plt.rcParams['font.family'] = 'Malgun Gothic'
        elif sys_name == 'Darwin':
            plt.rcParams['font.family'] = 'AppleGothic'
            
    plt.rcParams['axes.unicode_minus'] = False

setup_korean_font()

# -----------------------------------------------------------------------------
# 2. 데이터 로드 및 전처리
# -----------------------------------------------------------------------------
@st.cache_data
def load_temperature_data():
    # 상위 폴더 및 현재 폴더 경로 탐색
    file_path = os.path.join(os.path.dirname(__file__), '..', 'temperature.csv')
    if not os.path.exists(file_path):
        file_path = 'temperature.csv'
        
    if not os.path.exists(file_path):
        st.error("'temperature.csv' 파일을 찾을 수 없습니다. 상위 폴더에 파일을 업로드해 주세요.")
        st.stop()
        
    # cp949 인코딩으로 한글 깨짐 방지
    df = pd.read_csv(file_path, encoding='cp949')
    
    # '일시' 컬럼(예: 'Oct-07')에서 월(Month)과 연도(Year) 추출
    def parse_date(val):
        try:
            parts = str(val).strip().split('-')
            if len(parts) == 2:
                return parts[0], parts[1]
        except:
            pass
        return None, None

    df['Month'], df['Year'] = zip(*df['일시'].apply(parse_date))
    return df

df = load_temperature_data()

# -----------------------------------------------------------------------------
# 3. 사이드바 월(Month) 선택 UI
# -----------------------------------------------------------------------------
st.title("🌡️ 월별 최고·최저 기온 분석 대시보드")
st.markdown("사용자가 선택한 월에 따른 연도별 최고 기온 및 최저 기온 변화를 꺾은선 그래프로 시각화합니다.")

st.sidebar.header("🔍 조회 조건 설정")

# 월 영문 매핑 (사용자 편의용 한글 라벨 제공)
month_map = {
    "1월 (Jan)": "Jan", "2월 (Feb)": "Feb", "3월 (Mar)": "Mar", 
    "4월 (Apr)": "Apr", "5월 (May)": "May", "6월 (Jun)": "Jun", 
    "7월 (Jul)": "Jul", "8월 (Aug)": "Aug", "9월 (Sep)": "Sep", 
    "10월 (Oct)": "Oct", "11월 (Nov)": "Nov", "12월 (Dec)": "Dec"
}

selected_month_label = st.sidebar.selectbox("분석할 월 선택", list(month_map.keys()), key="temp_month_select")
selected_month_code = month_map[selected_month_label]

# -----------------------------------------------------------------------------
# 4. 데이터 필터링 및 그래프 시각화
# -----------------------------------------------------------------------------
# 선택한 월에 해당하는 데이터만 필터링
filtered_df = df[df['Month'] == selected_month_code].copy()

if filtered_df.empty:
    st.warning("선택한 월에 해당하는 데이터가 없습니다.")
else:
    years = filtered_df['Year'].tolist()
    
    # 최고기온 및 최저기온 데이터 추출 (컬럼명 주의: 최고기온(℃), 최저기온(℃))
    max_temps = filtered_df['최고기온(℃)'].tolist()
    min_temps = filtered_df['최저기온(℃)'].tolist()

    # 그래프 생성
    fig, ax = plt.subplots(figsize=(11, 6))

    # 3. 최고기온: 핫핑크 (#FF69B4), 최저기온: 하늘색 (#87CEEB)
    ax.plot(years, max_temps, marker='o', color='#FF69B4', linewidth=2.5, label='최고기온')
    ax.plot(years, min_temps, marker='s', color='#87CEEB', linewidth=2.5, label='최저기온')

    # 4. 그래프 제목 및 범례 표시
    ax.set_title(f"[{selected_month_label}] 연도별 기온 분석", fontsize=15, pad=15)
    ax.legend(loc='upper left', fontsize=12)

    # 5. 가로축(X축): 연도, 세로축(Y축): 온도
    ax.set_xlabel("연도", fontsize=12, labelpad=10)
    ax.set_ylabel("온도 (℃)", fontsize=12, labelpad=10)

    # X축 연도가 많을 경우 겹치지 않게 간격 조절 또는 회전
    plt.xticks(rotation=45)
    
    ax.grid(True, linestyle='--', alpha=0.6, color='gray')

    # 스트림릿에 그래프 출력
    st.pyplot(fig)

    # 📊 하단 데이터 상세 테이블 제공
    with st.expander(f"📋 {selected_month_label} 상세 기온 데이터 보기"):
        display_df = filtered_df[['일시', '평균기온(℃)', '최고기온(℃)', '최저기온(℃)']].copy()
        display_df.columns = ['일시', '평균기온 (℃)', '최고기온 (℃)', '최저기온 (℃)']
        st.dataframe(display_df.reset_index(drop=True), use_container_width=True)
