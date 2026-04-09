import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Admin", page_icon="⚙️", layout="wide")
st.title("관리자용 화면")
st.caption("지금은 구조만 분리한 상태입니다.")

data_dir = Path(__file__).resolve().parents[1] / "data"

st.subheader("현재 데이터 파일 확인")
for name in ["companies.json", "activity_2024.json"]:
    p = data_dir / name
    st.write(f"- {name}: {'존재함' if p.exists() else '없음'}")

st.subheader("조회 정책")
st.write("- 현재는 수신메일(email) 하나로만 조회합니다.")
