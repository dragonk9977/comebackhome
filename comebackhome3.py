import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import base64
import os
import urllib.parse
import datetime

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
        
        segments = []
        for section in route.get('sections', []):
            for road in section.get('roads', []):
                traffic_state = road.get('traffic_state', 0)
                
                if traffic_state == 1: color = "#FF0000"   
                elif traffic_state == 2: color = "#FF8C00" 
                elif traffic_state == 3: color = "#FFD700" 
                elif traffic_state == 4: color = "#008000" 
                else: color = "#1E90FF"                    

                vertexes = road.get('vertexes', [])
                road_coords = []
                for i in range(0, len(vertexes), 2):
                    road_coords.append([vertexes[i+1], vertexes[i]])
                    
                if road_coords:
                    segments.append({"coords": road_coords, "color": color})
                    
        guides = [g.get('guidance') for s in route.get('sections', []) for g in s.get('guides', []) if g.get('guidance')]
        return distance_km, duration_min, segments, guides
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
            
            segments = []
            guides = []
            
            for feature in data['features']:
                geom = feature.get('geometry', {})
                p = feature.get('properties', {})
                
                if geom.get('type') == 'LineString':
                    line_coords = []
                    for coord in geom.get('coordinates', []):
                        line_coords.append([coord[1], coord[0]])
                        
                    if line_coords:
                        segments.append({"coords": line_coords, "color": "#1E90FF"})
                
                if geom.get('type') == 'Point' and 'description' in p:
                    guides.append(p['description'])
                    
            return distance_km, duration_min, segments, guides
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

saved_home = st.query_params.get("home", "")
saved_work = st.query_params.get("work", "")

st.markdown("### ⚙️ 나의 기본 주소 설정 (입력 시 즐겨찾기용 주소가 자동 생성됩니다)")
setting_col1, setting_col2 = st.columns(2)
with setting_col1:
    home_address = st.text_input("🏠 우리 집", value=saved_home, placeholder="예: 서울특별시 강남구 역삼동")
with setting_col2:
    work_address = st.text_input("🏢 우리 회사", value=saved_work, placeholder="예: 경기도 성남시 분당구 판교역로")

if home_address:
    st.query_params["home"] = home_address
if work_address:
    st.query_params["work"] = work_address

st.markdown("---")

kst_now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
current_hour = kst_now.hour
default_route_idx = 0 if current_hour < 12 else 1

route_choice = st.radio(
    "🚗 조회할 경로 선택",
    ["1️⃣ 출근길 (집 ➔ 회사)", "2️⃣ 퇴근길 (회사 ➔ 집)", "3️⃣ 직접 설정"],
    index=default_route_idx,
    horizontal=True
)

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

if is_custom:
    col1, col2 = st.columns(2)
    with col1:
        start_target = st.text_input("출발지 직접 입력", placeholder="출발지를 입력하세요")
    with col2:
        end_target = st.text_input("도착지 직접 입력", placeholder="도착지를 입력하세요")
else:
    st.info(f"📍 **현재 선택된 경로:** {start_target if start_target else '(집 주소 미입력)'} ➔ {end_target if end_target else '(회사 주소 미입력)'}")

if "last_route_choice" not in st.session_state:
    st.session_state.last_route_choice = None

do_search = st.button("시간 비교 및 경로 보기", use_container_width=True)

if st.session_state.last_route_choice != route_choice:
    st.session_state.last_route_choice = route_choice
    if start_target and end_target:
        do_search = True

if "show_results" not in st.session_state:
    st.session_state.show_results = False

if do_search:
    if not start_target or not end_target:
        st.warning("출발지와 도착지를 모두 정확히 설정해 주세요.")
    else:
        with st.spinner("데이터를 수집 및 분석하는 중입니다..."):
            start_x, start_y = get_kakao_coords(start_target)
            end_x, end_y = get_kakao_coords(end_target)
    
            if start_x and end_x:
                k_dist, k_dur, k_segments, k_guides = get_kakao_route(start_x, start_y, end_x, end_y)
                t_dist, t_dur, t_segments, t_guides = get_tmap_route(start_x, start_y, end_x, end_y)
                
                st.session_state.results = {
                    "kakao": (k_dist, k_dur),
                    "tmap": (t_dist, t_dur),
                    "end_info": (end_target, end_x, end_y) 
                }
                st.session_state.k_segments = k_segments
                st.session_state.k_guides = k_guides
                st.session_state.t_segments = t_segments
                st.session_state.t_guides = t_guides
                st.session_state.show_results = True
            else:
                st.session_state.show_results = False
                st.error("입력하신 주소나 장소를 찾을 수 없습니다. 철자를 확인하거나 더 자세히 입력해 주세요.")

