def render_kakao_map(map_id, center_lat, center_lng, route_segments=None,
                      start=None, end=None, height=400, fit_bounds=True):
    """
    카카오맵 디버그 버전
    - HTML 실행 여부 확인
    - Kakao Maps SDK 로딩 여부 확인
    - kakao.maps.load 실행 여부 확인
    - 지도 생성 여부 확인
    - SDK 오류를 화면에 직접 표시
    """

    if not KAKAO_JS_KEY:
        st.error(
            "KAKAO_JS_KEY가 설정되지 않았습니다. "
            "Streamlit Secrets에 JavaScript Key를 추가해 주세요."
        )
        return

    route_segments = route_segments or []

    # -----------------------------
    # 경로 데이터 변환
    # -----------------------------
    route_data = []

    for seg in route_segments:
        if not seg.get("coords"):
            continue

        coords = []

        for c in seg["coords"]:
            try:
                coords.append({
                    "lat": float(c[0]),
                    "lng": float(c[1])
                })
            except Exception:
                continue

        if coords:
            route_data.append({
                "color": seg.get("color", "#1E90FF"),
                "coords": coords
            })

    data = {
        "center": {
            "lat": float(center_lat),
            "lng": float(center_lng)
        },
        "route": route_data,
        "start": (
            {
                "lat": float(start[0]),
                "lng": float(start[1])
            }
            if start else None
        ),
        "end": (
            {
                "lat": float(end[0]),
                "lng": float(end[1])
            }
            if end else None
        )
    }

    data_json = json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":")
    )

    # JavaScript Key 앞뒤 공백 제거
    js_key = str(KAKAO_JS_KEY).strip()

    # HTML 속성에 안전하게 삽입
    js_key_encoded = urllib.parse.quote(js_key, safe="")

    # map_id를 안전한 DOM ID로 사용
    safe_map_id = "".join(
        ch if ch.isalnum() or ch in "_-" else "_"
        for ch in str(map_id)
    )

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">

<style>
html, body {{
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    font-family: Arial, sans-serif;
}}

#debug {{
    position: absolute;
    z-index: 9999;
    top: 8px;
    left: 8px;
    right: 8px;
    padding: 10px 12px;
    background: rgba(255,255,255,0.95);
    border: 1px solid #ccc;
    border-radius: 6px;
    font-size: 13px;
    line-height: 1.5;
    color: #333;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}}

#map {{
    width: 100%;
    height: 100%;
    min-height: {height}px;
}}

.debug-ok {{
    color: #087f23;
}}

.debug-error {{
    color: #d32f2f;
    font-weight: bold;
}}

.debug-warn {{
    color: #e65100;
}}

.debug-loading {{
    color: #1565c0;
}}
</style>

<script
    src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={js_key_encoded}&autoload=false"
    onload="sdkScriptLoaded()"
    onerror="sdkScriptFailed()">
</script>

</head>

<body>

<div id="debug">
    <div class="debug-loading">
        ① HTML 실행됨
    </div>
    <div class="debug-loading">
        ② Kakao Maps SDK 로딩 대기 중...
    </div>
</div>

<div id="{safe_map_id}"></div>

<script>

const DATA = {data_json};

const MAP_ID = "{safe_map_id}";


// -----------------------------------------
// 디버그 메시지
// -----------------------------------------
function setDebug(message, className) {{

    const debug = document.getElementById("debug");

    if (!debug) {{
        return;
    }}

    debug.innerHTML +=
        '<div class="' + (className || '') + '">' +
        message +
        '</div>';
}}


// -----------------------------------------
// SDK script 로딩 성공
// -----------------------------------------
function sdkScriptLoaded() {{

    setDebug(
        "③ Kakao Maps SDK script 로딩 완료",
        "debug-ok"
    );

    setTimeout(function() {{

        if (typeof kakao === "undefined") {{

            setDebug(
                "❌ kakao 객체가 생성되지 않았습니다.",
                "debug-error"
            );

            return;
        }}

        if (!kakao.maps) {{

            setDebug(
                "❌ kakao.maps 객체가 없습니다.",
                "debug-error"
            );

            return;
        }}

        setDebug(
            "④ kakao.maps 객체 확인 완료",
            "debug-ok"
        );

        try {{

            kakao.maps.load(initMap);

        }} catch (error) {{

            setDebug(
                "❌ kakao.maps.load 오류: " +
                error.message,
                "debug-error"
            );
        }}

    }}, 100);

}}


// -----------------------------------------
// SDK script 로딩 실패
// -----------------------------------------
function sdkScriptFailed() {{

    setDebug(
        "❌ Kakao Maps SDK script 로딩 실패",
        "debug-error"
    );

    setDebug(
        "JavaScript Key 또는 Kakao Developers의 JavaScript SDK 도메인 설정을 확인하세요.",
        "debug-warn"
    );

    setDebug(
        "요청 주소: https://dapi.kakao.com/v2/maps/sdk.js",
        "debug-warn"
    );
}}


