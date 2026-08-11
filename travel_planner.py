import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict, List, Tuple
from dotenv import load_dotenv
import requests
from google import genai
from google.genai import types

# .env 파일 로드
load_dotenv()

# 환경변수에서 API 키 로드
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")


def check_env_vars():
    """API 키 설정 확인"""
    missing = []
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if not KAKAO_REST_API_KEY:
        missing.append("KAKAO_REST_API_KEY")

    if missing:
        print(f"[오류] 다음 환경변수가 설정되지 않았습니다: {', '.join(missing)}")
        print("\n[설정 방법]")
        print("1. 프로젝트 루트에 .env 파일을 생성하세요.")
        print("2. 아래 내용을 입력하세요:")
        print("   GEMINI_API_KEY=your_gemini_api_key_here")
        print("   KAKAO_REST_API_KEY=your_kakao_api_key_here")
        sys.exit(1)


def validate_date(date_text: str) -> bool:
    """YYYY-MM-DD 날짜 형식 검증"""
    try:
        datetime.datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def call_llm_for_recommendation(
    date_str: str, retry: bool = False
) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    """1차 Gemini 추천 API 호출 (JSON 파싱 및 1회 재시도 포함)"""
    errors = []
    client = genai.Client(api_key=GEMINI_API_KEY)

    system_prompt = (
        "당신은 국내 여행 전문가입니다. 반드시 아래 JSON 스키마 형식만을 준수하여 답변하세요. 다른 설명은 하지 마세요.\n"
        "응답은 파이썬 json.loads()로 파싱 가능한 유효한 JSON 문자열이어야 합니다.\n\n"
        "JSON 스키마:\n"
        "{\n"
        '  "recommended_city": "string (예: 제주, 강릉)",\n'
        '  "weather": "string (해당 시기 일반적 날씨 요약)",\n'
        '  "events": ["array of string (행사/축제 후보 1~3개)"],\n'
        '  "reason": "string (추천 근거 2~4문장)"\n'
        "}"
    )

    user_prompt = f"여행 날짜: {date_str}. 이 날짜에 어울리는 한국의 여행지 1곳을 추천해 주세요."
    if retry:
        user_prompt += "\n주의: 이전 응답이 JSON 파싱에 실패했습니다. 반드시 기재된 필수 키만 포함된 순수 JSON 형식으로만 응답해 주세요."

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.7,
            ),
        )

        data = json.loads(response.text)

        # 필수 키 검증
        required_keys = ["recommended_city", "weather", "events", "reason"]
        for key in required_keys:
            if key not in data:
                raise KeyError(f"필수 키 누락: {key}")

        return data, errors

    except Exception as e:
        err_msg = f"Gemini 추천 호출/파싱 실패: {str(e)}"
        errors.append(
            {"step": "llm_recommendation", "type": "PARSE_ERROR", "message": err_msg}
        )

        if not retry:
            print(f"  └─ 파싱 오류 발생. 재요청 1회를 진행합니다...")
            return call_llm_for_recommendation(date_str, retry=True)
        else:
            print(f"  └─ 재요청 실패. 기본값으로 진행합니다.")
            fallback_data = {
                "recommended_city": "제주",
                "weather": "날씨 정보 파싱 실패",
                "events": [],
                "reason": "LLM 응답을 정형 데이터로 변환하지 못하여 기본 추천지로 대체되었습니다.",
            }
            return fallback_data, errors


def search_places_kakao(
    city: str, limit: int = 5
) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """Kakao Local API를 사용한 맛집 검색"""
    errors = []
    places = []
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    query = f"{city} 맛집"
    params = {"query": query, "size": limit}

    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)

        if res.status_code in (401, 403):
            err = {"step": "place_search", "type": "AUTH_ERROR", "message": f"HTTP {res.status_code}"}
            errors.append(err)
            print(f"  └─ 오류: 카카오 API 인증 실패({res.status_code}). 키를 확인하세요.")
            return [], errors

        res.raise_for_status()
        data = res.json()
        documents = data.get("documents", [])

        if not documents:
            errors.append(
                {
                    "step": "place_search",
                    "type": "EMPTY_RESULT",
                    "message": f"0 results for query={query}",
                }
            )
            return [], errors

        for doc in documents:
            places.append(
                {
                    "name": doc.get("place_name", ""),
                    "address": doc.get("road_address_name") or doc.get("address_name", ""),
                    "category": doc.get("category_name", ""),
                    "url": doc.get("place_url", ""),
                    "x": float(doc.get("x", 0)) if doc.get("x") else None,
                    "y": float(doc.get("y", 0)) if doc.get("y") else None,
                }
            )

    except requests.exceptions.RequestException as e:
        errors.append(
            {
                "step": "place_search",
                "type": "NETWORK_ERROR",
                "message": str(e),
            }
        )
        print(f"  └─ 지도 API 요청 중 오류 발생: {e}")

    return places, errors


