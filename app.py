import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import threading
import xml.etree.ElementTree as ET
import random

# ---------------------------------------------------------
# [기본 설정] 페이지 제목
# ---------------------------------------------------------
st.set_page_config(page_title="황금알 자동 봇", page_icon="🪿")

# ---------------------------------------------------------
# [기능 1] 키워드 수집 (무엇을 찾을까?)
# ---------------------------------------------------------
def get_google_trends():
    """구글 트렌드: 이슈 키워드 10개"""
    url = "https://trends.google.co.kr/trends/trendingsearches/daily/rss?geo=KR"
    try:
        response = requests.get(url)
        root = ET.fromstring(response.content)
        return [item.find('title').text for item in root.findall('.//item')][:10]
    except:
        return ["특가", "오류", "대란"]

def get_naver_shopping_best():
    """네이버 쇼핑: 잘 팔리는 디지털 기기 10개"""
    # 디지털/가전 카테고리 랭킹
    url = "https://search.shopping.naver.com/best/category/click?categoryCategoryId=50000003&viewType=list&sort=popular"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 상품명 태그 찾기 (네이버 구조 변경 대비)
        items = soup.find_all('div', class_=lambda x: x and 'imageTitle_title' in x)
        
        keywords = []
        for item in items:
            # 너무 긴 이름은 앞 2단어만 (예: 삼성전자 갤럭시북4... -> 삼성전자 갤럭시북4)
            short_name = " ".join(item.text.split()[:2])
            keywords.append(short_name)
        return list(set(keywords))[:10]
    except:
        return ["아이폰", "갤럭시", "노트북"]

# ---------------------------------------------------------
# [기능 2] 봇 엔진 (찾고 알림 보내기)
# ---------------------------------------------------------
def send_telegram(token, chat_id, msg):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.get(url, params={"chat_id": chat_id, "text": msg})
    except:
        pass

def bot_engine(token, chat_id, target_url, mode, manual_kws, log_area):
    if 'sent_list' not in st.session_state:
        st.session_state['sent_list'] = []

    while st.session_state['is_running']:
        try:
            # 1. 키워드 선정
            if mode == "네이버 쇼핑 랭킹 (수익)":
                keywords = get_naver_shopping_best()
                icon = "🛍️"
            elif mode == "구글 트렌드 (이슈)":
                keywords = get_google_trends()
                icon = "🌊"
            else:
                keywords = manual_kws
                icon = "✍️"

            # 2. 로그 표시
            kws_text = ", ".join(keywords[:3])
            log_area.info(f"[{time.strftime('%H:%M:%S')}] {icon} 감시 중: {kws_text} 등 {len(keywords)}개")

            # 3. 사이트 뒤지기
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(target_url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # (중요) 사이트마다 제목 태그가 다름. 기본은 네이버 뉴스/게시판
            articles = soup.select("dt > a") 
            if not articles: articles = soup.select("a") # 태그 못 찾으면 모든 링크 검사

            for article in articles:
                title = article.text.strip()
                link = article.get('href')

                # 키워드가 제목에 있는지 검사
                for kw in keywords:
                    if kw in title and title not in st.session_state['sent_list']:
                        # 찾았다!
                        msg = f"🔥 [심봤다! {kw}]\n제목: {title}\n링크: {link}"
                        send_telegram(token, chat_id, msg)
                        st.session_state['sent_list'].append(title)

            # 4. 휴식 (1분 + 랜덤)
            time.sleep(60 + random.randint(1, 10))

        except Exception as e:
            log_area.error(f"에러 발생: {e}")
            time.sleep(60)

# ---------------------------------------------------------
# [화면] UI 구성
# ---------------------------------------------------------
st.title("🪿 황금알 자동 봇")
st.markdown("왼쪽 화살표(>)를 눌러 설정을 입력하고 시작하세요.")

# 사이드바 (설정 입력)
with st.sidebar:
    st.header("⚙️ 설정 입력")
    # 비밀번호처럼 가려지게 처리
    u_token = st.text_input("텔레그램 토큰", type="password")
    u_id = st.text_input("채팅 ID")
    u_url = st.text_input("감시할 URL", value="https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1=105&sid2=230")
    st.caption("팁: '뽐뿌'나 '딜바다' URL을 넣으면 더 좋습니다.")

# 메인 화면
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🎯 사냥감 선택")
    mode = st.radio("모드 선택", ["네이버 쇼핑 랭킹 (수익)", "구글 트렌드 (이슈)", "수동 입력"])
    
    manual_kws = []
    if mode == "수동 입력":
        txt = st.text_area("키워드 (쉼표로 구분)", "특가, 오류, 대란")
        manual_kws = txt.split(",")

with col2:
    st.subheader("🚀 제어")
    if 'is_running' not in st.session_state:
        st.session_state['is_running'] = False
        
    if st.button("시작", type="primary", use_container_width=True):
        if not u_token or not u_id:
            st.error("설정을 먼저 입력하세요!")
        elif not st.session_state['is_running']:
            st.session_state['is_running'] = True
            st.toast("봇이 출발했습니다!")
            # 백그라운드 실행
            t = threading.Thread(target=bot_engine, args=(u_token, u_id, u_url, mode, manual_kws, st.empty()))
            t.start()
            
    if st.button("중지", use_container_width=True):
        st.session_state['is_running'] = False
        st.info("중지 신호를 보냈습니다.")

st.divider()
st.caption("실시간 로그")
# 로그가 출력될 빈 공간
st.empty()
