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
# 🖥️ 웹 페이지 기본 설정 (가장 먼저 실행)
# ==========================================
st.set_page_config(page_title="나만의 내비게이션 Pro", page_icon="🚗", layout="wide")

# ==========================================
# 🎨 UI/UX 전면 개편 (세련된 모바일 앱 스타일 CSS)
# ==========================================
custom_css = """
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    /* 전체 폰트 및 크기 축소 */
    html, body, [class*="css"], p, span, div, label { 
        font-family: 'Pretendard', sans-serif !important; 
        font-size: 14.5px !important; /* 글씨를 작고 오밀조밀하게 */
    }
    
    h1 { font-size: 26px !important; font-weight: 800 !important; letter-spacing: -1px; }
    h3 { font-size: 18px !important; font-weight: 700 !important; }
    
    /* 탭(Tab) 디자인 세련되게 */
    button[data-baseweb="tab"] { font-size: 16px !important; font-weight: 600 !important; }

    /* 메인 버튼 강조 */
    div.stButton > button[kind="primary"] {
        background-color: #111111 !important; color: #FFFFFF !important;
        font-weight: 700 !important; border-radius: 8px !important;
        padding: 8px 0 !important; box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        transition: 0.2s;
    }
    div.stButton > button[kind="primary"]:hover { transform: translateY(-2px) !important; }

    /* 결과 카드(Card) UI */
    .result-card {
        background: #ffffff; border: 1px solid #eaeaea; border-radius: 12px;
        padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 15px;
    }
    .rank-badge {
        background: #1E90FF; color: white; padding: 4px 10px; 
        border-radius: 20px; font-weight: 800; font-size: 12px;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# 🔑 API 키 설정 (카카오 & 티맵 전용)
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

def get_kakao_route(start_x, start_y, end_x, end_y):
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
    """티맵 타임머신(미래 시간대별 예측) API"""
    url = "https://apis.openapi.sk.com/tmap/routes/prediction?version=1&format=json"
    headers = {"appKey": TMAP_APP_KEY, "Content-Type": "application/json"}
    payload = {
        "reqCoordType": "WGS84GEO", "resCoordType": "WGS84GEO",
        "startX": str(start_x), "startY": str(start_y), "endX": str(end_x), "endY": str(end_y),
        "startName": "S", "endName": "E", "predictionTime": time_str
    }
    try:
        res = requests.post(url, headers=headers, json=payload).json()
        if 'features' in res:
            return round(res['features'][0]['properties']['totalTime'] / 60)
    except: pass
    return None

def format_time(mins):
    if mins is None: return "오류"
    h, m = mins // 60, mins % 60
    return f"{h}시간 {m}분" if h > 0 else f"{m}분"

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
# 🚀 3개의 탭으로 기능 분리
# ==========================================
tab1, tab2, tab3 = st.tabs(["🗺️ 1:1 실시간 경로", "📍 다중 출발지 승부", "🔮 시간대별 타임머신"])
kst_now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)

# ------------------------------------------
# 탭 1: 기존 1:1 실시간 경로
# ------------------------------------------
with tab1:
    st.markdown("### ⚙️ 출발지/도착지 설정")
    c1, c2 = st.columns(2)
    with c1: t1_start = st.text_input("출발지", value="의정부시 신곡동", key="t1_s")
    with c2: t1_end = st.text_input("도착지", value="가산동 케이앤웍스", key="t1_e")
    
    if st.button("실시간 2파전 비교하기", type="primary", key="btn1", use_container_width=True):
        with st.spinner("경로를 탐색 중입니다..."):
            sx, sy = get_kakao_coords(t1_start)
            ex, ey = get_kakao_coords(t1_end)
            if sx and ex:
                k_dist, k_dur, k_seg = get_kakao_route(sx, sy, ex, ey)
                t_dist, t_dur, t_seg = get_tmap_route(sx, sy, ex, ey)
                
                # 결과 카드 UI
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                rc1, rc2 = st.columns(2)
                safe_end = urllib.parse.quote(t1_end)
                rc1.metric("🟡 카카오내비", format_time(k_dur), f"{k_dist} km" if k_dist else "")
                rc1.markdown(f'<a href="https://map.kakao.com/link/to/{safe_end},{ey},{sx}" target="_blank" style="display:block; text-align:center; padding:10px; background:#FEE500; color:#000; text-decoration:none; border-radius:8px; font-weight:700;">🟡 카카오 앱 열기</a>', unsafe_allow_html=True)
                rc2.metric("🔴 티맵", format_time(t_dur), f"{t_dist} km" if t_dist else "")
                rc2.markdown(f'<a href="tmap://route?goalname={safe_end}&goalx={ex}&goaly={ey}" style="display:block; text-align:center; padding:10px; background:#EF4C35; color:#FFF; text-decoration:none; border-radius:8px; font-weight:700;">🔴 티맵 앱 열기</a>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 지도 UI
                map_c1, map_c2 = st.columns(2)
                start_icon = '<div style="background:#1E90FF; color:white; border-radius:50%; width:24px; height:24px; display:flex; justify-content:center; align-items:center; font-weight:bold; font-size:12px; border:2px solid white;">S</div>'
                end_icon = '<div style="background:#FF0000; color:white; border-radius:50%; width:24px; height:24px; display:flex; justify-content:center; align-items:center; font-weight:bold; font-size:12px; border:2px solid white;">E</div>'
                tiles = "https://mt1.google.com/vt/lyrs=m&hl=ko&x={x}&y={y}&z={z}"
                
                with map_c1:
                    st.caption("🗺️ 카카오내비 상세 정체구간")
                    if k_seg:
                        coords = [c for s in k_seg for c in s['coords']]
                        m1 = folium.Map(location=coords[len(coords)//2], zoom_start=11, tiles=tiles, attr="Google")
                        folium.Marker(coords[0], icon=folium.DivIcon(html=start_icon)).add_to(m1)
                        folium.Marker(coords[-1], icon=folium.DivIcon(html=end_icon)).add_to(m1)
                        for s in k_seg: folium.PolyLine(locations=s['coords'], color=s['color'], weight=5, opacity=0.9).add_to(m1)
                        m1.fit_bounds(coords)
                        st_folium(m1, use_container_width=True, height=400, key="m1")
                with map_c2:
                    st.caption("🗺️ 티맵 최적 경로")
                    if t_seg:
                        coords = [c for s in t_seg for c in s['coords']]
                        m2 = folium.Map(location=coords[len(coords)//2], zoom_start=11, tiles=tiles, attr="Google")
                        folium.Marker(coords[0], icon=folium.DivIcon(html=start_icon)).add_to(m2)
                        folium.Marker(coords[-1], icon=folium.DivIcon(html=end_icon)).add_to(m2)
                        for s in t_seg: folium.PolyLine(locations=s['coords'], color=s['color'], weight=5, opacity=0.9).add_to(m2)
                        m2.fit_bounds(coords)
                        st_folium(m2, use_container_width=True, height=400, key="m2")
            else: st.error("주소를 찾을 수 없습니다.")

# ------------------------------------------
# 탭 2: 다중 출발지 승부 (순위 매기기)
# ------------------------------------------
with tab2:
    st.markdown("### 📍 어디서 출발하는게 가장 빠를까?")
    t2_end = st.text_input("🎯 공통 도착지", value="가산동 케이앤웍스", key="t2_e")
    st.caption("출발 후보지 (비워두면 계산에서 제외됩니다)")
    c1, c2, c3 = st.columns(3)
    with c1: t2_s1 = st.text_input("후보 1", value="의정부시 신곡동 파크프라임", key="t2_s1")
    with c2: t2_s2 = st.text_input("후보 2", placeholder="예: 구리시 인창동", key="t2_s2")
    with c3: t2_s3 = st.text_input("후보 3", placeholder="다른 출발지 입력", key="t2_s3")
    
    if st.button("출발지별 소요시간 랭킹 보기", type="primary", key="btn2", use_container_width=True):
        with st.spinner("각 출발지별 시간을 계산 중입니다..."):
            ex, ey = get_kakao_coords(t2_end)
            if not ex: st.error("도착지 주소를 확인해주세요.")
            else:
                results = []
                for name, s_addr in [("후보 1", t2_s1), ("후보 2", t2_s2), ("후보 3", t2_s3)]:
                    if s_addr.strip():
                        sx, sy = get_kakao_coords(s_addr)
                        if sx:
                            _, k_dur, _ = get_kakao_route(sx, sy, ex, ey)
                            _, t_dur, _ = get_tmap_route(sx, sy, ex, ey)
                            avg_dur = ((k_dur or 0) + (t_dur or 0)) / 2
                            results.append({"name": s_addr, "kakao": k_dur, "tmap": t_dur, "avg": avg_dur})
                
                if results:
                    # 평균 시간 기준으로 정렬
                    results = sorted(results, key=lambda x: x["avg"])
                    for i, res in enumerate(results):
                        rank = i + 1
                        badge_color = "#FF4B4B" if rank == 1 else "#555555"
                        st.markdown(f"""
                        <div class="result-card" style="{ 'border: 2px solid #FF4B4B;' if rank == 1 else '' }">
                            <span class="rank-badge" style="background:{badge_color}">현재 {rank}등</span> 
                            <strong style="font-size:16px; margin-left:8px;">{res['name']}</strong> ➔ {t2_end}
                            <div style="margin-top:10px; font-size:15px;">
                                🟡 카카오: <b>{format_time(res['kakao'])}</b> &nbsp;|&nbsp; 🔴 티맵: <b>{format_time(res['tmap'])}</b>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

