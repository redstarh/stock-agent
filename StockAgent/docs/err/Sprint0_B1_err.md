# Sprint 0 - B-1 에러 기록

## [에러 1] build-backend 설정 오류
- **단계**: GREEN (pip install)
- **에러**: `Cannot import 'setuptools.backends._legacy'` — pip install -e 실패
- **원인**: pyproject.toml의 build-backend가 `setuptools.backends._legacy:_Backend`로 잘못 지정됨 (존재하지 않는 모듈)
- **해결**: `setuptools.build_meta`로 수정 → 설치 성공

## 최종 결과
- 테스트 5/5 통과
- pytest, config, logging 모두 정상 동작
