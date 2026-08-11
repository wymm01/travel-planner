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

pip install requests python-dotenv google-genai

## 5. API 키 설정 방법

이 프로그램은 Gemini API와 Kakao Local API를 사용하므로
두 API의 키를 환경변수로 설정해야 합니다.

### 5-1. `.env` 파일 생성

프로젝트의 최상위 폴더에 `.env` 파일을 생성합니다.

프로젝트 구조는 다음과 같습니다.

travel_planner/  
├── travel_planner.py  
├── README.md  
├── .gitignore  
├── .env  
└── results/  

.env 파일에 다음과 같이 API 키를 입력합니다.
GEMINI_API_KEY=여기에_Gemini_API_키_입력
KAKAO_REST_API_KEY=여기에_Kakao_REST_API_키_입력

### 5-2. API 키 확인

프로그램을 실행하면 .env 파일에 설정된 환경변수에서
API 키를 자동으로 불러옵니다.  
from dotenv import load_dotenv  
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")

## 6. API 키 보안 및 유출 방지 주의사항

API 키는 개인정보 및 인증 정보와 같이 취급해야 하며
GitHub와 같은 공개 저장소에 절대로 공개해서는 안 됩니다.

반드시 지켜야 할 사항
 1. API 키를 travel_planner.py 코드에 직접 작성하지 않습니다.
 2. .env 파일을 GitHub에 업로드하지 않습니다.
 3. README.md에 실제 API 키를 작성하지 않습니다.
 4. GitHub에 코드를 업로드하기 전에 .env가 Git에 포함되지 않았는지 확인합니다.
 5. API 키가 실수로 GitHub에 공개된 경우 즉시 해당 API 키를 폐기하고 새로운 API 키를 발급받습니다.

현재 프로젝트의 .gitignore에는 다음과 같은 내용을 포함합니다.

.env  
__pycache__/  
*.pyc

이를 통해 API 키가 들어 있는 .env 파일과 Python 캐시 파일이
GitHub 저장소에 업로드되는 것을 방지합니다. 
