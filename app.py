import streamlit as st
from elasticsearch import Elasticsearch
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from kafka import KafkaProducer
import json
import time

# --- 1. 초기 연결 설정 ---
# Elasticsearch 연결 (버전 8 호환성 헤더 포함)
es = Elasticsearch(
    "http://localhost:9200",
    headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=8"}
)

# Kafka Producer 설정 (설문 제출용)
def get_kafka_producer():
    try:
        return KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    except Exception as e:
        st.error(f"Kafka 연결 실패: {e}")
        return None

# --- 2. 기본 환경 설정 ---
plt.rcParams['font.family'] = 'Malgun Gothic' # 윈도우 한글 폰트
plt.rcParams['axes.unicode_minus'] = False
st.set_page_config(page_title="셔틀버스 관제 시스템", layout="wide")

# --- 3. 로그인 세션 관리 ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.is_admin = False
    st.session_state.user_id = ""

# --- 4. 로그인 화면 ---
if not st.session_state.logged_in:
    st.title("🚌 셔틀버스 실시간 분석 시스템 로그인")
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            uid = st.text_input("학번(8자리) 또는 관리자 ID")
            upw = st.text_input("비밀번호", type="password")
            if st.form_submit_button("시스템 접속"):
                if uid == "admin" and upw == "1234":
                    st.session_state.logged_in = True
                    st.session_state.is_admin = True
                    st.rerun()
                elif len(uid) == 8 and uid.isdigit():
                    st.session_state.logged_in = True
                    st.session_state.is_admin = False
                    st.session_state.user_id = uid
                    st.rerun()
                else:
                    st.error("입력 정보를 확인하세요. (학생: 학번 8자리, 관리자: 전용 계정)")
    st.stop()

# --- 5. 데이터 로드 함수 ---
def load_es_data():
    try:
        res = es.search(index="shuttle_survey", size=5000)
        hits = res['hits']['hits']
        if not hits: return pd.DataFrame()
        return pd.DataFrame([hit['_source'] for hit in hits])
    except:
        return pd.DataFrame()

df = load_es_data()

# --- 6. 사이드바 및 권한별 메뉴 분리 ---
st.sidebar.title(f"👤 {st.session_state.user_id if not st.session_state.is_admin else 'Admin'}님")
if st.sidebar.button("로그아웃"):
    st.session_state.logged_in = False
    st.rerun()

# 권한에 따른 메뉴 구성
if st.session_state.is_admin:
    menu = st.sidebar.radio("메뉴 이동", ["📊 실시간 분석 대시보드", "📋 원본 데이터 로그"])
else:
    menu = st.sidebar.radio("메뉴 이동", ["📝 셔틀 개선 설문조사", "📊 실시간 분석 대시보드"])

# --- [기능 1] 📝 학생 전용: 설문조사 참여 (Kafka Producer) ---
if menu == "📝 셔틀 개선 설문조사":
    st.title("📝 셔틀버스 개선 설문조사")
    st.info("귀하의 응답은 Kafka를 통해 실시간으로 분석 서버에 전달됩니다.")
    
    with st.form("survey_form"):
        st.subheader("기본 정보 및 만족도")
        transport = st.selectbox("현재 주 이용 수단", ["지하철", "시내버스", "셔틀버스", "도보", "택시"])
        stop = st.selectbox("가장 자주 이용하는 역", ["길음역", "시청역", "잠실역", "신촌역", "불광역", "광화문역", "해당없음"])
        score = st.slider("현재 셔틀 서비스 만족도 (1-5)", 1, 5, 3)
        
        st.subheader("상세 의견")
        complaint = st.multiselect("불편 사항", ["실시간 위치 확인 불가", "외부인 탑승", "배차 불규칙", "불친절", "조기 출발"])
        wish = st.text_input("신설 희망 노선명")
        feedback = st.text_area("구체적인 건의사항")
        
        if st.form_submit_button("설문 제출"):
            payload = {
                "학번": st.session_state.user_id,
                "현재수단": transport,
                "현재탑승역": stop,
                "만족도": score,
                "불편사항": ", ".join(complaint) if complaint else "없음",
                "희망노선": wish if wish else "없음",
                "상세의견": feedback if feedback else "없음",
                "timestamp": time.time()
            }
            
            # Kafka로 데이터 전송
            producer = get_kafka_producer()
            if producer:
                producer.send('shuttle-topic', payload)
                st.success("✅ 제출 완료! Kafka를 통해 분석 엔진으로 데이터가 전송되었습니다.")
                st.balloons()

# --- [기능 2] 📊 공통: 실시간 분석 대시보드 ---
elif menu == "📊 실시간 분석 대시보드":
    st.title("📈 실시간 데이터 분석 대시보드")
    
    if df.empty:
        st.warning("분석할 데이터가 아직 없습니다.")
    else:
        # 상단 핵심 지표
        m1, m2, m3 = st.columns(3)
        m1.metric("총 응답 수", f"{len(df)}명")
        m2.metric("평균 만족도", f"{df['만족도'].mean():.2f}/5.0")
        m3.metric("셔틀 이용 비중", f"{(df['현재수단']=='셔틀버스').mean()*100:.1f}%")

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📍 정류장별 이용 분포")
            st.bar_chart(df['현재탑승역'].value_counts())
        
        with col2:
            st.subheader("🚨 주요 불편 유형")
            con_data = df['불편사항'].str.split(', ').explode().value_counts()
            fig, ax = plt.subplots()
            ax.pie(con_data, labels=con_data.index, autopct='%1.1f%%', startangle=90)
            st.pyplot(fig)

        st.divider()
        
        st.subheader("💭 실시간 의견 워드클라우드")
        text = " ".join(df['상세의견'].dropna().astype(str))
        if len(text) > 5:
            sw = set(['때문에', '정말', '진짜', '너무', '있음', '수', '하는'])
            wc = WordCloud(font_path='malgun.ttf', background_color='white', stopwords=sw, width=1000, height=400).generate(text)
            fig_wc, ax_wc = plt.subplots(figsize=(12, 5))
            ax_wc.imshow(wc, interpolation='bilinear')
            ax_wc.axis("off")
            st.pyplot(fig_wc)

# --- [기능 3] 📋 관리자 전용: 원본 데이터 로그 ---
elif menu == "📋 원본 데이터 로그":
    st.title("🕵️ 관리자 데이터 모니터링")
    st.subheader("Elasticsearch 원본 저장소 로그")
    
    # 데이터 검색 및 필터링 기능
    search_q = st.text_input("학번 또는 키워드 검색")
    if search_q:
        filtered_df = df[df.apply(lambda row: row.astype(str).str.contains(search_q).any(), axis=1)]
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

    if st.button("CSV 파일로 추출"):
        df.to_csv("shuttle_report.csv", index=False, encoding='utf-8-sig')
        st.success("shuttle_report.csv 파일이 생성되었습니다.")