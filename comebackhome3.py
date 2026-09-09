import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import base64
import os
import urllib.parse
import datetime
import pandas as pd

# ==========================================
# 🖥️ 웹 페이지 기본 설정
# ==========================================
st.set_page_config(page_title="나만의 내비게이션 Pro", page_icon="🚗", layout="wide")

# ==========================================
# 🎨 UI/UX 디자인 (세련된 모바일 뷰 유지)
# ==========================================
custom_css = """
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"], p, span, div, label { 
        font-family: 'Pretendard', sans-serif !important; 
        font-size: 14.5px !important; 
    }
    
    h1 { font-size: 26px !important; font-weight: 800 !important; letter-spacing: -1px; }
    h3 { font-size: 18px !important; font-weight: 700 !important; }
    
    div.stButton > button[kind="primary"] {
        background-color: #111111 !important; color: #FFFFFF !important;
        font-weight: 700 !important; border-radius: 8px !important;
        padding: 8px 0 !important; box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        transition: 0.2s;
    }
    div.stButton > button[kind="primary"]:hover { transform: translateY(-2px) !important; }

    .result-card {
        background: #ffffff; border: 1px solid #eaeaea; border-radius: 12px;
        padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 15px;
    }
    .rank-badge {
        color: white; padding: 4px 10px; border-radius: 20px; font-weight: 800; font-size: 12px;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# 🔑 API 키 설정
# ==========================================
try:
    KAKAO_API_KEY = st.secrets["KAKAO_API_KEY"]
    TMAP_APP_KEY = st.secrets["TMAP_APP_KEY"]
except:
    KAKAO_API_KEY = "96fc63ab0efc0a7d8591eeb8b34db8a9"
    TMAP_APP_KEY = "kstcD6L0he3GU4SSTkWNF6IHGefkURVXak3qpabh"

# ==========================================
# 🛠️ 길찾기 핵심 함수 모음
# ==========================================
def get_kakao_coords(address):
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    for url in ["https://dapi.kakao.com/v2/local/search/keyword.json", "https://dapi.kakao.com/v2/local/search/address.json"]:
        res = requests.get(url, headers=headers, params={"query": address}).json()
        if res.get('documents'): return res['documents'][0]['x'], res['documents'][0]['y']
    return None, None

def get_kakao_route(start_x, start_y, end_x, end_y, solid_color=None):
    url = "https://apis-navi.kakaomobility.com/v1/directions"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"origin": f"{start_x},{start_y}", "destination": f"{end_x},{end_y}", "priority": "RECOMMEND"}
    res = requests.get(url, headers=headers, params=params).json()
    if res.get('routes'):
        route = res['routes'][0]
        distance_km = round(route['summary']['distance'] / 1000, 1)
        duration_min = round(route['summary']['duration'] / 60)
        segments = []
        for section in route.get('sections', []):
            for road in section.get('roads', []):
                if solid_color:
                    color = solid_color
                else:
                    color = {1:"#FF0000", 2:"#FF8C00", 3:"#FFD700", 4:"#008000"}.get(road.get('traffic_state', 0), "#1E90FF")
                coords = [[v, road['vertexes'][i]] for i, v in enumerate(road['vertexes'][1::2])]
                if coords: segments.append({"coords": coords, "color": color})
        return distance_km, duration_min, segments
    return None, None, []

def get_tmap_route(start_x, start_y, end_x, end_y):
    url = "https://apis.openapi.sk.com/tmap/routes?version=1&format=json"
    headers = {"appKey": TMAP_APP_KEY, "Content-Type": "application/json"}
    payload = {"startX": str(start_x), "startY": str(start_y), "endX": str(end_x), "endY": str(end_y),
               "startName": "S", "endName": "E", "reqCoordType": "WGS84GEO", "resCoordType": "WGS84GEO"}
    try:
        res = requests.post(url, headers=headers, json=payload).json()
        if 'features' in res:
            dist = round(res['features'][0]['properties']['totalDistance'] / 1000, 1)
            time = round(res['features'][0]['properties']['totalTime'] / 60) 
            segments = [{"coords": [[c[1], c[0]] for c in f['geometry']['coordinates']], "color": "#1E90FF"} 
                        for f in res['features'] if f.get('geometry', {}).get('type') == 'LineString']
            return dist, time, segments
    except: pass
    return None, None, []

def get_tmap_prediction(start_x, start_y, end_x, end_y, time_str):
    url = "https://apis.openapi.sk.com/tmap/routes/prediction?version=1&format=json"
    headers = {"appKey": TMAP_APP_KEY, "Content-Type": "application/json"}
    # 🌟 버그 수정: predictionType 누락 해결 및 정확한 포맷 전달
    payload = {
        "reqCoordType": "WGS84GEO", "resCoordType": "WGS84GEO",
        "startX": str(start_x), "startY": str(start_y), "endX": str(end_x), "endY": str(end_y),
        "startName": "S", "endName": "E", 
        "predictionType": "departure", 
        "predictionTime": time_str
    }
    try:
        res = requests.post(url, headers=headers, json=payload).json()
        if 'features' in res:
            return round(res['features'][0]['properties']['totalTime'] / 60), ""
        else:
            return None, str(res)
    except Exception as e: 
        return None, str(e)

def format_time(mins):
    if mins is None: return "오류"
    h, m = mins // 60, mins % 60
    return f"{h}시간 {m}분" if h > 0 else f"{m}분"

# ==========================================
# 🌟 지도 꺼짐 방지용 세션(캐시) 초기화
# ==========================================
if "t1_res" not in st.session_state: st.session_state.t1_res = None
if "t2_res" not in st.session_state: st.session_state.t2_res = None
if "t3_res" not in st.session_state: st.session_state.t3_res = None

# ==========================================
# 🖥️ 사이드바 (차량 이미지 커스텀)
# ==========================================
with st.sidebar:
    st.markdown("### 🚘 내 차 이미지")
    uploaded_img = st.file_uploader("그랑콜레오스 등 내 차 사진 업로드", type=["jpg", "jpeg", "png"])
b64_encoded = base64.b64encode(uploaded_img.read()).decode() if uploaded_img else (base64.b64encode(open("mycar.jpg", "rb").read()).decode() if os.path.exists("mycar.jpg") else "")

if b64_encoded:
    st.markdown(f'<div style="display:flex; align-items:center; margin-bottom:15px;"><img src="data:image/jpeg;base64,{b64_encoded}" style="width:60px; height:60px; border-radius:12px; object-fit:cover; margin-right:15px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);"><h1 style="margin:0;">나만의 내비게이션 Pro</h1></div>', unsafe_allow_html=True)
else:
    st.title("🚗 나만의 내비게이션 Pro")

# ==========================================
# ⚙️ 공통 설정 (기존 출퇴근 기능 완벽 복구)
# ==========================================
saved_home = st.query_params.get("home", "")
saved_work = st.query_params.get("work", "")

st.markdown("### ⚙️ 나의 기본 주소 설정")
c1, c2 = st.columns(2)
with c1: home_address = st.text_input("🏠 우리 집", value=saved_home, placeholder="예: 의정부시 신곡동 파크프라임")
with c2: work_address = st.text_input("🏢 우리 회사", value=saved_work, placeholder="예: 서울 금천구 가산동 케이앤웍스")

if home_address: st.query_params["home"] = home_address
if work_address: st.query_params["work"] = work_address

st.markdown("---")

# ==========================================
# 🚀 3개의 탭으로 기능 분리
# ==========================================
tab1, tab2, tab3 = st.tabs(["🗺️ 1:1 실시간 경로", "📍 다중 출발지 승부", "🔮 시간대별 타임머신"])
kst_now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)

google_tiles = "https://mt1.google.com/vt/lyrs=m&hl=ko&x={x}&y={y}&z={z}"

# ------------------------------------------
# 탭 1: 기존 1:1 실시간 경로
# ------------------------------------------
with tab1:
    # 🌟 출퇴근 라디오 버튼 복구!
    route_choice = st.radio("🚗 조회할 경로 선택", ["1️⃣ 출근길 (집 ➔ 회사)", "2️⃣ 퇴근길 (회사 ➔ 집)", "3️⃣ 직접 설정"], index=0 if kst_now.hour < 12 else 1, horizontal=True)
    
    is_custom = False
    if route_choice == "1️⃣ 출근길 (집 ➔ 회사)": start_target, end_target = home_address, work_address
    elif route_choice == "2️⃣ 퇴근길 (회사 ➔ 집)": start_target, end_target = work_address, home_address
    else:
        is_custom = True
        start_target, end_target = "", ""

    if is_custom:
        ct1, ct2 = st.columns(2)
        with ct1: start_target = st.text_input("출발지 직접 입력", placeholder="출발지를 입력하세요")
        with ct2: end_target = st.text_input("도착지 직접 입력", placeholder="도착지를 입력하세요")
    else:
        st.info(f"📍 **현재 선택된 경로:** {start_target if start_target else '(집 미입력)'} ➔ {end_target if end_target else '(회사 미입력)'}")

    if st.button("실시간 2파전 비교하기", type="primary", key="btn1", use_container_width=True):
        if not start_target or not end_target:
            st.warning("출발지와 도착지를 모두 정확히 설정해 주세요.")
        else:
            with st.spinner("경로를 탐색 중입니다..."):
                sx, sy = get_kakao_coords(start_target)
                ex, ey = get_kakao_coords(end_target)
                if sx and ex:
                    k_dist, k_dur, k_seg = get_kakao_route(sx, sy, ex, ey)
                    t_dist, t_dur, t_seg = get_tmap_route(sx, sy, ex, ey)
                    # 🌟 결과를 세션에 단단히 저장 (지도 안꺼짐)
                    st.session_state.t1_res = {
                        "k_dist": k_dist, "k_dur": k_dur, "k_seg": k_seg,
                        "t_dist": t_dist, "t_dur": t_dur, "t_seg": t_seg,
                        "end_target": end_target, "ex": ex, "ey": ey, "sx": sx, "sy": sy
                    }
                else:
                    st.error("주소를 찾을 수 없습니다.")

    # 🌟 저장된 결과가 있으면 항상 그려줌 (마우스를 만져도 유지됨)
    if st.session_state.t1_res:
        res = st.session_state.t1_res
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        rc1, rc2 = st.columns(2)
        safe_end = urllib.parse.quote(res["end_target"])
        rc1.metric("🟡 카카오내비", format_time(res["k_dur"]), f"{res['k_dist']} km" if res["k_dist"] else "")
        rc1.markdown(f'<a href="https://map.kakao.com/link/to/{safe_end},{res["ey"]},{res["ex"]}" target="_blank" style="display:block; text-align:center; padding:10px; background:#FEE500; color:#000; text-decoration:none; border-radius:8px; font-weight:700;">🟡 카카오 앱 열기</a>', unsafe_allow_html=True)
        rc2.metric("🔴 티맵", format_time(res["t_dur"]), f"{res['t_dist']} km" if res["t_dist"] else "")
        rc2.markdown(f'<a href="tmap://route?goalname={safe_end}&goalx={res["ex"]}&goaly={res["ey"]}" style="display:block; text-align:center; padding:10px; background:#EF4C35; color:#FFF; text-decoration:none; border-radius:8px; font-weight:700;">🔴 티맵 앱 열기</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        map_c1, map_c2 = st.columns(2)
        start_icon = '<div style="background:#1E90FF; color:white; border-radius:50%; width:24px; height:24px; display:flex; justify-content:center; align-items:center; font-weight:bold; font-size:12px; border:2px solid white;">S</div>'
        end_icon = '<div style="background:#FF0000; color:white; border-radius:50%; width:24px; height:24px; display:flex; justify-content:center; align-items:center; font-weight:bold; font-size:12px; border:2px solid white;">E</div>'
        
        with map_c1:
            st.caption("🗺️ 카카오내비 상세 정체구간")
            if res["k_seg"]:
                coords = [c for s in res["k_seg"] for c in s['coords']]
                m1 = folium.Map(location=coords[len(coords)//2], zoom_start=11, tiles=google_tiles, attr="Google")
                folium.Marker(coords[0], icon=folium.DivIcon(html=start_icon)).add_to(m1)
                folium.Marker(coords[-1], icon=folium.DivIcon(html=end_icon)).add_to(m1)
                for s in res["k_seg"]: folium.PolyLine(locations=s['coords'], color=s['color'], weight=5, opacity=0.9).add_to(m1)
                m1.fit_bounds(coords)
                st_folium(m1, use_container_width=True, height=400, key="m1_t1")
        with map_c2:
            st.caption("🗺️ 티맵 최적 경로")
            if res["t_seg"]:
                coords = [c for s in res["t_seg"] for c in s['coords']]
                m2 = folium.Map(location=coords[len(coords)//2], zoom_start=11, tiles=google_tiles, attr="Google")
                folium.Marker(coords[0], icon=folium.DivIcon(html=start_icon)).add_to(m2)
                folium.Marker(coords[-1], icon=folium.DivIcon(html=end_icon)).add_to(m2)
                for s in res["t_seg"]: folium.PolyLine(locations=s['coords'], color=s['color'], weight=5, opacity=0.9).add_to(m2)
                m2.fit_bounds(coords)
                st_folium(m2, use_container_width=True, height=400, key="m2_t1")

# ------------------------------------------
# 탭 2: 다중 출발지 승부 (통합 지도 추가)
# ------------------------------------------
with tab2:
    st.markdown("### 📍 어디서 출발하는게 가장 빠를까?")
    t2_end = st.text_input("🎯 공통 도착지", value=work_address, key="t2_e")
    st.caption("출발 후보지 (비워두면 계산에서 제외됩니다)")
    c1, c2, c3 = st.columns(3)
    with c1: t2_s1 = st.text_input("후보 1", value=home_address, key="t2_s1")
    with c2: t2_s2 = st.text_input("후보 2", placeholder="예: 구리시 인창동", key="t2_s2")
    with c3: t2_s3 = st.text_input("후보 3", placeholder="다른 출발지 입력", key="t2_s3")
    
    if st.button("출발지별 소요시간 랭킹 보기", type="primary", key="btn2", use_container_width=True):
        with st.spinner("각 출발지별 시간을 계산 중입니다..."):
            ex, ey = get_kakao_coords(t2_end)
            if not ex: st.error("도착지 주소를 확인해주세요.")
            else:
                results = []
                for idx, (name, s_addr) in enumerate([("후보 1", t2_s1), ("후보 2", t2_s2), ("후보 3", t2_s3)]):
                    if s_addr.strip():
                        sx, sy = get_kakao_coords(s_addr)
                        if sx:
                            _, k_dur, _ = get_kakao_route(sx, sy, ex, ey)
                            _, t_dur, _ = get_tmap_route(sx, sy, ex, ey)
                            avg_dur = ((k_dur or 0) + (t_dur or 0)) / 2
                            results.append({"id": idx+1, "name": s_addr, "sx":sx, "sy":sy, "kakao": k_dur, "tmap": t_dur, "avg": avg_dur})
                
                if results:
                    results = sorted(results, key=lambda x: x["avg"])
                    # 순위 매기기 및 색상 부여 (1등 빨강, 2등 파랑, 3등 초록)
                    colors = ["#FF4B4B", "#1E90FF", "#03C75A"]
                    for i, res in enumerate(results):
                        res["rank"] = i + 1
                        res["color"] = colors[i] if i < len(colors) else "#555555"
                    
                    st.session_state.t2_res = {"results": results, "ex": ex, "ey": ey}
    
    # 🌟 저장된 결과가 있으면 항상 그려줌 (지도 추가)
    if st.session_state.t2_res:
        res_data = st.session_state.t2_res
        results = res_data["results"]
        ex, ey = res_data["ex"], res_data["ey"]
        
        # 1. 랭킹 카드 렌더링
        for res in results:
            rank, badge_color = res["rank"], res["color"]
            st.markdown(f"""
            <div class="result-card" style="{ 'border: 2px solid #FF4B4B;' if rank == 1 else '' }">
                <span class="rank-badge" style="background:{badge_color}">현재 {rank}등</span> 
                <strong style="font-size:16px; margin-left:8px;">{res['name']}</strong> ➔ {t2_end}
                <div style="margin-top:10px; font-size:15px;">
                    🟡 카카오: <b>{format_time(res['kakao'])}</b> &nbsp;|&nbsp; 🔴 티맵: <b>{format_time(res['tmap'])}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        # 2. 통합 다중 경로 지도 렌더링
        st.markdown("#### 🗺️ 순위별 경로 비교 지도")
        m_multi = folium.Map(location=[float(ey), float(ex)], zoom_start=11, tiles=google_tiles, attr="Google")
        end_icon = '<div style="background:#000000; color:white; border-radius:50%; width:26px; height:26px; display:flex; justify-content:center; align-items:center; font-weight:bold; font-size:12px; border:2px solid white;">도착</div>'
        folium.Marker([float(ey), float(ex)], icon=folium.DivIcon(html=end_icon)).add_to(m_multi)
        
        all_coords_multi = []
        for res in results:
            # 겹쳤을 때 보기 편하게 각 순위별 단일 색상으로 경로를 따옵니다.
            _, _, segs = get_kakao_route(res["sx"], res["sy"], ex, ey, solid_color=res["color"])
            if segs:
                s_icon = f'<div style="background:{res["color"]}; color:white; border-radius:50%; width:28px; height:28px; display:flex; justify-content:center; align-items:center; font-weight:bold; font-size:12px; border:2px solid white;">{res["rank"]}등</div>'
                folium.Marker([float(res["sy"]), float(res["sx"])], icon=folium.DivIcon(html=s_icon)).add_to(m_multi)
                for s in segs: 
                    folium.PolyLine(locations=s['coords'], color=s['color'], weight=6, opacity=0.8).add_to(m_multi)
                    all_coords_multi.extend(s['coords'])
        
        if all_coords_multi:
            m_multi.fit_bounds(all_coords_multi)
        st_folium(m_multi, use_container_width=True, height=500, key="m_multi_t2")

