# GHG Data Portal (Streamlit, email-only lookup)

수신메일 하나로 업체를 조회하고, 전년도(2024) 기준값을 확인한 뒤 올해(2025) 값을 입력할 수 있는 Streamlit 예시 구조입니다.

## 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 조회 방식
- 사업자등록번호 없이 **수신메일(email)만으로 조회**
- 이메일은 유일값이라고 가정

## 데이터 파일
- `data/companies.json`
- `data/activity_2024.json`
