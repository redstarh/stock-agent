"""모델별 감성분석 비교 테스트."""
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.core.llm import call_llm
from app.core.config import settings

MODELS = {
    "haiku": settings.bedrock_model_id_fast,
    "sonnet": settings.bedrock_model_id_mid,
    "opus": settings.bedrock_model_id,
}

SYSTEM_PROMPT = """당신은 한국 금융 시장 전문 감성 분석가입니다.
뉴스 제목의 주가 영향도를 분석하여 sentiment, score를 JSON으로 반환하세요.
- positive (0.3~1.0), neutral (-0.3~0.3), negative (-1.0~-0.3)
JSON만 반환: {"sentiment": "...", "score": float}"""

SAMPLES = [
    {"title": "삼성전자 4분기 영업이익 10조원 돌파", "expected": "positive (0.8~0.9)"},
    {"title": "SK하이닉스 메모리 반도체 가격 급락", "expected": "negative (-0.7~-0.8)"},
    {"title": "[속보]삼성전자주가, 19만원 넘었다", "expected": "positive (0.5~0.7)"},
    {"title": "현대차 CEO 교체 발표", "expected": "neutral (0.0)"},
    {"title": "카카오스타일, 임직원 대상 섬유 품질 특강 진행", "expected": "neutral (0.0)"},
    {"title": "LG에너지솔루션 배터리 화재로 대규모 리콜", "expected": "negative (-0.8~-0.95)"},
    {"title": "셀트리온 바이오시밀러 FDA 승인 획득", "expected": "positive (0.8~0.9)"},
    {"title": "Palo Alto Networks' stock slides as underwhelming outlook overshadows AI messaging", "expected": "negative (-0.6~-0.7)"},
]

def test_model(model_name, model_id, title):
    start = time.time()
    try:
        result = call_llm(SYSTEM_PROMPT, title, model_id=model_id)
        parsed = json.loads(result)
        elapsed = time.time() - start
        return model_name, parsed, elapsed
    except Exception as e:
        elapsed = time.time() - start
        return model_name, {"error": str(e)}, elapsed

print("=== 모델별 감성분석 비교 테스트 ===\n")

for sample in SAMPLES:
    title = sample["title"]
    expected = sample["expected"]
    print(f"뉴스: {title}")
    print(f"기대: {expected}")

    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(test_model, name, mid, title): name
            for name, mid in MODELS.items()
            if mid
        }
        for future in as_completed(futures):
            name, parsed, elapsed = future.result()
            results[name] = (parsed, elapsed)

    for name in ["haiku", "sonnet", "opus"]:
        if name in results:
            parsed, elapsed = results[name]
            sent = parsed.get("sentiment", "?")
            score = parsed.get("score", "?")
            print(f"  {name:8s}: {sent:10s} score={str(score):8s} ({elapsed:.2f}s)")
    print()
