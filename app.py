from pathlib import Path

import pandas as pd
import streamlit as st

from utils.data_loader import load_companies, load_activity_by_company
from utils.export_excel import build_workbook_bytes

st.set_page_config(page_title="GHG Data Portal", page_icon="📊", layout="wide")

st.title("활동데이터 제출 포털")
st.caption("수신메일 하나로 조회 후, 2024 기준값을 참고하고 2025 값을 표처럼 붙여넣는 버전")

DATA_DIR = Path(__file__).parent / "data"
companies = load_companies(DATA_DIR / "companies.json")

SECTION_TITLES = {
    "fixed": "Scope 1 · 고정연소",
    "mobile": "Scope 1 · 이동연소",
    "waste": "Scope 1 · 폐기물 소각",
    "process": "Scope 1 · 공정배출",
    "electricity": "Scope 2 · 전력 사용시설",
    "steam": "Scope 2 · 열/스팀 사용시설",
}

META_COLUMNS = {
    "fixed": ["facility", "fuel", "unit"],
    "mobile": ["facility", "fuel", "unit"],
    "waste": ["incinerator", "wasteType", "wasteDetail", "unit"],
    "process": ["processType", "processSubType", "calcFactor", "unit"],
    "electricity": ["facility", "fuel", "unit"],
    "steam": ["facility", "fuel", "unit"],
}

META_LABELS = {
    "facility": "배출시설명",
    "fuel": "연료명",
    "unit": "단위",
    "incinerator": "소각로명",
    "wasteType": "폐기물분류",
    "wasteDetail": "폐기물세부분류",
    "processType": "공정구분",
    "processSubType": "세부구분",
    "calcFactor": "계산 인자",
}

if "lookup_done" not in st.session_state:
    st.session_state.lookup_done = False
if "company" not in st.session_state:
    st.session_state.company = None
if "activity" not in st.session_state:
    st.session_state.activity = None
if "tables_2025" not in st.session_state:
    st.session_state.tables_2025 = {}


def make_2024_df(section_key: str, rows: list[dict]) -> pd.DataFrame:
    meta_cols = META_COLUMNS[section_key]
    records = []
    for row in rows:
        rec = {META_LABELS[col]: row.get(col) for col in meta_cols}
        for i, value in enumerate(row.get("months", [None] * 12), start=1):
            rec[f"{i}월"] = value
        records.append(rec)
    return pd.DataFrame(records)


def make_2025_df(section_key: str, rows: list[dict]) -> pd.DataFrame:
    meta_cols = META_COLUMNS[section_key]
    records = []
    for row in rows:
        rec = {META_LABELS[col]: row.get(col) for col in meta_cols}
        for i in range(1, 13):
            rec[f"{i}월"] = ""
        records.append(rec)
    return pd.DataFrame(records)


def section_table_key(section_key: str) -> str:
    company_id = st.session_state.company["companyId"]
    return f"{company_id}_{section_key}_2025_table"


def initialize_section_tables() -> None:
    activity = st.session_state.activity or {"sections": {}}
    for section_key in SECTION_TITLES:
        rows = activity.get("sections", {}).get(section_key, [])
        if not rows:
            continue
        key = section_table_key(section_key)
        if key not in st.session_state.tables_2025:
            st.session_state.tables_2025[key] = make_2025_df(section_key, rows)


def collect_inputs_for_export() -> dict[str, str]:
    inputs = {}
    activity = st.session_state.activity or {"sections": {}}
    for section_key in SECTION_TITLES:
        rows = activity.get("sections", {}).get(section_key, [])
        if not rows:
            continue
        table_key = section_table_key(section_key)
        df = st.session_state.tables_2025.get(table_key)
        if df is None:
            continue
        for idx in range(len(df)):
            for m in range(1, 13):
                value = df.iloc[idx][f"{m}월"]
                inputs[f"{section_key}_{idx+1}_{m}"] = "" if pd.isna(value) else str(value)
    return inputs


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
            st.session_state.tables_2025 = {}
            initialize_section_tables()
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

    for section_key, title in SECTION_TITLES.items():
        rows = activity.get("sections", {}).get(section_key, [])
        if not rows:
            continue

        with st.expander(title, expanded=True):
            st.write("2024 기준값")
            df_2024 = make_2024_df(section_key, rows)
            st.dataframe(df_2024, use_container_width=True, hide_index=True)

            st.write("2025 입력값")
            st.caption("엑셀에서 여러 셀을 복사해 붙여넣을 수 있도록 표 형태 편집으로 바꿨습니다.")
            table_key = section_table_key(section_key)
            edited_df = st.data_editor(
                st.session_state.tables_2025[table_key],
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                key=f"editor_{table_key}",
                disabled=[META_LABELS[col] for col in META_COLUMNS[section_key]],
            )
            st.session_state.tables_2025[table_key] = edited_df

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
            inputs_2025 = collect_inputs_for_export()
            excel_bytes = build_workbook_bytes(company, activity, inputs_2025)
            st.download_button(
                label="엑셀 다운로드",
                data=excel_bytes,
                file_name=f"{company.get('companyName','업체')}_활동데이터_2025_업데이트.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