# ------------------------------------------
# 탭 3: 티맵 타임머신 (버그 수정 완료)
# ------------------------------------------
with tab3:
    st.markdown("### 🔮 몇 시에 출발해야 안 막힐까?")
    st.info("티맵 빅데이터를 분석하여 **현재 시간부터 +3시간 뒤**까지의 교통량을 예측합니다.")
    c1, c2 = st.columns(2)
    with c1: t3_start = st.text_input("출발지", value=home_address, key="t3_s")
    with c2: t3_end = st.text_input("도착지", value=work_address, key="t3_e")
    
    if st.button("시간대별 예측 그래프 보기", type="primary", key="btn3", use_container_width=True):
        with st.spinner("티맵 타임머신을 가동 중입니다... (약 5초 소요)"):
            sx, sy = get_kakao_coords(t3_start)
            ex, ey = get_kakao_coords(t3_end)
            if sx and ex:
                times, durations = [], []
                err_log = ""
                
                # 지금, +1시간, +2시간, +3시간 계산
                for i in range(4):
                    target_time = kst_now + datetime.timedelta(hours=i)
                    # 티맵 서버가 요구하는 정확한 날짜 포맷
                    time_str = target_time.strftime("%Y-%m-%dT%H:%M:%S+0900") 
                    label = "지금 출발" if i == 0 else f"+{i}시간 뒤 ({target_time.strftime('%H:%M')})"
                    
                    pred_mins, err = get_tmap_prediction(sx, sy, ex, ey, time_str)
                    if pred_mins:
                        times.append(label)
                        durations.append(pred_mins)
                    if err:
                        err_log = err
                
                st.session_state.t3_res = {"times": times, "durations": durations, "err": err_log}
            else: 
                st.error("주소를 찾을 수 없습니다.")
                
    # 🌟 저장된 결과가 있으면 항상 그려줌
    if st.session_state.t3_res:
        res = st.session_state.t3_res
        if res["durations"]:
            chart_data = pd.DataFrame({"출발 시간대": res["times"], "예상 소요시간(분)": res["durations"]})
            chart_data = chart_data.set_index("출발 시간대")
            st.bar_chart(chart_data, height=300)
            
            min_time = min(res["durations"])
            best_idx = res["durations"].index(min_time)
            st.success(f"💡 **가장 추천하는 시간:** {res['times'][best_idx]}에 출발하시면 약 {format_time(min_time)}이 소요되어 가장 쾌적합니다!")
        else:
            st.error(f"티맵 예측 데이터를 가져올 수 없습니다. (에러: {res['err']})")
