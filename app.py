from pathlib import Path

import streamlit as st

from utils.data_loader import load_companies, load_activity_by_company
from utils.export_excel import build_workbook_bytes

st.set_page_config(page_title="GHG Data Portal", page_icon="📊", layout="wide")

st.title("활동데이터 제출 포털")
st.caption("수신메일 하나로 조회 후 2025 값을 입력하는 Streamlit 예시")

DATA_DIR = Path(__file__).parent / "data"
companies = load_companies(DATA_DIR / "companies.json")

if "lookup_done" not in st.session_state:
    st.session_state.lookup_done = False
if "company" not in st.session_state:
    st.session_state.company = None
if "activity" not in st.session_state:
    st.session_state.activity = None
if "inputs_2025" not in st.session_state:
    st.session_state.inputs_2025 = {}

with st.container(border=True):
    c1, c2 = st.columns([2, 1])
    email = c1.text_input("수신메일", placeholder="예: esg@company.com")
    lookup = c2.button("기본정보 및 전년도 값 불러오기", use_container_width=True)

    if lookup:
        company = next(
            (c for c in companies if str(c.get("email", "")).strip().lower() == email.strip().lower()),
            None,
        )
        if company is None:
            st.session_state.lookup_done = False
            st.session_state.company = None
            st.session_state.activity = None
            st.error("일치하는 업체를 찾지 못했습니다.")
        else:
            st.session_state.lookup_done = True
            st.session_state.company = company
            st.session_state.activity = load_activity_by_company(DATA_DIR / "activity_2024.json", company["companyId"])
            st.success("기본정보와 2024년 기준값을 불러왔습니다.")

if st.session_state.lookup_done and st.session_state.company:
    company = st.session_state.company
    activity = st.session_state.activity or {"sections": {}}

    with st.container(border=True):
        st.subheader("기본정보")
        a, b, c = st.columns(3)
        a.text_input("업체명", value=company.get("companyName", ""), disabled=True)
        b.text_input("사업자등록번호", value=company.get("bizNo", ""), disabled=True)
        c.text_input("수신메일", value=company.get("email", ""), disabled=True)

    section_titles = {
        "fixed": "Scope 1 · 고정연소",
        "mobile": "Scope 1 · 이동연소",
        "waste": "Scope 1 · 폐기물 소각",
        "process": "Scope 1 · 공정배출",
        "electricity": "Scope 2 · 전력 사용시설",
        "steam": "Scope 2 · 열/스팀 사용시설",
    }

    for section_key, title in section_titles.items():
        rows = activity.get("sections", {}).get(section_key, [])
        if not rows:
            continue

        with st.expander(title, expanded=True):
            st.caption("2024 기준값은 참고용, 2025 값만 입력")
            for idx, row in enumerate(rows, start=1):
                st.markdown(f"**행 {idx}**")
                meta_cols = st.columns(3)
                meta_cols[0].text_input(
                    "시설/항목",
                    value=row.get("facility") or row.get("incinerator") or row.get("processType") or "",
                    disabled=True,
                    key=f"{section_key}_{idx}_meta1",
                )
                meta_cols[1].text_input(
                    "연료/세부",
                    value=row.get("fuel") or row.get("wasteType") or row.get("processSubType") or "",
                    disabled=True,
                    key=f"{section_key}_{idx}_meta2",
                )
                meta_cols[2].text_input("단위", value=row.get("unit") or "", disabled=True, key=f"{section_key}_{idx}_unit")

                months_2024 = row.get("months", [None] * 12)

                st.write("2024 기준값")
                cols_2024 = st.columns(6)
                for m in range(12):
                    cols_2024[m % 6].text_input(
                        f"{m+1}월",
                        value="" if months_2024[m] is None else str(months_2024[m]),
                        disabled=True,
                        key=f"{section_key}_{idx}_2024_{m+1}",
                    )

                st.write("2025 입력값")
                cols_2025 = st.columns(6)
                for m in range(12):
                    v = cols_2025[m % 6].text_input(
                        f"{m+1}월 입력",
                        value=st.session_state.inputs_2025.get(f"{section_key}_{idx}_{m+1}", ""),
                        key=f"{section_key}_{idx}_2025_{m+1}",
                    )
                    st.session_state.inputs_2025[f"{section_key}_{idx}_{m+1}"] = v
                st.divider()

    with st.container(border=True):
        st.subheader("증빙 업로드")
        up1, up2 = st.columns(2)
        up1.file_uploader("전기 사용량 증빙", accept_multiple_files=True, key="e1")
        up2.file_uploader("이동연소 증빙", accept_multiple_files=True, key="e2")
        up1, up2 = st.columns(2)
        up1.file_uploader("고정연소 증빙", accept_multiple_files=True, key="e3")
        up2.file_uploader("기타 증빙", accept_multiple_files=True, key="e4")
        st.info("현재 예시는 업로드 UI만 포함합니다. 영구 저장은 별도 스토리지 연결이 필요합니다.")

    with st.container(border=True):
        st.subheader("엑셀 다운로드")
        if st.button("사용자 입력 반영 엑셀 만들기", type="primary"):
            excel_bytes = build_workbook_bytes(company, activity, st.session_state.inputs_2025)
            st.download_button(
                label="엑셀 다운로드",
                data=excel_bytes,
                file_name=f"{company.get('companyName','업체')}_활동데이터_2025_업데이트.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
