import streamlit as st
import requests
from bs4 import BeautifulSoup

st.title("🚑 긴급 진단 키트")
st.write("어디가 고장 났는지 확인해 봅시다.")

# 1. 입력 받기
token = st.text_input("텔레그램 토큰", type="password")
chat_id = st.text_input("채팅 ID")
keyword = st.text_input("테스트 키워드", value="뉴스")
url = "https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1=105&sid2=230"

if st.button("진단 시작 (눌러보세요)"):
    st.divider()
    
    # --- 테스트 1: 텔레그램 연결 ---
    st.subheader("1. 텔레그램 연결 테스트")
    send_url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {"chat_id": chat_id, "text": "🔔 [테스트] 이 메시지가 보이면 성공!"}
    
    try:
        res = requests.get(send_url, params=params)
        result = res.json()
        
        if res.status_code == 200:
            st.success(f"✅ 성공! 텔레그램 메시지를 확인하세요.")
        else:
            st.error(f"❌ 실패! (토큰이나 ID가 틀렸습니다)")
            st.code(f"에러 내용: {result}", language="json")
            st.info("팁: 토큰 앞에 빈칸이 있거나, ID가 숫자가 아닌지 확인하세요.")
            
    except Exception as e:
        st.error(f"❌ 통신 에러: {e}")

    # --- 테스트 2: 사이트 크롤링 ---
    st.subheader("2. 사이트 접속 테스트")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers)
        
        if res.status_code == 200:
            st.success(f"✅ 사이트 접속 성공! (상태코드: 200)")
            
            soup = BeautifulSoup(res.text, 'html.parser')
            articles = soup.select("dt > a")
            
            found = False
            st.write(f"🔍 '{keyword}' 단어를 찾는 중...")
            
            # 검색 결과 미리보기
            count = 0
            for article in articles:
                title = article.text.strip()
                if keyword in title:
                    st.write(f"- 발견: {title}")
                    found = True
                    count += 1
            
            if found:
                st.success(f"✅ 총 {count}개의 글을 찾았습니다! 크롤링 기능은 정상입니다.")
            else:
                st.warning(f"⚠️ 사이트 접속은 됐는데 '{keyword}' 단어가 제목에 없습니다.")
                st.write("현재 페이지의 제목들(일부):")
                for i, article in enumerate(articles[:3]):
                    st.caption(f"{i+1}. {article.text.strip()}")
        else:
            st.error("❌ 사이트 접속 차단됨 (봇으로 의심받음)")
            
    except Exception as e:
        st.error(f"❌ 크롤링 에러: {e}")
