"""모델별 테마 분류 비교 테스트."""
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.processing.llm_theme_classifier import classify_theme_llm
from app.core.config import settings

MODELS = {
    "haiku": settings.bedrock_model_id_fast,
    "sonnet": settings.bedrock_model_id_mid,
    "opus": settings.bedrock_model_id,
}

# 정답이 명확한 샘플 뉴스
SAMPLES = [
    {"title": "[속보]삼성전자주가, 19만원 넘었다", "expected": "[] (주가 변동, 특정 테마 아님)"},
    {"title": "인천 송도,바이오생산 116만리터 달성··· '세계 최대' 유지", "expected": "['바이오']"},
    {"title": "삼성전자, 국내 250대 기업 중 ESG 종합평가 1위", "expected": "[] (ESG, 특정 테마 아님)"},
    {"title": "집·가게·공장...LG로봇 포트폴리오 한 눈에 보기", "expected": "['로봇']"},
    {"title": "KB국민은행·희망친구기아대책, 설맞이 전통시장 사랑나눔 후원금 기탁", "expected": "['금융'] 또는 []"},
    {"title": "전기차 '가격 전쟁'…테슬라·BYD 공세에 현대차·기아 맞불", "expected": "['자동차']"},
    {"title": "현대차, 美 친환경차 누적 판매 100만대 돌파…하이브리드가 견인", "expected": "['자동차']"},
    {"title": "SK하이닉스 HBM3E 12단 양산 돌입…AI 서버 수요 대응", "expected": "['반도체', 'AI']"},
    {"title": "카카오스타일, KOTITI시험연구원과 임직원 대상 섬유 품질 특강 진행", "expected": "[] (사내 행사)"},
    {"title": "현대차·삼성전자·카카오와 협업 기회…스타트업 30곳 공모", "expected": "[] (스타트업 공모)"},
]

def test_model(model_name, model_id, title):
    start = time.time()
    result = classify_theme_llm(title, model_id=model_id)
    elapsed = time.time() - start
    return model_name, result, elapsed

print(f"=== 모델별 테마 분류 비교 테스트 ===\n")
print(f"Models: {json.dumps({k: v for k, v in MODELS.items()}, indent=2)}\n")

for sample in SAMPLES:
    title = sample["title"]
    expected = sample["expected"]
    print(f"뉴스: {title}")
    print(f"기대: {expected}")

    # 3개 모델 병렬 실행
    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(test_model, name, mid, title): name
            for name, mid in MODELS.items()
            if mid  # 빈 문자열 제외
        }
        for future in as_completed(futures):
            name, themes, elapsed = future.result()
            results[name] = (themes, elapsed)

    for name in ["haiku", "sonnet", "opus"]:
        if name in results:
            themes, elapsed = results[name]
            print(f"  {name:8s}: {str(themes):30s} ({elapsed:.2f}s)")
    print()
