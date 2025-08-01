# ==============================================================================
# detail_view.py - 보호소 상세 현황 탭
# ==============================================================================
# 이 파일은 사용자가 지도에서 특정 보호소를 선택했을 때, 해당 보호소의
# 상세 정보와 현재 보호 중인 동물들의 목록을 보여주는 화면을 구성합니다.
#
# [주요 기능]
# 1. **선택된 보호소 확인:** `st.session_state`에 저장된 `selected_shelter` 값을
#    가져와 현재 어떤 보호소가 선택되었는지 확인합니다.
# 2. **동물 상세 정보 조회:** `data_manager.get_animal_details` 함수를 호출하여
#    선택된 보호소에 소속된 동물들의 데이터를 DB에서 가져옵니다.
# 3. **동물 목록 표시:** 조회된 동물 데이터를 반복하면서 각 동물의 사진, 이름,
#    나이, 특징 등의 정보를 `st.columns`를 활용하여 깔끔하게 표시합니다.
# 4. **찜하기 기능:** 각 동물 정보 옆에 '찜하기/찜 취소' 버튼을 추가합니다.
#    - 사용자가 버튼을 누르면 `st.session_state.favorites` 목록에 해당 동물의
#      고유 ID(`desertion_no`)를 추가하거나 제거합니다.
#    - 상태 변경 후 `st.rerun()`을 호출하여 화면을 즉시 새로고침하고 변경사항을
#      반영합니다.
# 5. **데이터 다운로드:** 현재 필터링된 조건에 맞는 보호소 목록 전체를
#    CSV 파일로 다운로드할 수 있는 버튼을 제공합니다.
# ==============================================================================

import streamlit as st
from data_manager import get_animal_details
import pandas as pd

def show(filtered_data):
    """
    '보호소 상세 현황' 탭의 전체 UI를 그리고 로직을 처리하는 메인 함수입니다.

    Args:
        filtered_data (pd.DataFrame): app.py에서 필터링된 보호소 데이터.
                                      CSV 다운로드 기능에 사용됩니다.
    """
    st.subheader("📋 보호소 상세 현황")

    # 세션 상태에서 사용자가 지도에서 클릭한 보호소 이름을 가져옵니다.
    selected_shelter = st.session_state.get("selected_shelter", None)

    # 보호소가 선택된 경우에만 상세 정보를 표시합니다.
    if selected_shelter:
        st.markdown(f"### 🏠 {selected_shelter}")

        # 선택된 보호소 이름으로 해당 보호소의 동물 목록을 조회합니다.
        animal_details = get_animal_details(selected_shelter)

        if not animal_details.empty:
            # 조회된 동물 목록을 하나씩 순회하며 화면에 표시합니다.
            for _, animal in animal_details.iterrows():
                # 화면을 두 개의 컬럼으로 나누어 왼쪽은 이미지, 오른쪽은 텍스트 정보를 배치합니다.
                cols = st.columns([1, 3])
                with cols[0]:
                    # 표시 이름을 결정 (animal_name → kind_name → notice_no 순서)
                    display_name = (
                        animal.get('kind_name') if pd.notna(animal.get('kind_name')) else animal.get('notice_no', '이름 없음')
                    )

                    if "image_url" in animal and pd.notna(animal["image_url"]):
                        st.image(animal["image_url"], width=150, caption=display_name)
                    else:
                        st.image("https://via.placeholder.com/150?text=사진+없음", width=150, caption=display_name)
                with cols[1]:
                    # --- 찜하기 버튼 로직 ---
                    # 각 버튼은 고유한 key를 가져야 하므로, 동물의 고유 ID(desertion_no)를 사용합니다.
                    # desertion_no가 없는 데이터의 경우, 찜하기 기능을 비활성화합니다.
                    if 'desertion_no' in animal and pd.notna(animal['desertion_no']):
                        is_favorited = animal['desertion_no'] in st.session_state.favorites
                        button_text = "❤️ 찜 취소" if is_favorited else "🤍 찜하기"
                        
                        # 버튼 클릭 시의 로직
                        if st.button(button_text, key=f"fav_add_{animal['desertion_no']}"):
                            if is_favorited:
                                st.session_state.favorites.remove(animal['desertion_no'])
                            else:
                                st.session_state.favorites.append(animal['desertion_no'])
                            # 화면을 새로고침하여 버튼 텍스트 변경 및 찜 목록 수 업데이트를 즉시 반영합니다.
                            st.rerun()
                    else:
                        st.info("찜하기 기능을 사용할 수 없습니다 (유기번호 없음).")

                    # 동물의 기본 정보를 마크다운 형식으로 예쁘게 표시합니다.
                    age_info = animal.get('age', '정보 없음')
                    weight_info = animal.get('weight', None)
                    if pd.notna(weight_info) and weight_info != '정보 없음':
                        st.markdown(f"**{display_name}** ({age_info}, {weight_info})")
                    else:
                        st.markdown(f"**{display_name}** ({age_info})")

                    sex_info = animal.get('sex', None)

                    if sex_info == 'F':
                        sex_display = "♀️ 성별: 암컷"
                    elif sex_info == 'M':
                        sex_display = "♂️ 성별: 수컷"
                    else:
                        sex_display = "성별: 정보 없음"

                    st.markdown(f"**{sex_display}**")

                    st.markdown(f"**🐾 정보:** {animal.get('special_mark', '정보 없음')}")

                    # 발견 장소 (있을 때만 표시)
                    happen_place = animal.get('happen_place', None)
                    if pd.notna(happen_place) and happen_place != '정보 없음':
                        st.markdown(f"**📍 발견 장소:** {happen_place}")
                
                st.markdown("---") # 각 동물 정보 사이에 구분선을 추가합니다.
        else:
            st.warning("이 보호소에 등록된 동물 정보가 없습니다.")

    else:
        # 아직 보호소를 선택하지 않은 사용자에게 안내 메시지를 보여줍니다.
        st.info("지도에서 보호소 마커를 클릭하여 상세 정보를 확인하세요.")

    st.markdown("---")
    # 사용자가 현재 선택된 보호소 동물 목록을 파일로 저장할 수 있도록 합니다.
    if selected_shelter and not animal_details.empty:
        st.download_button(
            label="📥 선택된 보호소 동물 목록 다운로드 (CSV)",
            data=animal_details.to_csv(index=False).encode('utf-8-sig'),
            file_name=f"{selected_shelter}_animals.csv",
            mime="text/csv"
        )