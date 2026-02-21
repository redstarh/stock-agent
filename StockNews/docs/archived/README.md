# Archived Documentation

이 디렉토리는 StockNews 프로젝트의 보관된 문서들을 포함합니다.

## 디렉토리 구조

```
archived/
├── v1-legacy/          # 초기 설계 문서 (v1.0)
├── task-plans/         # 개발 Task 계획서
├── specs/              # 상세 기능 스펙
└── err/                # 개발 중 에러 로그
```

## v1-legacy/

초기 시스템 설계 및 요약 문서

| 파일 | 설명 | 대체 문서 |
|------|------|----------|
| StockNews-v1.0.md | 초기 시스템 설계서 | [ARCHITECTURE.md](../ARCHITECTURE.md) |
| CONSOLIDATED_SUMMARY.md | 프로젝트 통합 요약 | [PRD.md](../PRD.md) |
| ARCHIVE_CANDIDATES.md | 보관 대상 문서 목록 | (완료됨) |

## task-plans/

개발 작업 분해 및 TDD 계획서

| 파일 | 설명 | 대체 문서 |
|------|------|----------|
| StockNews_Task.md | Phase 1 Task 계획 | [DEVELOPMENT_HISTORY.md](../DEVELOPMENT_HISTORY.md) |
| TestAgent.md | TDD 테스트 에이전트 설계 | [DEVELOPMENT_HISTORY.md](../DEVELOPMENT_HISTORY.md) |

## specs/

상세 기능 스펙 문서 (구현 완료)

| 파일 | 설명 | 대체 문서 |
|------|------|----------|
| MLPipeline-Spec.md | ML Pipeline 5단계 상세 스펙 | [ARCHITECTURE.md](../ARCHITECTURE.md) Section 5 |
| PredictionVerification-Architecture.md | 예측 검증 엔진 아키텍처 | [ARCHITECTURE.md](../ARCHITECTURE.md) |
| PredictionVerification-Spec.md | 예측 검증 상세 스펙 | [DETAILED_FLOWS.md](../DETAILED_FLOWS.md) |
| PredictionVerification-TestPlan.md | 예측 검증 TDD 테스트 계획 | [DEVELOPMENT_HISTORY.md](../DEVELOPMENT_HISTORY.md) Phase 4 |

## err/

개발 중 발생한 에러 로그 (역사적 기록)

- `Task1_err.md` ~ `Task13_err.md`: Phase 1 개발 중 발생한 에러와 해결 방법
- 참고용으로 보관되며, 현재는 사용하지 않음

## 보관 사유

이 문서들은 다음 이유로 보관되었습니다:

1. **통합됨**: 내용이 새로운 통합 문서로 재구성됨
2. **완료됨**: 구현이 완료되어 참조 필요성이 낮아짐
3. **중복됨**: 여러 문서에 동일 내용이 산재되어 있었음
4. **역사적**: 개발 과정의 기록으로만 의미가 있음

## 접근 권장사항

- **신규 개발자**: 먼저 [../README.md](../README.md)를 읽고 Core Documentation 섹션부터 시작
- **역사적 맥락 파악**: 이 디렉토리의 문서들을 참고
- **상세 구현 스펙**: `specs/` 디렉토리 문서 참조 (구현 완료 상태)

## 복원 방법

보관된 문서가 필요하다면:

```bash
# Git 히스토리에서 원래 위치 확인
git log --follow archived/v1-legacy/StockNews-v1.0.md

# 특정 커밋에서 파일 내용 보기
git show <commit-hash>:docs/StockNews-v1.0.md
```
