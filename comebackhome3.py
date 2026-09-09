import streamlit as st
import streamlit.components.v1 as components
import requests
import json
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
# 🎨 UI/UX 디자인
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
        padding: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 12px;
    }
    .rank-badge {
        color: white; padding: 4px 10px; border-radius: 20px; font-weight: 800; font-size: 12px; margin-right: 5px;
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
    KAKAO_JS_KEY = st.secrets.get("KAKAO_JS_KEY", "42e54a502a4ea6b063acba6bbef6ff42")
except:
    KAKAO_API_KEY = "96fc63ab0efc0a7d8591eeb8b34db8a9"
    TMAP_APP_KEY = "kstcD6L0he3GU4SSTkWNF6IHGefkURVXak3qpabh"
    KAKAO_JS_KEY = "42e54a502a4ea6b063acba6bbef6ff42"

# ==========================================
# 🗺️ [핵심] 순정 카카오 / 티맵 렌더링 함수
# ==========================================
def render_kakao_map(center_lat, center_lng, route_segments, markers, map_key=0, height=400):
    route_js = json.dumps(route_segments)
    markers_js = json.dumps(markers)
    # 🌟 질문자님이 가져오셨던 '성공 코드'의 로딩 방식(정적 태그 + setTimeout 대기)을 100% 적용했습니다!
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style> 
            html, body {{ width: 100%; height: 100%; margin: 0; padding: 0; background-color:#f8f9fa; }} 
            #map {{ width: 100%; height: 100%; display: none; }}
            #loading {{ width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; color: #888; font-size: 13px; }}
        </style>
        <script type="text/javascript" src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&autoload=false" onload="onKakaoLoaded()" onerror="onKakaoError()"></script>
    </head>
    <body>
        <!-- Map Key: {map_key} -->
        <div id="loading">카카오 지도를 불러오는 중입니다...</div>
        <div id="map"></div>
        <script>
            function onKakaoError() {{
                document.getElementById('loading').innerHTML = '<div style="color:red; font-weight:bold; text-align:center;">카카오맵 로딩 실패.<br>로컬 테스트 중이시라면 도메인에 http://localhost:8501 도 추가해주세요.</div>';
            }}
            
            function onKakaoLoaded() {{
                // 🌟 스트림릿 환경에서 kakao 객체가 완전히 초기화될 때까지 0.1초 강제 대기 (핵심 비법)
                setTimeout(function() {{
                    kakao.maps.load(function() {{
                        document.getElementById('loading').style.display = 'none';
                        var container = document.getElementById('map');
                        container.style.display = 'block';
                        
                        var options = {{ center: new kakao.maps.LatLng({center_lat}, {center_lng}), level: 7 }};
                        var map = new kakao.maps.Map(container, options);
                        var bounds = new kakao.maps.LatLngBounds();
                        var hasBounds = false;
                        
                        function createMarker(color, text) {{
                            var svg = `<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30"><circle cx="15" cy="15" r="14" fill="${{color}}" stroke="white" stroke-width="2"/><text x="15" y="20" text-anchor="middle" font-size="12" font-weight="bold" fill="white">${{text}}</text></svg>`;
                            return new kakao.maps.MarkerImage("data:image/svg+xml;charset=UTF-8," + encodeURIComponent(svg), new kakao.maps.Size(30, 30), {{offset: new kakao.maps.Point(15, 15)}});
                        }}

                        var routes = {route_js};
                        routes.forEach(function(seg) {{
                            var path = [];
                            seg.coords.forEach(function(c) {{
                                var p = new kakao.maps.LatLng(c[0], c[1]);
                                path.push(p); bounds.extend(p); hasBounds = true;
                            }});
                            if(path.length > 1) {{
                                new kakao.maps.Polyline({{ map: map, path: path, strokeWeight: 5, strokeColor: seg.color, strokeOpacity: 0.9, strokeStyle: 'solid' }});
                            }}
                        }});
                        
                        var markersData = {markers_js};
                        markersData.forEach(function(m) {{
                            var p = new kakao.maps.LatLng(m.coord[0], m.coord[1]);
                            new kakao.maps.Marker({{ position: p, map: map, image: createMarker(m.color, m.text) }});
                            bounds.extend(p); hasBounds = true;
                        }});
                        
                        if(hasBounds) {{ map.setBounds(bounds, 40, 40, 40, 40); }}
                    }});
                }}, 100);
            }}
        </script>
    </body>
    </html>
    """
    components.html(html, height=height)

def render_tmap(center_lat, center_lng, route_segments, markers, map_key=0, height=400):
    route_js = json.dumps(route_segments)
    markers_js = json.dumps(markers)
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style> html, body {{ width: 100%; height: 100%; margin: 0; padding: 0; }} </style>
        <script src="https://apis.openapi.sk.com/tmap/jsv2?version=1&appKey={TMAP_APP_KEY}"></script>
    </head>
    <body onload="initTmap()">
        <!-- Map Key: {map_key} -->
        <div id="map" style="width:100%; height:100%;"></div>
        <script>
            function initTmap() {{
                var map = new Tmapv2.Map("map", {{ center: new Tmapv2.LatLng({center_lat}, {center_lng}), zoom: 11 }});
                var bounds = new Tmapv2.LatLngBounds();
                var hasBounds = false;
                
                var routes = {route_js};
                routes.forEach(function(seg) {{
                    var path = [];
                    seg.coords.forEach(function(c) {{
                        var p = new Tmapv2.LatLng(c[0], c[1]);
                        path.push(p); bounds.extend(p); hasBounds = true;
                    }});
                    if(path.length > 1) {{
                        new Tmapv2.Polyline({{ map: map, path: path, strokeWeight: 5, strokeColor: seg.color, strokeOpacity: 0.9 }});
                    }}
                }});
                
                var markersData = {markers_js};
                markersData.forEach(function(m) {{
                    var p = new Tmapv2.LatLng(m.coord[0], m.coord[1]);
                    var svg = `<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30"><circle cx="15" cy="15" r="14" fill="${{m.color}}" stroke="white" stroke-width="2"/><text x="15" y="20" text-anchor="middle" font-size="12" font-weight="bold" fill="white">${{m.text}}</text></svg>`;
                    var iconUrl = "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(svg);
                    new Tmapv2.Marker({{ position: p, map: map, icon: iconUrl, iconSize: new Tmapv2.Size(30, 30) }});
                    bounds.extend(p); hasBounds = true;
                }});
                
                if(hasBounds) {{ map.fitBounds(bounds); }}
            }}
        </script>
    </body>
    </html>
    """
    components.html(html, height=height)

# ==========================================
# 🛠️ 길찾기 API 통신 함수 모음
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
                color = solid_color if solid_color else {1:"#FF0000", 2:"#FF8C00", 3:"#FFD700", 4:"#008000"}.get(road.get('traffic_state', 0), "#1E90FF")
                coords = [[road['vertexes'][i+1], road['vertexes'][i]] for i in range(0, len(road['vertexes']), 2)]
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
    url = "https://apis.openapi.sk.com/tmap/routes/prediction?version=1&reqCoordType=WGS84GEO&resCoordType=WGS84GEO"
    headers = {"appKey": TMAP_APP_KEY, "Content-Type": "application/json"}
    payload = {
        "routesInfo": {
            "departure": {"name": "출발지", "lon": str(start_x), "lat": str(start_y)},
            "destination": {"name": "도착지", "lon": str(end_x), "lat": str(end_y)},
            "predictionType": "departure", "predictionTime": time_str
        }
    }
    try:
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code != 200: return None, f"티맵 에러 (코드: {res.status_code})"
        data = res.json()
        if 'features' in data: return round(data['features'][0]['properties']['totalTime'] / 60), ""
        else: return None, str(data)
    except Exception as e: return None, str(e)

def format_time(mins):
    if mins is None: return "오류"
    h, m = mins // 60, mins % 60
    return f"{h}시간 {m}분" if h > 0 else f"{m}분"

# ==========================================
# 🌟 세션 초기화
# ==========================================
kst_now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)

if "t1_res" not in st.session_state: st.session_state.t1_res = None
if "t2_res" not in st.session_state: st.session_state.t2_res = None
if "t3_res" not in st.session_state: st.session_state.t3_res = None
if "map_key" not in st.session_state: st.session_state.map_key = 0 
if "custom_h" not in st.session_state: st.session_state.custom_h = 5
if "custom_m" not in st.session_state: st.session_state.custom_m = 0
if "prev_r3" not in st.session_state: st.session_state.prev_r3 = "1️⃣ 출근길 (집 ➔ 회사)"

# ==========================================
# 🖥️ 사이드바
# ==========================================
with st.sidebar:
    st.markdown("### 🚘 내 차 이미지")
    uploaded_img = st.file_uploader("사진 업로드", type=["jpg", "jpeg", "png"])
b64_encoded = base64.b64encode(uploaded_img.read()).decode() if uploaded_img else (base64.b64encode(open("mycar.jpg", "rb").read()).decode() if os.path.exists("mycar.jpg") else "")

if b64_encoded:
    st.markdown(f'<div style="display:flex; align-items:center; margin-bottom:15px;"><img src="data:image/jpeg;base64,{b64_encoded}" style="width:60px; height:60px; border-radius:12px; object-fit:cover; margin-right:15px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);"><h1 style="margin:0;">나만의 내비게이션 Pro</h1></div>', unsafe_allow_html=True)
else:
    st.title("🚗 나만의 내비게이션 Pro")

# ==========================================
# ⚙️ 기본 주소 설정
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
# 🚀 3개의 탭 기능 분리
# ==========================================
tab1, tab2, tab3 = st.tabs(["🗺️ 1:1 실시간 경로", "📍 다중 출발지 승부", "🔮 시간대별 타임머신"])

# ------------------------------------------
# 탭 1: 기존 1:1 실시간 경로
# ------------------------------------------
with tab1:
    route_choice1 = st.radio("🚗 조회할 경로 선택", ["1️⃣ 출근길 (집 ➔ 회사)", "2️⃣ 퇴근길 (회사 ➔ 집)", "3️⃣ 직접 설정"], index=0 if kst_now.hour < 12 else 1, horizontal=True, key="r1")
    
    is_custom1 = False
    if route_choice1.startswith("1️⃣"): start_target1, end_target1 = home_address, work_address
    elif route_choice1.startswith("2️⃣"): start_target1, end_target1 = work_address, home_address
    else:
        is_custom1 = True
        start_target1, end_target1 = "", ""

    if is_custom1:
        ct1, ct2 = st.columns(2)
        with ct1: start_target1 = st.text_input("출발지 직접 입력", placeholder="출발지를 입력하세요", key="st1")
        with ct2: end_target1 = st.text_input("도착지 직접 입력", placeholder="도착지를 입력하세요", key="et1")
    else:
        st.info(f"📍 **현재 선택된 경로:** {start_target1 if start_target1 else '(집 미입력)'} ➔ {end_target1 if end_target1 else '(회사 미입력)'}")

    if st.button("실시간 2파전 비교하기", type="primary", key="btn1", use_container_width=True):
        if not start_target1 or not end_target1:
            st.warning("출발지와 도착지를 모두 정확히 설정해 주세요.")
        else:
            with st.spinner("경로를 탐색 중입니다..."):
                sx, sy = get_kakao_coords(start_target1)
                ex, ey = get_kakao_coords(end_target1)
                if sx and ex:
                    k_dist, k_dur, k_seg = get_kakao_route(sx, sy, ex, ey)
                    t_dist, t_dur, t_seg = get_tmap_route(sx, sy, ex, ey)
                    st.session_state.t1_res = {
                        "k_dist": k_dist, "k_dur": k_dur, "k_seg": k_seg,
                        "t_dist": t_dist, "t_dur": t_dur, "t_seg": t_seg,
                        "end_target": end_target1, "ex": ex, "ey": ey, "sx": sx, "sy": sy
                    }
                else:
                    st.error("주소를 찾을 수 없습니다.")

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
        
        if st.button("🔄 지도 정위치로 되돌리기", key="reset_map_1", use_container_width=True):
            st.session_state.map_key += 1
            
        map_c1, map_c2 = st.columns(2)
        markers = [
            {"coord": [res["sy"], res["sx"]], "color": "#1E90FF", "text": "S"},
            {"coord": [res["ey"], res["ex"]], "color": "#FF0000", "text": "E"}
        ]
        
        with map_c1:
            st.caption("🗺️ 카카오내비 최적 경로 (순정 카카오맵)")
            render_kakao_map(res["ey"], res["ex"], res["k_seg"], markers, map_key=st.session_state.map_key, height=400)
        with map_c2:
            st.caption("🗺️ 티맵 최적 경로 (순정 티맵)")
            render_tmap(res["ey"], res["ex"], res["t_seg"], markers, map_key=st.session_state.map_key, height=400)

# ------------------------------------------
# 탭 2: 다중 출발지 승부
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
                            _, k_dur, k_seg = get_kakao_route(sx, sy, ex, ey)
                            _, t_dur, _ = get_tmap_route(sx, sy, ex, ey)
                            avg_dur = ((k_dur or 0) + (t_dur or 0)) / 2
                            results.append({
                                "name": s_addr, "sx":sx, "sy":sy, 
                                "kakao": k_dur, "tmap": t_dur, "avg": avg_dur, "k_seg": k_seg
                            })
                
                if results:
                    results = sorted(results, key=lambda x: x["avg"])
                    colors = ["#FF4B4B", "#1E90FF", "#03C75A"]
                    for i, res in enumerate(results):
                        res["rank"] = i + 1
                        res["color"] = colors[i] if i < len(colors) else "#555555"
                    
                    st.session_state.t2_res = {"results": results, "ex": ex, "ey": ey}
    
    if st.session_state.t2_res:
        res_data = st.session_state.t2_res
        results = res_data["results"]
        ex, ey = res_data["ex"], res_data["ey"]
        
        c_left, c_right = st.columns([1, 3])
        
        with c_left:
            st.markdown("#### 🏆 순위 결과")
            for res in results:
                rank, badge_color = res["rank"], res["color"]
                st.markdown(f"""
                <div class="result-card" style="border-left: 5px solid {badge_color}; padding: 12px;">
                    <div style="margin-bottom: 5px;">
                        <span class="rank-badge" style="background:{badge_color}; padding: 3px 8px;">{rank}등</span>
                        <strong style="font-size: 14px;">{res['name']}</strong>
                    </div>
                    <div style="font-size: 13px; color: #333; margin-left:2px;">
                        🟡 카카오: <b>{format_time(res['kakao'])}</b> <br> 🔴 티맵: <b>{format_time(res['tmap'])}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        with c_right:
            c_title, c_btn = st.columns([1, 1])
            with c_title: st.markdown("#### 🗺️ 1~3등 전체 비교 지도")
            with c_btn:
                if st.button("🔄 전체 지도 정위치", key="reset_map_2", use_container_width=True):
                    st.session_state.map_key += 1

            markers = [{"coord": [ey, ex], "color": "#000000", "text": "E"}]
            all_k_segs = []
            for res in results:
                markers.append({"coord": [res["sy"], res["sx"]], "color": res["color"], "text": f"{res['rank']}등"})
                if res["k_seg"]:
                    for s in res["k_seg"]: s["color"] = res["color"]
                    all_k_segs.extend(res["k_seg"])
                    
            render_kakao_map(ey, ex, all_k_segs, markers, map_key=st.session_state.map_key, height=450)

        st.markdown("<hr style='margin: 20px 0 10px 0;'>", unsafe_allow_html=True)
        st.markdown("#### 🔍 후보지별 개별 상세 경로")
        
        indiv_cols = st.columns(len(results))
        for i, res in enumerate(results):
            with indiv_cols[i]:
                st.markdown(f"**[{res['rank']}등]** {res['name']} 출발")
                mks = [
                    {"coord": [ey, ex], "color": "#000000", "text": "E"},
                    {"coord": [res["sy"], res["sx"]], "color": "#1E90FF", "text": "S"}
                ]
                _, _, fresh_seg = get_kakao_route(res["sx"], res["sy"], ex, ey)
                render_kakao_map(ey, ex, fresh_seg, mks, map_key=f"{st.session_state.map_key}_{i}", height=300)

# ------------------------------------------
# 탭 3: 티맵 타임머신
# ------------------------------------------
with tab3:
    st.markdown("### 🔮 몇 시에 출발해야 안 막힐까?")
    st.info("티맵 빅데이터를 분석하여 **현재 시간부터 +3시간 뒤** 및 **지정된 스케줄**의 교통량을 동시에 예측합니다.")
    
    route_choice3 = st.radio("🚗 타임머신 경로 선택", ["1️⃣ 출근길 (집 ➔ 회사)", "2️⃣ 퇴근길 (회사 ➔ 집)", "3️⃣ 직접 설정"], index=0 if kst_now.hour < 12 else 1, horizontal=True, key="r3")
    
    if st.session_state.prev_r3 != route_choice3:
        st.session_state.prev_r3 = route_choice3
        if route_choice3.startswith("1️⃣"): 
            st.session_state.custom_h, st.session_state.custom_m = 5, 0
        elif route_choice3.startswith("2️⃣"): 
            st.session_state.custom_h, st.session_state.custom_m = 17, 30
        else:
            st.session_state.custom_h, st.session_state.custom_m = kst_now.hour, (kst_now.minute // 10) * 10

    is_custom3 = False
    if route_choice3.startswith("1️⃣"): start_target3, end_target3 = home_address, work_address
    elif route_choice3.startswith("2️⃣"): start_target3, end_target3 = work_address, home_address
    else:
        is_custom3 = True
        start_target3, end_target3 = "", ""

    if is_custom3:
        ct3, ct4 = st.columns(2)
        with ct3: start_target3 = st.text_input("출발지 직접 입력", placeholder="출발지를 입력하세요", key="st3")
        with ct4: end_target3 = st.text_input("도착지 직접 입력", placeholder="도착지를 입력하세요", key="et3")
    else:
        st.info(f"📍 **예측 경로:** {start_target3 if start_target3 else '(집 미입력)'} ➔ {end_target3 if end_target3 else '(회사 미입력)'}")

    if st.button("시간대별 일괄 예측 조회하기", type="primary", key="btn3", use_container_width=True):
        if not start_target3 or not end_target3:
            st.warning("출발지와 도착지를 모두 정확히 설정해 주세요.")
        else:
            with st.spinner("티맵 타임머신을 가동 중입니다... (약 5초 소요)"):
                sx, sy = get_kakao_coords(start_target3)
                ex, ey = get_kakao_coords(end_target3)
                if sx and ex:
                    times, durations = [], []
                    err_log = ""
                    
                    _, _, k_seg = get_kakao_route(sx, sy, ex, ey)
                    _, _, t_seg = get_tmap_route(sx, sy, ex, ey)
                    
                    for i in range(4):
                        target_time = kst_now + datetime.timedelta(hours=i)
                        time_str = target_time.strftime("%Y-%m-%dT%H:%M:%S+0900") 
                        label = "지금 출발 🚀" if i == 0 else f"+{i}시간 뒤 ({target_time.strftime('%H:%M')})"
                        
                        pred_mins, err = get_tmap_prediction(sx, sy, ex, ey, time_str)
                        if pred_mins:
                            times.append(label)
                            durations.append(pred_mins)
                        if err: err_log = err
                    
                    st.session_state.t3_res = {
                        "sx": sx, "sy": sy, "ex": ex, "ey": ey,
                        "k_seg": k_seg, "t_seg": t_seg,
                        "times": times, "durations": durations, "err": err_log
                    }
                else: 
                    st.error("주소를 찾을 수 없습니다.")
                
    if st.session_state.t3_res:
        res = st.session_state.t3_res
        if res["durations"]:
            min_time = min(res["durations"])
            best_idx = res["durations"].index(min_time)
            
            st.success(f"💡 **가장 쾌적한 추천 시간:** {res['times'][best_idx]}에 출발하시면 약 {format_time(min_time)}이 소요됩니다!")
            st.markdown("#### ⏳ 시간대별 흐름 & 내 스케줄 비교")
            
            cols = st.columns(5)
            for i, (label, mins) in enumerate(zip(res["times"], res["durations"])):
                is_best = (i == best_idx)
                bg_color = "#FFF4F4" if is_best else "#F8F9FA"
                border_color = "#FF4B4B" if is_best else "#EAEAEA"
                badge = '<div style="background:#FF4B4B; color:white; font-size:12px; font-weight:bold; border-radius:20px; padding:3px 10px; display:inline-block; margin-bottom:15px;">🏆 최적 추천</div>' if is_best else '<div style="height:26px; margin-bottom:15px;"></div>'

                card_html = f"""
                <div style="background:{bg_color}; border:2px solid {border_color}; border-radius:12px; padding:15px 5px; text-align:center; height: 165px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                    {badge}
                    <div style="font-size:13px; color:#555; margin-bottom:10px; font-weight:600;">{label}</div>
                    <div style="font-size:22px; font-weight:800; color:#111;">{format_time(mins)}</div>
                </div>
                """
                cols[i].markdown(card_html, unsafe_allow_html=True)
                
            with cols[4]:
                st.markdown("<div style='text-align:center; font-weight:bold; color:#1E90FF; margin-bottom:0px; font-size:13px; height: 26px; line-height: 26px;'>⏰ 스케줄 조절 (10분 단위)</div>", unsafe_allow_html=True)
                
                time_options = [f"{h:02d}:{m:02d}" for h in range(24) for m in range(0, 60, 10)]
                default_time_str = f"{st.session_state.custom_h:02d}:{st.session_state.custom_m:02d}"
                if default_time_str not in time_options:
                    time_options.append(default_time_str)
                    time_options.sort()
                    
                selected_time = st.selectbox("시간", time_options, index=time_options.index(default_time_str), label_visibility="collapsed")
                sel_h, sel_m = map(int, selected_time.split(":"))
                st.session_state.custom_h = sel_h
                st.session_state.custom_m = sel_m
                
                target_dt = kst_now.replace(hour=sel_h, minute=sel_m, second=0, microsecond=0)
                if kst_now > target_dt: target_dt += datetime.timedelta(days=1)
                custom_time_str = target_dt.strftime("%Y-%m-%dT%H:%M:%S+0900")
                
                with st.spinner("⏳ 갱신 중..."):
                    c_mins, _ = get_tmap_prediction(res["sx"], res["sy"], res["ex"], res["ey"], custom_time_str)
                
                if c_mins:
                    st.markdown(f"""
                    <div style="background:#E8F0FE; border:2px solid #1E90FF; border-radius:12px; padding:15px 5px; text-align:center; height: 95px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top:2px;">
                        <div style="font-size:12px; color:#1E90FF; margin-bottom:5px; font-weight:600;">{target_dt.strftime('%m/%d')} 예상 소요시간</div>
                        <div style="font-size:22px; font-weight:800; color:#111;">{format_time(c_mins)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else: st.error("예측 실패")
                
            st.markdown("<hr style='margin: 20px 0 10px 0;'>", unsafe_allow_html=True)
            c_title, c_btn = st.columns([1, 1])
            with c_title: st.markdown("#### 🗺️ 예측 기준 경로 (실시간)")
            with c_btn:
                if st.button("🔄 기준 지도 정위치", key="reset_map_3", use_container_width=True):
                    st.session_state.map_key += 1
                    
            map_c1, map_c2 = st.columns(2)
            markers = [
                {"coord": [res["sy"], res["sx"]], "color": "#1E90FF", "text": "S"},
                {"coord": [res["ey"], res["ex"]], "color": "#FF0000", "text": "E"}
            ]
            
            with map_c1:
                st.caption("🗺️ 카카오내비 기준 경로 (순정 카카오맵)")
                if res.get("k_seg"):
                    render_kakao_map(res["ey"], res["ex"], res["k_seg"], markers, map_key=st.session_state.map_key, height=350)
            with map_c2:
                st.caption("🗺️ 티맵 기준 경로 (순정 티맵)")
                if res.get("t_seg"):
                    render_tmap(res["ey"], res["ex"], res["t_seg"], markers, map_key=st.session_state.map_key, height=350)
        else:
            st.error(f"티맵 예측 데이터를 가져올 수 없습니다. (에러: {res['err']})")
