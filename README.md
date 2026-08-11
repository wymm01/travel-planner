# 국내 여행지 추천 프로그램

Gemini API와 Kakao Local API를 활용하여 여행 날짜에 맞는 국내 여행지를 추천하고, 추천 지역의 맛집을 검색하여 최종 여행 리포트를 생성하는 CLI 기반 Python 프로그램입니다.

## 1. 프로그램 개요

사용자가 여행 날짜를 입력하면 다음 순서로 프로그램이 실행됩니다.

1. Gemini API를 이용하여 국내 여행지 1곳을 추천합니다.
2. 추천 지역의 날씨, 행사/축제, 추천 이유를 JSON 형태로 생성합니다.
3. Kakao Local API를 이용하여 추천 지역의 맛집을 검색합니다.
4. Gemini API를 이용하여 최종 여행 리포트를 Markdown 형식으로 생성합니다.
5. `results/` 폴더에 원본 데이터 JSON과 최종 여행 리포트를 저장합니다.

## 2. 주요 기능

- CLI 기반 여행 날짜 입력
- `YYYY-MM-DD` 날짜 형식 검증
- Gemini API를 이용한 국내 여행지 추천
- Gemini API JSON 응답 처리
- JSON 파싱 오류 발생 시 1회 재요청
- Kakao Local API를 이용한 맛집 검색
- API 및 네트워크 오류 기록
- 최종 Markdown 여행 리포트 생성
- LLM 오류 발생 시 기본 리포트 생성
- 실행 결과 자동 저장

## 3. 실행 환경

- Python 3.10 이상 권장
- Gemini API Key
- Kakao REST API Key

## 4. 라이브러리 설치

프로젝트 폴더에서 다음 명령어를 실행합니다.

```bash
pip install requests python-dotenv google-genai
