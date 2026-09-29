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
# 🎨 UI/UX 디자인 (폰트 깨짐 완벽 해결)
# ==========================================
custom_css = """
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

    :root {
        --bg-page: #2b2f3b;
        --bg-card: #383d4b;
        --bg-card-hover: #434958;
        --border-card: #4d5364;
        --text-main: #e8e9ed;
        --text-muted: #9aa0ad;
    }

    /* 🌙 전체 다크 테마 배경 */
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: var(--bg-page) !important;
    }
    
    /* 기존에 span, div 등을 전부 덮어씌워서 아이콘이 깨지던 문제를 해결했습니다.
       + Material 아이콘 텍스트(예: expand_more, keyboard_double_arrow_right)가
       하필 p/label 안에 들어있는 경우까지 대비해, 아이콘 전용 폰트를
       fallback으로 같이 넣어 어떤 태그 안에 있어도 깨지지 않도록 처리 */
    html, body, p, label, h1, h2, h3, h4, h5, h6, strong, b, li { 
        font-family: 'Pretendard', 'Material Symbols Rounded', sans-serif !important; 
        color: var(--text-main) !important;
    }
    
    /* 🔧 "⚙️ 앱 설정" 팝오버 버튼의 펼치기 화살표 아이콘이 텍스트(expand_more)로
       깨져 보이는 문제 수정. 이 아이콘은 알파벳으로만 이뤄져 있어서 폰트
       fallback으로는 해결이 안 되므로, 텍스트를 숨기고 화살표를 직접 그려 넣음 */
    [data-testid="stPopover"] [data-testid="stIconMaterial"] {
        font-size: 0 !important;
    }
    [data-testid="stPopover"] [data-testid="stIconMaterial"]::after {
        content: "▾";
        font-family: sans-serif !important;
        font-size: 16px !important;
        color: inherit !important;
    }
    h3 { font-size: 18px !important; font-weight: 700 !important; }

    /* 🌙 컴팩트한 pill 스타일 검색창 */
    .stTextInput input, .stNumberInput input {
        height: 40px !important;
        border-radius: 20px !important;
        padding: 0 16px !important;
        background-color: var(--bg-card) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border-card) !important;
        font-size: 14px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #FEE500 !important;
        box-shadow: 0 0 0 2px rgba(254,229,0,0.2) !important;
    }
    .stTextInput label, .stSelectbox label, .stNumberInput label {
        font-size: 12px !important; color: var(--text-muted) !important;
        margin-bottom: 2px !important;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: var(--bg-card) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border-card) !important;
        border-radius: 20px !important;
        min-height: 40px !important;
    }
    [data-baseweb="popover"] li, [data-baseweb="menu"] li {
        background-color: var(--bg-card) !important;
        color: var(--text-main) !important;
    }

    /* 🌙 st.info / st.warning / st.success 알림 박스 다크화 */
    [data-testid="stAlert"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-card) !important;
        border-radius: 12px !important;
    }
    [data-testid="stAlert"] p { color: var(--text-main) !important; }

    /* 🌙 위젯 사이 여백을 좁혀서 전체적으로 더 컴팩트하게 */
    [data-testid="stVerticalBlock"] { gap: 0.6rem !important; }
    .element-container { margin-bottom: 0 !important; }

    /* 🌙 가로 라디오를 세그먼트 탭(pill) 스타일로 — 기본 원형 라디오 숨기고 라벨을 버튼처럼 */
    div[role="radiogroup"] { gap: 6px !important; }
    div[role="radiogroup"] label {
        background: var(--bg-card) !important; border: 1px solid var(--border-card) !important;
        border-radius: 18px !important; padding: 6px 14px !important; margin: 0 !important;
        transition: 0.15s;
    }
    div[role="radiogroup"] label:has(input:checked) {
        background: #FEE500 !important; border-color: #FEE500 !important;
    }
    div[role="radiogroup"] label:has(input:checked) p { color: #191919 !important; font-weight: 700 !important; }
    div[role="radiogroup"] label > div:first-child { display: none !important; }

    div.stButton > button {
        border-radius: 20px !important;
        height: 40px !important;
    }
    div.stButton > button[kind="primary"] {
        background-color: #FEE500 !important;
        font-weight: 800 !important;
        box-shadow: 0 4px 10px rgba(254,229,0,0.15) !important;
        border: none !important; transition: 0.2s;
    }
    /* 전역 "p { color: var(--text-main) }" 규칙이 버튼 안쪽 <p>에도 직접 걸려서
       버튼 자체의 색 지정보다 우선 적용되는 바람에 노란 배경에 흰 글씨로 보이던 문제.
       버튼 안 <p>를 직접 지정해서 확실히 덮어씀 */
    div.stButton > button[kind="primary"] p,
    div.stButton > button[kind="primary"] div {
        color: #191919 !important;
    }
    div.stButton > button[kind="primary"]:hover { transform: translateY(-2px) !important; }
    div.stButton > button[kind="secondary"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-card) !important;
    }
    div.stButton > button[kind="secondary"] p,
    div.stButton > button[kind="secondary"] div {
        color: var(--text-main) !important;
    }

    .result-card {
        background: var(--bg-card); border: 1px solid var(--border-card); border-radius: 12px;
        padding: 15px; margin-bottom: 12px;
    }
    .rank-badge {
        color: white; padding: 4px 10px; border-radius: 20px; font-weight: 800; font-size: 12px; margin-right: 5px;
    }

    /* 🏆 4사 비교 스코어보드에서 아이디어를 가져온 결과 카드 스타일 */
    .scoreboard-card {
        background: var(--bg-card); border: 2px solid var(--border-card); border-radius: 14px;
        padding: 16px; text-align: center; position: relative; transition: 0.2s;
    }
    .scoreboard-card.is-winner { border-color: #22C55E; box-shadow: 0 0 0 1px #22C55E inset; }
    .provider-badge {
        display: inline-flex; align-items: center; justify-content: center;
        width: 22px; height: 22px; border-radius: 6px; color: white;
        font-size: 12px; font-weight: 800; margin-right: 6px;
    }
    .provider-badge.badge-k { color: #191919; }
    .winner-pill {
        background: #22C55E; color: #06210f; font-size: 11px; font-weight: 800;
        border-radius: 12px; padding: 2px 9px; margin-left: 6px;
    }
    .scoreboard-time { font-size: 26px; font-weight: 800; color: var(--text-main); margin: 4px 0 2px 0; }
    .scoreboard-dist { font-size: 13px; color: var(--text-muted); margin-bottom: 10px; }
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
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <!-- 🌟 실수로 누락되었던 마법의 보안 차단 해제 태그 완벽 복구!! -->
        <meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
        <style> 
            html, body {{ width: 100%; height: 100%; margin: 0; padding: 0; background-color:#f8f9fa; }} 
            #mapWrap {{ position: relative; width: 100%; height: 100%; }}
            #map {{ width: 100%; height: 100%; display: none; }}
            #loading {{ width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; color: #888; font-size: 13px; text-align: center; line-height: 1.5; }}
            #clickGuard {{
                position: absolute; inset: 0; z-index: 10;
                display: flex; align-items: center; justify-content: center;
                background: rgba(0,0,0,0.12); color: #fff; font-size: 12px; font-weight: 600;
                cursor: pointer; text-align: center; padding: 0 12px;
            }}
        </style>
    </head>
    <body>
        <!-- Map Key: {map_key} -->
        <div id="loading">카카오 지도를 불러오는 중입니다...</div>
        <div id="mapWrap">
            <div id="map"></div>
            <div id="clickGuard">🖱️ 클릭하면 지도를 움직일 수 있어요</div>
        </div>
        <script>
            function initKakaoMap() {{
                kakao.maps.load(function() {{
                    document.getElementById('loading').style.display = 'none';
                    var container = document.getElementById('map');
                    container.style.display = 'block';
                    
                    var options = {{ center: new kakao.maps.LatLng({center_lat}, {center_lng}), level: 7 }};
                    var map = new kakao.maps.Map(container, options);
                    map.setDraggable(false);
                    var guard = document.getElementById('clickGuard');
                    guard.addEventListener('click', function() {{
                        map.setDraggable(true);
                        guard.style.display = 'none';
                    }});
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
            }}

            var script = document.createElement('script');
            script.type = 'text/javascript';
            script.src = "https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&autoload=false";
            script.onload = function() {{
                setTimeout(initKakaoMap, 100);
            }};
            script.onerror = function() {{
                document.getElementById('loading').innerHTML = '<span style="color:red; font-weight:bold;">카카오맵 로딩 실패.<br>로컬 테스트 중이시라면 도메인에 http://localhost:8501 도 추가해주세요.</span>';
            }};
            document.head.appendChild(script);
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
        <!-- 🌟 티맵에도 혹시 모를 차단을 막기 위해 동일한 보안 태그를 추가했습니다. -->
        <meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
        <style>
            html, body {{ width: 100%; height: 100%; margin: 0; padding: 0; overflow: hidden; }}
            #mapWrap {{ position: relative; width: 100%; height: 100%; }}
            #map {{ width: 100%; height: 100%; }}
            #clickGuard {{
                position: absolute; inset: 0; z-index: 10;
                display: flex; align-items: center; justify-content: center;
                background: rgba(0,0,0,0.12); color: #fff; font-size: 12px; font-weight: 600;
                cursor: pointer; text-align: center; padding: 0 12px;
            }}
        </style>
        <script src="https://apis.openapi.sk.com/tmap/jsv2?version=1&appKey={TMAP_APP_KEY}"></script>
    </head>
    <body onload="initTmap()">
        <!-- Map Key: {map_key} -->
        <div id="mapWrap">
            <div id="map" style="width:100%; height:100%;"></div>
            <div id="clickGuard">🖱️ 클릭하면 지도를 움직일 수 있어요</div>
        </div>
        <script>
            function initTmap() {{
                var map = new Tmapv2.Map("map", {{ center: new Tmapv2.LatLng({center_lat}, {center_lng}), zoom: 11 }});
                try {{ map.setDraggable(false); }} catch (e) {{ /* SDK 버전에 따라 메서드가 없을 수 있음 */ }}
                var guard = document.getElementById('clickGuard');
                guard.addEventListener('click', function() {{
                    try {{ map.setDraggable(true); }} catch (e) {{}}
                    guard.style.display = 'none';
                }});
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

def search_kakao_places(query):
    """검색어에 대한 후보 목록(최대 5개)을 반환. 사용자가 그중 하나를 고를 수 있게 하기 위함."""
    if not query or not query.strip():
        return []
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    for url in ["https://dapi.kakao.com/v2/local/search/keyword.json", "https://dapi.kakao.com/v2/local/search/address.json"]:
        try:
            res = requests.get(url, headers=headers, params={"query": query, "size": 5}).json()
        except Exception:
            continue
        docs = res.get('documents', [])
        if docs:
            candidates = []
            for d in docs:
                name = d.get('place_name') or d.get('address_name', query)
                addr = d.get('road_address_name') or d.get('address_name', '')
                label = f"{name} ({addr})" if addr and addr != name else name
                candidates.append({"label": label, "x": d['x'], "y": d['y']})
            return candidates
    return []

def get_kakao_route(start_x, start_y, end_x, end_y, waypoints=None, priority="RECOMMEND", solid_color=None):
    url = "https://apis-navi.kakaomobility.com/v1/directions"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"origin": f"{start_x},{start_y}", "destination": f"{end_x},{end_y}", "priority": priority}
    if waypoints:
        # 카카오모빌리티 길찾기는 경유지를 최대 5개까지, "lng,lat|lng,lat" 형식으로 지원
        params["waypoints"] = "|".join([f"{wx},{wy}" for wx, wy, _ in waypoints[:5]])
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

def get_tmap_route(start_x, start_y, end_x, end_y, waypoints=None, search_option="0"):
    url = "https://apis.openapi.sk.com/tmap/routes?version=1&format=json"
    headers = {"appKey": TMAP_APP_KEY, "Content-Type": "application/json"}
    payload = {"startX": str(start_x), "startY": str(start_y), "endX": str(end_x), "endY": str(end_y),
               "startName": "S", "endName": "E", "reqCoordType": "WGS84GEO", "resCoordType": "WGS84GEO",
               "searchOption": search_option}
    if waypoints:
        # 티맵 경유지(passList)는 "lng,lat_lng,lat" 형식 (구간은 밑줄로 구분)
        payload["passList"] = "_".join([f"{wx},{wy}" for wx, wy, _ in waypoints[:5]])
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
# 💾 경로 프리셋 저장/불러오기
# (같은 서버 인스턴스 안에서는 유지되지만, Streamlit Cloud 재배포 시 초기화될 수 있음)
# ==========================================
PRESET_FILE = "route_presets.json"

def load_presets():
    if os.path.exists(PRESET_FILE):
        try:
            with open(PRESET_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_presets(presets):
    try:
        with open(PRESET_FILE, "w", encoding="utf-8") as f:
            json.dump(presets, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def apply_preset_to_session(preset):
    """저장된 프리셋 값을 address_picker가 쓰는 session_state 키에 직접 주입"""
    def set_addr(key, label, x, y):
        st.session_state[f"{key}_query"] = label
        st.session_state[f"{key}_prev_query"] = label
        st.session_state[f"{key}_candidates"] = [{"label": label, "x": x, "y": y}]
        st.session_state[f"{key}_pick"] = label

    set_addr("t1_start", preset["start_label"], preset["start_x"], preset["start_y"])
    set_addr("t1_end", preset["end_label"], preset["end_x"], preset["end_y"])

    waypoints = preset.get("waypoints", [])
    st.session_state.t1_wp_count = len(waypoints)
    for i, wp in enumerate(waypoints):
        set_addr(f"t1_wp{i}", wp["label"], wp["x"], wp["y"])

    if preset.get("route_option"):
        st.session_state.t1_route_option = preset["route_option"]

def address_picker(label, key, default_query=""):
    """
    주소를 입력받아 검색하고, 검색 결과 후보 중 사용자가 직접 선택하게 하는 UI.
    별도 '검색' 버튼 없이, 입력값이 바뀌면(엔터/포커스 아웃 시) 자동으로 검색됨.
    반환값: (x, y, 선택된 라벨) — 아직 선택 전이면 (None, None, None)
    """
    query = st.text_input(label, value=default_query, key=f"{key}_query")
    prev_query_key = f"{key}_prev_query"

    if query and query != st.session_state.get(prev_query_key):
        st.session_state[prev_query_key] = query
        st.session_state[f"{key}_candidates"] = search_kakao_places(query)

    candidates = st.session_state.get(f"{key}_candidates", [])
    if candidates:
        options = [c["label"] for c in candidates]
        picked_label = st.selectbox(f"{label} 검색결과 중 선택", options, key=f"{key}_pick")
        chosen = candidates[options.index(picked_label)]
        return chosen["x"], chosen["y"], picked_label
    return None, None, None

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
# 🖥️ 상단 헤더 (타이틀 + 우측 앱 설정 팝업)
# ==========================================
header_col1, header_col2 = st.columns([4, 1])

with header_col1:
    if "uploaded_img" in st.session_state and st.session_state.uploaded_img:
        b64_encoded = base64.b64encode(st.session_state.uploaded_img.read()).decode()
        st.session_state.uploaded_img.seek(0)
    else:
        b64_encoded = base64.b64encode(open("mycar.jpg", "rb").read()).decode() if os.path.exists("mycar.jpg") else ""

    if b64_encoded:
        st.markdown(f'<div style="display:flex; align-items:center; margin-bottom:15px;"><img src="data:image/jpeg;base64,{b64_encoded}" style="width:60px; height:60px; border-radius:12px; object-fit:cover; margin-right:15px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);"><h1 style="margin:0;">나만의 내비게이션 Pro</h1></div>', unsafe_allow_html=True)
    else:
        st.title("🚗 나만의 내비게이션 Pro")

with header_col2:
    st.markdown("<div style='text-align: right; padding-top: 10px;'>", unsafe_allow_html=True)
    with st.popover("⚙️ 앱 설정", use_container_width=True):
        st.markdown("**🚘 내 차 이미지 변경**")
        new_img = st.file_uploader("사진 업로드", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        if new_img:
            st.session_state.uploaded_img = new_img
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 📌 메뉴 선택 (상단 가로 배치 - 모바일에서 사이드바를 열 필요가 없도록)
# ==========================================
menu_selection = st.radio(
    "이동할 메뉴를 선택하세요",
    ["🗺️ 1:1 실시간 경로", "📍 다중 출발지 승부", "🔮 시간대별 타임머신"],
    horizontal=True,
    label_visibility="collapsed"
)

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
# 🚀 메뉴별 화면 라우팅
# ==========================================

# ------------------------------------------
# 메뉴 1: 1:1 실시간 경로
# ------------------------------------------
if menu_selection == "🗺️ 1:1 실시간 경로":
    route_choice1 = st.radio("🚗 조회할 경로 선택", ["1️⃣ 출근길 (집 ➔ 회사)", "2️⃣ 퇴근길 (회사 ➔ 집)", "3️⃣ 직접 설정"], index=0 if kst_now.hour < 12 else 1, horizontal=True, key="r1")

    if route_choice1.startswith("1️⃣"): default_start, default_end = home_address, work_address
    elif route_choice1.startswith("2️⃣"): default_start, default_end = work_address, home_address
    else: default_start, default_end = "", ""

    # 출근길/퇴근길/직접설정 전환 시, 이전 검색 상태를 초기화해서 새 기본값으로 다시 검색되게 함
    if st.session_state.get("t1_prev_route_choice") != route_choice1:
        st.session_state.t1_prev_route_choice = route_choice1
        for k in ["t1_start", "t1_end"]:
            for suffix in ["_query", "_prev_query", "_candidates", "_pick"]:
                st.session_state.pop(f"{k}{suffix}", None)

    # --- ① 검색 결과 중 선택해서 출발/도착지 설정 (입력 후 엔터 치면 자동 검색) ---
    st.markdown("#### 📍 출발지 · 도착지")
    ct1, ct2 = st.columns(2)
    with ct1:
        sx, sy, start_label = address_picker("출발지", key="t1_start", default_query=default_start)
    with ct2:
        ex, ey, end_label = address_picker("도착지", key="t1_end", default_query=default_end)

    # --- ② 경유지 설정 ---
    st.markdown("#### 🚩 경유지 (선택, 최대 3곳)")
    if "t1_wp_count" not in st.session_state: st.session_state.t1_wp_count = 0
    wcol1, wcol2, _ = st.columns([1, 1, 4])
    with wcol1:
        if st.button("➕ 경유지 추가", key="t1_wp_add", use_container_width=True):
            if st.session_state.t1_wp_count < 3:
                st.session_state.t1_wp_count += 1
    with wcol2:
        if st.button("➖ 경유지 삭제", key="t1_wp_del", use_container_width=True):
            if st.session_state.t1_wp_count > 0:
                st.session_state.t1_wp_count -= 1

    waypoints1 = []
    for i in range(st.session_state.t1_wp_count):
        wx, wy, wlabel = address_picker(f"경유지 {i+1}", key=f"t1_wp{i}")
        if wx and wy:
            waypoints1.append((wx, wy, wlabel))

    # --- ③ 경로 옵션 선택 ---
    st.markdown("#### ⚙️ 경로 탐색 옵션")
    route_option1 = st.radio(
        "탐색 옵션", ["추천 경로", "최소시간", "최단거리"],
        horizontal=True, key="t1_route_option", label_visibility="collapsed"
    )
    kakao_priority_map = {"추천 경로": "RECOMMEND", "최소시간": "TIME", "최단거리": "DISTANCE"}
    tmap_option_map = {"추천 경로": "0", "최소시간": "2", "최단거리": "10"}

    if start_label and end_label:
        route_lines = [f"🔵 출발: **{start_label}**"]
        for i, (_, _, wlabel) in enumerate(waypoints1):
            route_lines.append(f"🚩 경유 {i+1}: **{wlabel.split(' (')[0]}**")
        route_lines.append(f"🔴 도착: **{end_label}**")
        st.info("📍 **현재 선택된 경로**\n\n" + "\n\n".join(route_lines))
    else:
        st.warning("출발지와 도착지를 검색해서 선택해주세요.")

    # --- 💾 경로 프리셋 저장/불러오기 ---
    with st.expander("💾 자주 쓰는 경로 프리셋"):
        presets = load_presets()
        if presets:
            preset_names = [p["name"] for p in presets]
            pcol1, pcol2, pcol3 = st.columns([3, 1, 1])
            with pcol1:
                selected_preset_name = st.selectbox("저장된 프리셋", preset_names, key="t1_preset_select", label_visibility="collapsed")
            with pcol2:
                if st.button("📂 불러오기", key="t1_preset_load", use_container_width=True):
                    preset = next(p for p in presets if p["name"] == selected_preset_name)
                    apply_preset_to_session(preset)
                    st.rerun()
            with pcol3:
                if st.button("🗑️ 삭제", key="t1_preset_delete", use_container_width=True):
                    save_presets([p for p in presets if p["name"] != selected_preset_name])
                    st.rerun()
        else:
            st.caption("아직 저장된 프리셋이 없어요.")

        st.markdown("&nbsp;", unsafe_allow_html=True)
        ncol1, ncol2 = st.columns([3, 1])
        with ncol1:
            new_preset_name = st.text_input("새 프리셋 이름", placeholder="예: 주말 처가댁", key="t1_preset_new_name", label_visibility="collapsed")
        with ncol2:
            if st.button("💾 저장", key="t1_preset_save", use_container_width=True):
                if not new_preset_name.strip():
                    st.warning("프리셋 이름을 입력해주세요.")
                elif not (sx and ex):
                    st.warning("출발지와 도착지를 먼저 설정해주세요.")
                else:
                    new_preset = {
                        "name": new_preset_name.strip(),
                        "start_label": start_label, "start_x": sx, "start_y": sy,
                        "end_label": end_label, "end_x": ex, "end_y": ey,
                        "waypoints": [{"label": w[2], "x": w[0], "y": w[1]} for w in waypoints1],
                        "route_option": route_option1,
                    }
                    presets = [p for p in presets if p["name"] != new_preset["name"]] + [new_preset]
                    save_presets(presets)
                    st.success(f"'{new_preset['name']}' 프리셋으로 저장했어요.")
        st.caption("⚠️ 이 서버가 재배포되면 프리셋이 초기화될 수 있어요.")

    # 출발지/도착지/경유지/경로옵션 중 하나라도 바뀌면 자동으로 재탐색
    current_sig = (sx, sy, ex, ey, tuple((w[0], w[1]) for w in waypoints1), route_option1)
    auto_trigger = bool(sx and ex) and st.session_state.get("t1_last_sig") != current_sig
    manual_trigger = st.button("카카오내비 vs Tmap", type="primary", key="btn1", use_container_width=True)
    st.caption("출발지·도착지·경유지·탐색옵션을 바꾸면 자동으로 재탐색됩니다. 값은 그대로 두고 실시간 정보만 새로고침하려면 버튼을 눌러주세요.")

    if manual_trigger or auto_trigger:
        if not sx or not ex:
            st.warning("출발지와 도착지를 모두 정확히 설정해 주세요.")
        else:
            st.session_state.t1_last_sig = current_sig
            with st.spinner("경로를 탐색 중입니다..."):
                k_dist, k_dur, k_seg = get_kakao_route(
                    sx, sy, ex, ey, waypoints=waypoints1, priority=kakao_priority_map[route_option1]
                )
                t_dist, t_dur, t_seg = get_tmap_route(
                    sx, sy, ex, ey, waypoints=waypoints1, search_option=tmap_option_map[route_option1]
                )
                st.session_state.t1_res = {
                    "k_dist": k_dist, "k_dur": k_dur, "k_seg": k_seg,
                    "t_dist": t_dist, "t_dur": t_dur, "t_seg": t_seg,
                    "end_target": end_label, "ex": ex, "ey": ey, "sx": sx, "sy": sy,
                    "waypoints": waypoints1, "route_option": route_option1
                }

    if st.session_state.t1_res:
        res = st.session_state.t1_res
        safe_end = urllib.parse.quote(res["end_target"])

        k_dur, t_dur = res["k_dur"], res["t_dur"]
        k_is_winner = k_dur is not None and (t_dur is None or k_dur < t_dur)
        t_is_winner = t_dur is not None and (k_dur is None or t_dur < k_dur)

        rc1, rc2 = st.columns(2)
        with rc1:
            st.markdown(f"""
            <div class="scoreboard-card {'is-winner' if k_is_winner else ''}">
                <div><span class="provider-badge badge-k" style="background:#F5C518;">K</span><strong>카카오내비</strong>{' <span class="winner-pill">⚡ 더 빠름</span>' if k_is_winner else ''}</div>
                <div class="scoreboard-time">{format_time(k_dur)}</div>
                <div class="scoreboard-dist">{f"{res['k_dist']} km" if res["k_dist"] else "-"}</div>
                <a href="https://map.kakao.com/link/to/{safe_end},{res['ey']},{res['ex']}" target="_blank" style="display:block; text-align:center; padding:10px; background:#FEE500; color:#000; text-decoration:none; border-radius:8px; font-weight:700;">🟡 카카오 앱 열기</a>
            </div>
            """, unsafe_allow_html=True)
        with rc2:
            st.markdown(f"""
            <div class="scoreboard-card {'is-winner' if t_is_winner else ''}">
                <div><span class="provider-badge" style="background:#EF4C35;">T</span><strong>티맵</strong>{' <span class="winner-pill">⚡ 더 빠름</span>' if t_is_winner else ''}</div>
                <div class="scoreboard-time">{format_time(t_dur)}</div>
                <div class="scoreboard-dist">{f"{res['t_dist']} km" if res["t_dist"] else "-"}</div>
                <a href="tmap://route?goalname={safe_end}&goalx={res['ex']}&goaly={res['ey']}" style="display:block; text-align:center; padding:10px; background:#EF4C35; color:#FFF; text-decoration:none; border-radius:8px; font-weight:700;">🔴 티맵 앱 열기</a>
            </div>
            """, unsafe_allow_html=True)

        wp_names = " → ".join(w[2].split(" (")[0] for w in res.get("waypoints", []))
        st.caption(f"탐색 옵션: {res.get('route_option', '추천 경로')}" + (f" · 경유지: {wp_names}" if wp_names else ""))
        
        if st.button("🔄 지도 정위치로 되돌리기", key="reset_map_1", use_container_width=True):
            st.session_state.map_key += 1
            
        map_c1, map_c2 = st.columns(2)
        markers = [
            {"coord": [res["sy"], res["sx"]], "color": "#1E90FF", "text": "S"},
            {"coord": [res["ey"], res["ex"]], "color": "#FF0000", "text": "E"}
        ]
        for i, (wx, wy, _) in enumerate(res.get("waypoints", [])):
            markers.append({"coord": [wy, wx], "color": "#8A2BE2", "text": f"경유{i+1}"})
        
        with map_c1:
            st.caption("🗺️ 카카오내비 최적 경로 (순정 카카오맵)")
            render_kakao_map(res["ey"], res["ex"], res["k_seg"], markers, map_key=st.session_state.map_key, height=400)
        with map_c2:
            st.caption("🗺️ 티맵 최적 경로 (순정 티맵)")
            render_tmap(res["ey"], res["ex"], res["t_seg"], markers, map_key=st.session_state.map_key, height=400)

# ------------------------------------------
# 메뉴 2: 다중 출발지 승부
# ------------------------------------------
elif menu_selection == "📍 다중 출발지 승부":
    st.markdown("### 📍 어디서 출발하는게 가장 빠를까?")
    t2_ex, t2_ey, t2_end_label = address_picker("🎯 공통 도착지", key="t2_end", default_query=work_address)
    st.caption("출발 후보지 (비워두면 계산에서 제외됩니다)")
    c1, c2, c3 = st.columns(3)
    with c1: t2_s1x, t2_s1y, t2_s1_label = address_picker("후보 1", key="t2_s1", default_query=home_address)
    with c2: t2_s2x, t2_s2y, t2_s2_label = address_picker("후보 2", key="t2_s2")
    with c3: t2_s3x, t2_s3y, t2_s3_label = address_picker("후보 3", key="t2_s3")
    
    if st.button("출발지별 소요시간 랭킹 보기", type="primary", key="btn2", use_container_width=True):
        if not t2_ex:
            st.error("공통 도착지를 검색해서 선택해주세요.")
        else:
            with st.spinner("각 출발지별 시간을 계산 중입니다..."):
                results = []
                for name, sx, sy, label in [
                    ("후보 1", t2_s1x, t2_s1y, t2_s1_label),
                    ("후보 2", t2_s2x, t2_s2y, t2_s2_label),
                    ("후보 3", t2_s3x, t2_s3y, t2_s3_label),
                ]:
                    if sx and sy:
                        _, k_dur, k_seg = get_kakao_route(sx, sy, t2_ex, t2_ey)
                        _, t_dur, _ = get_tmap_route(sx, sy, t2_ex, t2_ey)
                        avg_dur = ((k_dur or 0) + (t_dur or 0)) / 2
                        results.append({
                            "name": label, "sx":sx, "sy":sy, 
                            "kakao": k_dur, "tmap": t_dur, "avg": avg_dur, "k_seg": k_seg
                        })
                
                if results:
                    results = sorted(results, key=lambda x: x["avg"])
                    colors = ["#FF4B4B", "#1E90FF", "#03C75A"]
                    for i, res in enumerate(results):
                        res["rank"] = i + 1
                        res["color"] = colors[i] if i < len(colors) else "#555555"
                    
                    st.session_state.t2_res = {"results": results, "ex": t2_ex, "ey": t2_ey}
    
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
# 메뉴 3: 시간대별 타임머신
# ------------------------------------------
elif menu_selection == "🔮 시간대별 타임머신":
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

    if route_choice3.startswith("1️⃣"): default_start3, default_end3 = home_address, work_address
    elif route_choice3.startswith("2️⃣"): default_start3, default_end3 = work_address, home_address
    else: default_start3, default_end3 = "", ""

    # 출근길/퇴근길/직접설정 전환 시 이전 검색 상태 초기화
    if st.session_state.get("t3_prev_route_choice") != route_choice3:
        st.session_state.t3_prev_route_choice = route_choice3
        for k in ["t3_start", "t3_end"]:
            for suffix in ["_query", "_prev_query", "_candidates", "_pick"]:
                st.session_state.pop(f"{k}{suffix}", None)

    ct3, ct4 = st.columns(2)
    with ct3:
        sx3, sy3, start_label3 = address_picker("출발지", key="t3_start", default_query=default_start3)
    with ct4:
        ex3, ey3, end_label3 = address_picker("도착지", key="t3_end", default_query=default_end3)

    if start_label3 and end_label3:
        st.info(f"📍 **예측 경로:** {start_label3} ➔ {end_label3}")
    else:
        st.warning("출발지와 도착지를 검색해서 선택해주세요.")

    if st.button("시간대별 일괄 예측 조회하기", type="primary", key="btn3", use_container_width=True):
        if not sx3 or not ex3:
            st.warning("출발지와 도착지를 모두 정확히 설정해 주세요.")
        else:
            with st.spinner("티맵 타임머신을 가동 중입니다... (약 5초 소요)"):
                sx, sy, ex, ey = sx3, sy3, ex3, ey3
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