def generate_final_report_llm(
    date_str: str,
    rec_data: Dict[str, Any],
    places: List[Dict[str, Any]],
    errors: List[Dict[str, str]],
) -> str:
    """최종 마크다운 리포트 생성 (Gemini API 연동)"""
    client = genai.Client(api_key=GEMINI_API_KEY)

    places_text = json.dumps(places, ensure_ascii=False, indent=2) if places else "데이터 없음 (장소 검색 결과 0건 또는 오류)"
    errors_text = json.dumps(errors, ensure_ascii=False, indent=2)

    prompt = f"""
다음 정보를 바탕으로 깔끔하고 가독성 좋은 여행 리포트를 Markdown 형식으로 생성해 주세요.

[입력 정보]
- 날짜: {date_str}
- 추천 지역: {rec_data.get('recommended_city')}
- 날씨 정보: {rec_data.get('weather')}
- 행사/축제 정보: {json.dumps(rec_data.get('events', []), ensure_ascii=False)}
- 추천 이유: {rec_data.get('reason')}
- 맛집 리스트: {places_text}
- 발생 오류 목록: {errors_text}

[리포트 포함 필수 항목 및 제목 구조]
# {date_str} 국내 여행 추천 리포트
## 추천 지역
## 추천 이유
## 날씨 요약
## 행사/축제
## 맛집 추천 (데이터가 없으면 '데이터 없음'으로 작성)
## 1일 일정 제안 (오전/오후/저녁)
## 오류 요약(errors)
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception:
        return generate_fallback_markdown(date_str, rec_data, places, errors)


def generate_fallback_markdown(date_str, rec_data, places, errors) -> str:
    """LLM 실패 시 기본 마크다운 작성 fallback"""
    md = f"# {date_str} 국내 여행 추천 리포트\n\n"
    md += f"## 추천 지역\n{rec_data.get('recommended_city', '정보 없음')}\n\n"
    md += f"## 추천 이유\n{rec_data.get('reason', '정보 없음')}\n\n"
    md += f"## 날씨 요약\n{rec_data.get('weather', '정보 없음')}\n\n"
    md += "## 행사/축제\n"
    for ev in rec_data.get("events", []):
        md += f"- {ev}\n"
    if not rec_data.get("events"):
        md += "관련 행사 정보 없음\n"

    md += "\n## 맛집 추천\n"
    if places:
        for p in places:
            md += f"- **{p['name']}** ({p['category']}): {p['address']} [상세보기]({p['url']})\n"
    else:
        md += "데이터 없음 (장소 검색 결과 0건)\n"

    md += "\n## 1일 일정 제안\n"
    md += "- **오전**: 주요 명소 방문 및 산책\n"
    md += "- **오후**: 추천 맛집에서 점심 식사 및 현지 카페 이용\n"
    md += "- **저녁**: 대표 야경 명소 감상 및 일정 마무리\n\n"

    md += "## 오류 요약(errors)\n"
    md += f"```json\n{json.dumps(errors, ensure_ascii=False, indent=2)}\n```\n"

    return md


def main():
    parser = argparse.ArgumentParser(description="API 활용 국내 여행지 추천 프로그램")
    parser.add_argument(
        "-date",
        "--date",
        type=str,
        required=True,
        help="여행 날짜 (형식: YYYY-MM-DD)",
    )

    args = parser.parse_args()

    if not validate_date(args.date):
        print("[오류] 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형태로 입력하세요.")
        parser.print_help()
        sys.exit(1)

    check_env_vars()

    all_errors = []

    print(f"[1/3] 1차 추천 생성 중(LLM)...")
    rec_data, llm_errors = call_llm_for_recommendation(args.date)
    all_errors.extend(llm_errors)
    city = rec_data.get("recommended_city", "제주")
    print(f'  └─ recommended_city: "{city}"')

    print(f"[2/3] 맛집 검색 중(지도/장소 API)...")
    places, search_errors = search_places_kakao(city, limit=5)
    all_errors.extend(search_errors)
    if places:
        print(f"  └─ 맛집 {len(places)}곳 검색 완료")
    else:
        print(f"  └─ 검색 결과 0건 또는 오류 발생 (다음 단계로 계속 진행)")

    print(f"[3/3] 최종 리포트 생성 중(LLM)...")
    report_md = generate_final_report_llm(args.date, rec_data, places, all_errors)
    print(f"  └─ 리포트 생성 완료")

    os.makedirs("results", exist_ok=True)
    json_path = os.path.join("results", f"{args.date}_data.json")
    md_path = os.path.join("results", f"{args.date}_travel_plan.md")

    result_json = {
        "date": args.date,
        "recommendation": rec_data,
        "restaurants": places,
        "errors": all_errors,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result_json, f, ensure_ascii=False, indent=2)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"\n완료! {md_path} 및 {json_path} 를 확인하세요.")


if __name__ == "__main__":
    main()