// -----------------------------------------
// 마커 이미지
// -----------------------------------------
function markerImage(color, text) {{

    const svg =
        '<svg xmlns="http://www.w3.org/2000/svg" width="42" height="42">' +
        '<circle cx="21" cy="21" r="18" fill="' + color +
        '" stroke="white" stroke-width="3"/>' +
        '<text x="21" y="27" text-anchor="middle" ' +
        'font-size="15" font-weight="bold" fill="white">' +
        text +
        '</text>' +
        '</svg>';

    return new kakao.maps.MarkerImage(
        "data:image/svg+xml;charset=UTF-8," +
        encodeURIComponent(svg),
        new kakao.maps.Size(42, 42),
        {{
            offset: new kakao.maps.Point(21, 21)
        }}
    );
}}


// -----------------------------------------
// 지도 생성
// -----------------------------------------
function initMap() {{

    setDebug(
        "⑤ kakao.maps.load 실행 완료",
        "debug-ok"
    );

    try {{

        const mapElement =
            document.getElementById(MAP_ID);

        if (!mapElement) {{

            setDebug(
                "❌ 지도 DOM을 찾을 수 없습니다.",
                "debug-error"
            );

            return;
        }}

        const center =
            new kakao.maps.LatLng(
                DATA.center.lat,
                DATA.center.lng
            );

        const map =
            new kakao.maps.Map(
                mapElement,
                {{
                    center: center,
                    level: 7
                }}
            );

        setDebug(
            "⑥ 카카오맵 생성 완료",
            "debug-ok"
        );

        const bounds =
            new kakao.maps.LatLngBounds();


        // -----------------------------------------
        // 경로 표시
        // -----------------------------------------
        DATA.route.forEach(function(seg) {{

            if (!seg.coords || seg.coords.length === 0) {{
                return;
            }}

            const path = [];

            seg.coords.forEach(function(c) {{

                const p =
                    new kakao.maps.LatLng(
                        c.lat,
                        c.lng
                    );

                path.push(p);

                bounds.extend(p);
            }});


            if (path.length > 1) {{

                new kakao.maps.Polyline({{
                    map: map,
                    path: path,
                    strokeWeight: 6,
                    strokeColor: seg.color,
                    strokeOpacity: 0.9,
                    strokeStyle: "solid"
                }});
            }}

        }});


        // -----------------------------------------
        // 출발지
        // -----------------------------------------
        if (DATA.start) {{

            const p =
                new kakao.maps.LatLng(
                    DATA.start.lat,
                    DATA.start.lng
                );

            new kakao.maps.Marker({{
                map: map,
                position: p,
                image: markerImage(
                    "#1E90FF",
                    "S"
                )
            }});

            bounds.extend(p);
        }}


        // -----------------------------------------
        // 도착지
        // -----------------------------------------
        if (DATA.end) {{

            const p =
                new kakao.maps.LatLng(
                    DATA.end.lat,
                    DATA.end.lng
                );

            new kakao.maps.Marker({{
                map: map,
                position: p,
                image: markerImage(
                    "#FF0000",
                    "E"
                )
            }});

            bounds.extend(p);
        }}


        // -----------------------------------------
        // 경로에 맞춰 지도 영역 조정
        // -----------------------------------------
        if ({str(fit_bounds).lower()} &&
            !bounds.isEmpty()) {{

            map.setBounds(
                bounds,
                40,
                40,
                40,
                40
            );
        }}


        // -----------------------------------------
        // 화면 크기 변경
        // -----------------------------------------
        window.addEventListener(
            "resize",
            function() {{

                map.relayout();

                if (
                    {str(fit_bounds).lower()} &&
                    !bounds.isEmpty()
                ) {{

                    map.setBounds(
                        bounds,
                        40,
                        40,
                        40,
                        40
                    );
                }}
            }}
        );


        setDebug(
            "⑦ 지도 렌더링 완료",
            "debug-ok"
        );

    }} catch (error) {{

        setDebug(
            "❌ 지도 생성 중 JavaScript 오류: " +
            error.message,
            "debug-error"
        );

        console.error(
            "Kakao Map Error:",
            error
        );
    }}
}}


// -----------------------------------------
// 초기 실행 상태
// -----------------------------------------
setDebug(
    "Map ID: " + MAP_ID,
    "debug-loading"
);

setDebug(
    "JavaScript Key 길이: " +
    "{len(js_key)}",
    "debug-loading"
);

</script>

</body>
</html>
"""

    components.html(
        html,
        height=height,
        scrolling=False
    )