# --- 결과 화면 출력 ---
if st.session_state.show_results:
    st.info("💡 **교통 상황 색상 안내:** 🔴 매우 정체 ｜ 🟠 정체 ｜ 🟡 보통 ｜ 🟢 원활 (카카오내비 전용)\n\n"
            "⚠️ **안내:** 티맵 오픈 API 정책상 외부 앱에는 구간별 혼잡도 데이터가 제한되어 파란색으로만 표기됩니다. 상세 정체 구간은 카카오내비 지도를 참고해 주세요!")
    res = st.session_state.results
    end_name, e_x, e_y = res["end_info"]
    safe_end_name = urllib.parse.quote(end_name)
    
    st.subheader("📊 예상 소요 시간 결과")
    c1, c2 = st.columns(2)
    
    k_dist, k_dur = res["kakao"]
    c1.metric(label="🟡 카카오내비", value=format_time(k_dur), delta=f"{k_dist} km" if k_dist else "데이터 없음", delta_color="off")
    kakao_link = f"https://map.kakao.com/link/to/{safe_end_name},{e_y},{e_x}"
    c1.markdown(f'<a href="{kakao_link}" target="_blank" style="display: block; width: 100%; text-align: center; padding: 12px; background-color: #FEE500; color: #000000; text-decoration: none; border-radius: 8px; font-weight: bold; margin-top: 10px; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">🟡 카카오내비 앱 열기</a>', unsafe_allow_html=True)
    
    t_dist, t_dur = res["tmap"]
    c2.metric(label="🔴 티맵", value=format_time(t_dur), delta=f"{t_dist} km" if t_dist else "데이터 없음", delta_color="off")
    tmap_link = f"tmap://route?goalname={safe_end_name}&goalx={e_x}&goaly={e_y}"
    c2.markdown(f'<a href="{tmap_link}" style="display: block; width: 100%; text-align: center; padding: 12px; background-color: #EF4C35; color: #FFFFFF; text-decoration: none; border-radius: 8px; font-weight: bold; margin-top: 10px; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">🔴 티맵 앱 열기</a>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 🌟 지도 새로고침 전용 세션(고유 Key) 생성
    if "map_reset_key" not in st.session_state:
        st.session_state.map_reset_key = 0

    # 🌟 이 버튼을 누르면 고유 Key가 바뀌면서 지도가 완벽하게 새로 그려집니다!
    if st.button("🔄 지도 화면 원래대로 되돌리기 (경로 한눈에 보기)", use_container_width=True):
        st.session_state.map_reset_key += 1
    
    start_html = '<div style="background-color: #1E90FF; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; justify-content: center; align-items: center; font-weight: bold; border: 2px solid white; box-shadow: 1px 1px 3px rgba(0,0,0,0.4); font-size: 14px; font-family: Arial, sans-serif;">S</div>'
    end_html = '<div style="background-color: #FF0000; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; justify-content: center; align-items: center; font-weight: bold; border: 2px solid white; box-shadow: 1px 1px 3px rgba(0,0,0,0.4); font-size: 14px; font-family: Arial, sans-serif;">E</div>'
    
    google_tiles = "https://mt1.google.com/vt/lyrs=m&hl=ko&x={x}&y={y}&z={z}"
    
    map_col1, map_col2 = st.columns(2)
    
    with map_col1:
        st.subheader("🗺️ 카카오내비 경로")
        k_segments = st.session_state.k_segments
        if k_segments:
            all_k_coords = [coord for seg in k_segments for coord in seg['coords']]
            
            # 🌟 scrollWheelZoom 옵션 제거 -> 휠로 자유롭게 확대/축소 가능!
            m1 = folium.Map(
                location=all_k_coords[len(all_k_coords)//2], 
                zoom_start=11, 
                tiles=google_tiles,
                attr="Google Maps"
            )
            
            folium.Marker(all_k_coords[0], icon=folium.DivIcon(html=start_html, icon_anchor=(14, 14))).add_to(m1)
            folium.Marker(all_k_coords[-1], icon=folium.DivIcon(html=end_html, icon_anchor=(14, 14))).add_to(m1)
            
            for seg in k_segments:
                folium.PolyLine(locations=seg['coords'], color=seg['color'], weight=6, opacity=0.9).add_to(m1)
            
            m1.fit_bounds(all_k_coords)
            # 🌟 고유 Key를 적용하여 버튼 누를 때마다 화면 갱신 강제 수행
            st_folium(m1, use_container_width=True, height=500, key=f"kakao_map_{st.session_state.map_reset_key}")
            
    with map_col2:
        st.subheader("🗺️ 티맵 경로")
        t_segments = st.session_state.t_segments
        if t_segments:
            all_t_coords = [coord for seg in t_segments for coord in seg['coords']]
            
            # 🌟 scrollWheelZoom 옵션 제거 -> 휠로 자유롭게 확대/축소 가능!
            m2 = folium.Map(
                location=all_t_coords[len(all_t_coords)//2], 
                zoom_start=11, 
                tiles=google_tiles,
                attr="Google Maps"
            )
            
            folium.Marker(all_t_coords[0], icon=folium.DivIcon(html=start_html, icon_anchor=(14, 14))).add_to(m2)
            folium.Marker(all_t_coords[-1], icon=folium.DivIcon(html=end_html, icon_anchor=(14, 14))).add_to(m2)
            
            for seg in t_segments:
                folium.PolyLine(locations=seg['coords'], color=seg['color'], weight=6, opacity=0.9).add_to(m2)
                
            m2.fit_bounds(all_t_coords)
            # 🌟 고유 Key를 적용하여 버튼 누를 때마다 화면 갱신 강제 수행
            st_folium(m2, use_container_width=True, height=500, key=f"tmap_map_{st.session_state.map_reset_key}")
