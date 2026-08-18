import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import base64
import os

# ==========================================
# 🔑 API 키 설정 (클라우드 배포용 안전 처리)
# ==========================================
try:
    KAKAO_API_KEY = st.secrets["KAKAO_API_KEY"]
    TMAP_APP_KEY = st.secrets["TMAP_APP_KEY"]
except:
    KAKAO_API_KEY = "96fc63ab0efc0a7d8591eeb8b34db8a9"
    TMAP_APP_KEY = "kstcD6L0he3GU4SSTkWNF6IHGefkURVXak3qpabh"


# ==========================================

# --- 카카오 API 통신 ---
def get_kakao_coords(address):
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}

    keyword_url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    res_keyword = requests.get(keyword_url, headers=headers, params={"query": address})
    data_keyword = res_keyword.json()

    if data_keyword.get('documents'):
        return data_keyword['documents'][0]['x'], data_keyword['documents'][0]['y']

    addr_url = "https://dapi.kakao.com/v2/local/search/address.json"
    res_addr = requests.get(addr_url, headers=headers, params={"query": address})
    data_addr = res_addr.json()

    if data_addr.get('documents'):
        return data_addr['documents'][0]['x'], data_addr['documents'][0]['y']

    return None, None


def get_kakao_route(start_x, start_y, end_x, end_y):
    url = "https://apis-navi.kakaomobility.com/v1/directions"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"origin": f"{start_x},{start_y}", "destination": f"{end_x},{end_y}", "priority": "RECOMMEND"}
    res = requests.get(url, headers=headers, params=params)
    data = res.json()

    if data.get('routes'):
        route = data['routes'][0]
        summary = route['summary']
        distance_km = round(summary['distance'] / 1000, 1)
        duration_min = round(summary['duration'] / 60)

        path_coords = []
        for section in route.get('sections', []):
            for road in section.get('roads', []):
                vertexes = road.get('vertexes', [])
                for i in range(0, len(vertexes), 2):
                    path_coords.append([vertexes[i + 1], vertexes[i]])

        guides = [g.get('guidance') for s in route.get('sections', []) for g in s.get('guides', []) if
                  g.get('guidance')]
        return distance_km, duration_min, path_coords, guides
    return None, None, [], []