# ------------------------------------------
# 탭 3: 티맵 타임머신 (미래 시간대별 예측)
# ------------------------------------------
with tab3:
    st.markdown("### 🔮 몇 시에 출발해야 안 막힐까?")
    st.info("티맵 빅데이터를 분석하여 **현재 시간부터 +3시간 뒤**까지의 교통량을 예측합니다.")
    c1, c2 = st.columns(2)
    with c1: t3_start = st.text_input("출발지", value="의정부시 신곡동", key="t3_s")
    with c2: t3_end = st.text_input("도착지", value="가산동 케이앤웍스", key="t3_e")
    
    if st.button("시간대별 예측 그래프 보기", type="primary", key="btn3", use_container_width=True):
        with st.spinner("티맵 타임머신을 가동 중입니다..."):
            sx, sy = get_kakao_coords(t3_start)
            ex, ey = get_kakao_coords(t3_end)
            if sx and ex:
                times = []
                durations = []
                labels = []
                
                # 지금, +1시간, +2시간, +3시간 계산
                for i in range(4):
                    target_time = kst_now + datetime.timedelta(hours=i)
                    time_str = target_time.strftime("%Y-%m-%dT%H:%M:%S+0900")
                    label = "지금 출발" if i == 0 else f"+{i}시간 뒤 ({target_time.strftime('%H:%M')})"
                    
                    pred_mins = get_tmap_prediction(sx, sy, ex, ey, time_str)
                    if pred_mins:
                        times.append(label)
                        durations.append(pred_mins)
                
                if durations:
                    # 보기 예쁜 막대 그래프 생성
                    chart_data = pd.DataFrame({"출발 시간대": times, "예상 소요시간(분)": durations})
                    chart_data = chart_data.set_index("출발 시간대")
                    st.bar_chart(chart_data, height=300)
                    
                    min_time = min(durations)
                    best_idx = durations.index(min_time)
                    st.success(f"💡 **가장 추천하는 시간:** {times[best_idx]}에 출발하시면 약 {format_time(min_time)}이 소요되어 가장 쾌적합니다!")
                else:
                    st.error("티맵 예측 데이터를 가져올 수 없습니다.")
            else: st.error("주소를 찾을 수 없습니다.")
