import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import sys, os
sys.stderr = open(os.devnull, "w")

def show(filtered_shelters, filtered_animals, tab_labels):
    st.subheader("🗺️ 보호소 지도")

    # 데이터가 없는 경우 즉시 리턴
    if filtered_shelters.empty:
        st.warning("표시할 데이터가 없습니다. 필터 조건을 변경해보세요.")
        return

    # 보호소별 대표 이미지 매핑
    if not filtered_animals.empty and 'image_url' in filtered_animals.columns:
        shelter_image_map = filtered_animals.groupby('shelter_name')['image_url'].first().to_dict()
    else:
        shelter_image_map = {}

    # 지도 중심 좌표 계산 (좌표가 없으면 서울시청 기준)
    valid_lat = filtered_shelters['lat'].dropna()
    valid_lon = filtered_shelters['lon'].dropna()
    if not valid_lat.empty and not valid_lon.empty:
        map_center = [valid_lat.mean(), valid_lon.mean()]
    else:
        map_center = [37.5665, 126.9780]

    # folium 지도 생성
    map_obj = folium.Map(location=map_center, zoom_start=7)

    # 마커 추가
    for _, row in filtered_shelters.iterrows():
        if pd.notna(row['lat']) and pd.notna(row['lon']):
            image_url = shelter_image_map.get(row['shelter_name'])
            if not image_url or image_url == '':
                image_url = "https://via.placeholder.com/150?text=사진+없음"
            popup_html = f"""
                <b>{row['shelter_name']}</b><br>
                <img src='{image_url}' width='150'><br>
                지역: {row.get('region', '정보 없음')}<br>
                주요 품종: {row.get('kind_name', '정보 없음')}<br>
                보호 중: {int(row.get('count', 0))} 마리
            """
            folium.Marker(
                [row['lat'], row['lon']],
                popup=popup_html,
                tooltip=row['shelter_name'],
                icon=folium.Icon(color="blue", icon="paw", prefix='fa')
            ).add_to(map_obj)

    # Use a column to explicitly group map and table for consistent layout
    col1, = st.columns(1)
    with col1:
        # 지도 렌더링 - rerun 시 발생하는 FileNotFoundError 무시
        map_event = None
        try:
            map_event = st_folium(map_obj, width='100%', height=500)
        except FileNotFoundError:
            # rerun 도중에 발생하는 frontend/build/None 에러는 무시
            map_event = None
        except Exception as e:
            print(f"[DEBUG] st_folium 예외 발생 (무시): {e}")
            map_event = None

        # 클릭 이벤트 처리
        if map_event and map_event.get("last_object_clicked_tooltip"):
            clicked_shelter = map_event["last_object_clicked_tooltip"]

            if st.session_state.get("selected_shelter") != clicked_shelter:
                st.session_state.selected_shelter = clicked_shelter
                detail_tab_idx = tab_labels.index("📋 보호소 상세 현황")
                st.session_state.active_tab_idx = detail_tab_idx

                try:
                    st.rerun()
                except Exception as e:
                    print(f"[DEBUG] rerun 예외 발생 (무시): {e}")

        # 보호소 현황 테이블
        st.subheader("📊 보호소별 동물 현황")
        base_cols = ['shelter_name', 'region']
        optional_cols = ['kind_name', 'count', 'long_term', 'adopted']
        display_cols = base_cols + [col for col in optional_cols if col in filtered_shelters.columns]

        st.dataframe(
            filtered_shelters[display_cols],
            use_container_width=True,
            column_config={
                "shelter_name": "보호소명",
                "region": "지역",
                "kind_name": "주요 품종",
                "count": "보호 중",
                "long_term": "장기 보호",
                "adopted": "입양 완료"
            }
        )