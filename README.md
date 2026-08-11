# API 활용 국내 여행지 추천 프로그램

본 프로그램은 OpenAI API와 Kakao Local API를 조합하여 입력받은 날짜에 최적화된 국내 여행지와 맛집을 추천하고, 1일 여행 리포트를 생성하는 CLI 프로그램입니다.

## 1. 주요 기능
- **CLI 인터페이스**: 날짜(`-date "YYYY-MM-DD"`) 입력 및 입력값 검증
- **LLM 추천 연동**: 날짜에 기반한 국내 도시 추천, 날씨 정보 및 지역 행사 정보 JSON 파싱
- **지도 API 맛집 검색**: 추천 도시의 맛집 5곳을 검색 (검색 실패 시에도 예외 처리 후 계속 진행)
- **최종 여행 리포트 생성**: Markdown 문서 및 원본 결과 데이터 JSON 저장

## 2. 사전 준비사항
- Python 3.10 이상
- 라이브러리 설치:
  ```bash
  pip install openai requests python-dotenv