# --- 티맵 API 통신 ---
def get_tmap_route(start_x, start_y, end_x, end_y):
    url = "https://apis.openapi.sk.com/tmap/routes?version=1&format=json"
    headers = {
        "appKey": TMAP_APP_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "startX": str(start_x),
        "startY": str(start_y),
        "endX": str(end_x),
        "endY": str(end_y),
        "startName": "출발지",
        "endName": "도착지",
        "reqCoordType": "WGS84GEO",
        "resCoordType": "WGS84GEO",
        "searchOption": "0"
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()

        if 'features' in data:
            prop = data['features'][0]['properties']
            distance_km = round(prop['totalDistance'] / 1000, 1)
            duration_min = round(prop['totalTime'] / 60)

            path_coords = []
            guides = []

            for feature in data['features']:
                geom = feature.get('geometry', {})
                p = feature.get('properties', {})

                if geom.get('type') == 'LineString':
                    for coord in geom.get('coordinates', []):
                        path_coords.append([coord[1], coord[0]])

                if geom.get('type') == 'Point' and 'description' in p:
                    guides.append(p['description'])

            return distance_km, duration_min, path_coords, guides
        else:
            return None, None, [], []

    except Exception as e:
        print(f"🔴 티맵 통신 실패: {e}")
        return None, None, [], []


def format_time(duration_min):
    if duration_min is None: return "오류"
    hours, mins = duration_min // 60, duration_min % 60
    return f"{hours}시간 {mins}분" if hours > 0 else f"{mins}분"


# ==========================================
# 🖥️ 웹 페이지 화면 구성
# ==========================================
st.set_page_config(page_title="나만의 내비게이션 비교", page_icon="🚗", layout="wide")

# 타이틀 및 자동차 아이콘 처리
image_path = "mycar.jpg"
if os.path.exists(image_path):
    with open(image_path, "rb") as f:
        img_data = f.read()
        b64_encoded = base64.b64encode(img_data).decode()
    html_title = f"""
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <img src="data:image/jpeg;base64,{b64_encoded}" style="width: 70px; height: 70px; border-radius: 15px; object-fit: cover; margin-right: 15px; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);">
        <h1 style="margin: 0; padding: 0;">나만의 실시간 길찾기 비교</h1>
    </div>
    """
    st.markdown(html_title, unsafe_allow_html=True)
else:
    st.title("🚗 나만의 실시간 길찾기 비교")

# 🌟 URL에서 저장된 집/회사 주소 불러오기
saved_home = st.query_params.get("home", "")
saved_work = st.query_params.get("work", "")

st.markdown("### ⚙️ 나의 기본 주소 설정 (입력 시 즐겨찾기용 주소가 자동 생성됩니다)")
setting_col1, setting_col2 = st.columns(2)
with setting_col1:
    home_address = st.text_input("🏠 우리 집", value=saved_home, placeholder="예: 서울특별시 강남구 역삼동")
with setting_col2:
    work_address = st.text_input("🏢 우리 회사", value=saved_work, placeholder="예: 경기도 성남시 분당구 판교역로")

# 입력값이 바뀌면 브라우저 상단 주소창 URL을 실시간으로 업데이트
if home_address:
    st.query_params["home"] = home_address
if work_address:
    st.query_params["work"] = work_address

st.markdown("---")

# 🌟 경로 프리셋 선택 메뉴
route_choice = st.radio(
    "🚗 조회할 경로 선택",
    ["1️⃣ 출근길 (집 ➔ 회사)", "2️⃣ 퇴근길 (회사 ➔ 집)", "3️⃣ 직접 설정"],
    horizontal=True
)

# 선택에 따른 출발지/도착지 자동 매핑
is_custom = False
if route_choice == "1️⃣ 출근길 (집 ➔ 회사)":
    start_target = home_address
    end_target = work_address
elif route_choice == "2️⃣ 퇴근길 (회사 ➔ 집)":
    start_target = work_address
    end_target = home_address
else:
    is_custom = True
    start_target = ""
    end_target = ""

st.markdown("<br>", unsafe_allow_html=True)

# 3번 '직접 설정'을 누른 경우에만 입력칸을 띄우고, 1/2번은 현재 경로만 텍스트로 보여줍니다.
if is_custom:
    col1, col2 = st.columns(2)
    with col1:
        start_target = st.text_input("출발지 직접 입력", placeholder="출발지를 입력하세요")
    with col2:
        end_target = st.text_input("도착지 직접 입력", placeholder="도착지를 입력하세요")
else:
    st.info(
        f"📍 **현재 선택된 경로:** {start_target if start_target else '(집 주소 미입력)'} ➔ {end_target if end_target else '(회사 주소 미입력)'}")

if "show_results" not in st.session_state:
    st.session_state.show_results = False

if st.button("시간 비교 및 경로 보기", use_container_width=True):
    if not start_target or not end_target:
        st.warning("출발지와 도착지를 모두 정확히 설정해 주세요.")
    else:
        with st.spinner("데이터를 수집 및 분석하는 중입니다..."):
            start_x, start_y = get_kakao_coords(start_target)
            end_x, end_y = get_kakao_coords(end_target)

            if start_x and end_x:
                k_dist, k_dur, k_path, k_guides = get_kakao_route(start_x, start_y, end_x, end_y)
                t_dist, t_dur, t_path, t_guides = get_tmap_route(start_x, start_y, end_x, end_y)

                st.session_state.results = {
                    "kakao": (k_dist, k_dur),
                    "tmap": (t_dist, t_dur)
                }
                st.session_state.k_path = k_path
                st.session_state.k_guides = k_guides
                st.session_state.t_path = t_path
                st.session_state.t_guides = t_guides
                st.session_state.show_results = True
            else:
                st.session_state.show_results = False
                st.error("입력하신 주소나 장소를 찾을 수 없습니다. 철자를 확인하거나 더 자세히 입력해 주세요.")

# --- 결과 화면 출력 ---
if st.session_state.show_results:
    st.success("💡 **Tip:** 브라우저 맨 위의 **주소창 링크를 복사해서 즐겨찾기(북마크)에 저장**해 보세요! 지금 설정한 집과 회사 주소가 평생 그대로 저장됩니다.")

    res = st.session_state.results

    st.subheader("📊 예상 소요 시간 결과")
    c1, c2 = st.columns(2)

    k_dist, k_dur = res["kakao"]
    c1.metric(label="🟡 카카오내비", value=format_time(k_dur), delta=f"{k_dist} km" if k_dist else "데이터 없음",
              delta_color="off")

    t_dist, t_dur = res["tmap"]
    c2.metric(label="🔴 티맵", value=format_time(t_dur), delta=f"{t_dist} km" if t_dist else "데이터 없음", delta_color="off")

    st.markdown("---")

    map_col1, map_col2 = st.columns(2)

    with map_col1:
        st.subheader("🗺️ 카카오내비 경로")
        k_path = st.session_state.k_path
        if k_path:
            mid_idx = len(k_path) // 2
            m1 = folium.Map(location=k_path[mid_idx], zoom_start=11)
            folium.Marker(k_path[0], popup="출발", icon=folium.Icon(color="blue", icon="play")).add_to(m1)
            folium.Marker(k_path[-1], popup="도착", icon=folium.Icon(color="red", icon="stop")).add_to(m1)
            folium.PolyLine(locations=k_path, color="#1E90FF", weight=5, opacity=0.8).add_to(m1)
            st_folium(m1, use_container_width=True, height=500, key="kakao_map")

        k_guides = st.session_state.k_guides
        if k_guides:
            with st.expander("📋 카카오 상세 경로 안내 보기"):
                for idx, guide in enumerate(k_guides, 1):
                    st.write(f"{idx}. {guide}")

    with map_col2:
        st.subheader("🗺️ 티맵 경로")
        t_path = st.session_state.t_path
        if t_path:
            mid_idx = len(t_path) // 2
            m2 = folium.Map(location=t_path[mid_idx], zoom_start=11)
            folium.Marker(t_path[0], popup="출발", icon=folium.Icon(color="blue", icon="play")).add_to(m2)
            folium.Marker(t_path[-1], popup="도착", icon=folium.Icon(color="red", icon="stop")).add_to(m2)
            folium.PolyLine(locations=t_path, color="#FF4500", weight=5, opacity=0.8).add_to(m2)
            st_folium(m2, use_container_width=True, height=500, key="tmap_map")

        t_guides = st.session_state.t_guides
        if t_guides:
            with st.expander("📋 티맵 상세 경로 안내 보기"):
                for idx, guide in enumerate(t_guides, 1):
                    st.write(f"{idx}. {guide}")