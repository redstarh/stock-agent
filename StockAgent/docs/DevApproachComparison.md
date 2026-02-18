# 개발 방식 비교: Minimal vs. Full Agent/Skill

StockAgent 프로젝트에서 실제 사용한 방식과 정의된 Agent/Skill을 전면 활용하는 방식의 장단점 비교.

---

## 1. 두 가지 방식 개요

### Minimal 방식 (실제 사용)

```
사용자 지시 -> Orchestrator가 직접 계획 -> executor (Sonnet) 병렬 투입 -> 수동 검증 -> 반복
```

사용 도구: `executor` (Sonnet) + `autopilot` 만 활용

### Full 방식 (권장)

```
ralplan(계획 수렴) -> architect(설계 검증) -> autopilot+ultrawork(병렬 구현)
-> ultraqa(QA 사이클) -> code-review + security-review -> git-master + writer
```

사용 도구: 8개 영역 20+ Agent/Skill 전면 활용

---

## 2. 단계별 비교

### 2.1 계획 단계

| 항목 | Minimal | Full |
|------|---------|------|
| 방법 | Orchestrator가 StockAgent_Task.md를 읽고 직접 Sprint 순서 결정 | `ralplan` -> Planner 초안 -> Architect 기술 검증 -> Critic 리뷰 -> 합의까지 반복 |
| 장점 | 빠름. 계획에 시간 소비 없이 바로 구현 착수 | 의존성 누락, 병렬 그룹 오류 사전 방지. 3자 검증으로 계획 품질 높음 |
| 단점 | 계획 오류 시 구현 중 발견 -> 재작업 리스크 | 계획에 Opus 3회 이상 호출 -> 비용/시간 증가 |
| 이 프로젝트 영향 | StockAgent_Task.md가 이미 상세해서 문제 없었음 | 태스크 계획서가 없었다면 필수적이었을 것 |

### 2.2 아키텍처 설계

| 항목 | Minimal | Full |
|------|---------|------|
| 방법 | StockAgent-v1.0.md 설계 스펙을 그대로 따름 | `architect` (Opus)가 모듈 간 인터페이스, 데이터 흐름 검증 |
| 장점 | 설계 문서가 충분하면 별도 검증 불필요 | 설계 스펙과 실제 구현 간 불일치 조기 발견 |
| 단점 | 설계 스펙의 모호한 부분이 구현 시 해석에 의존 | Opus 비용 추가 |
| 이 프로젝트 영향 | v1.0 스펙이 상세해서 큰 문제 없었음 | Strategy Engine <-> Scanner 간 인터페이스를 사전 정의했으면 더 깔끔했을 가능성 |

### 2.3 구현 단계

| 항목 | Minimal | Full |
|------|---------|------|
| 방법 | `executor` (Sonnet) 일률 투입. 모든 태스크에 같은 tier | 태스크 복잡도별 `executor-low`/`executor`/`executor-high` 분배 |
| 장점 | 일관성. Agent 선택 고민 없이 빠른 투입 | B-1 같은 단순 셋업은 Haiku로 비용 절감, B-13 같은 전략 로직은 Opus로 품질 확보 |
| 단점 | 단순 작업에도 Sonnet 비용 발생. 복잡한 작업에서 Sonnet 한계 가능 | Agent 선택 오버헤드. 잘못 배정하면 재작업 |
| 비용 추정 | 36 태스크 x Sonnet = 균일 비용 | ~12 Haiku + ~18 Sonnet + ~6 Opus = 총 비용 비슷하나 품질 분산 |

### 2.4 프론트엔드

| 항목 | Minimal | Full |
|------|---------|------|
| 방법 | `executor`가 컴포넌트 + 스타일 + 테스트 일괄 생성 | `designer`/`designer-high`가 UI 구현, `frontend-ui-ux` skill 자동 활성화 |
| 장점 | 빠른 구현. 기능 중심 개발 | 디자인 일관성. 13개 컴포넌트 간 UX 패턴 통일 |
| 단점 | 디자인 일관성은 개발자(Orchestrator) 판단에 의존 | Designer agent는 코드 실행 불가 -> executor와 협업 필요 |
| 이 프로젝트 영향 | TailwindCSS 유틸리티 기반이라 일관성 유지 용이했음 | 커스텀 디자인 시스템이 필요했다면 designer가 필수 |

### 2.5 테스트/품질

| 항목 | Minimal | Full |
|------|---------|------|
| 방법 | executor가 구현 시 테스트 동시 작성 -> 커버리지 확인 후 수동으로 개선 지시 | `tdd` skill 강제 -> `ultraqa`로 자동 반복 사이클 |
| 장점 | 유연함. 필요한 만큼만 테스트 | TDD 원칙 100% 준수 보장. 커버리지 목표 자동 달성 |
| 단점 | 초기 커버리지 낮음 (90%) -> 3라운드 수동 개선 필요 | ultraqa 사이클에 추가 시간/비용 |
| 이 프로젝트 영향 | 3라운드 수동 개선으로 97.59% 달성 | tdd + ultraqa 사용 시 1라운드에 95%+ 가능했을 것 |

### 2.6 코드 리뷰/보안

| 항목 | Minimal | Full |
|------|---------|------|
| 방법 | 별도 리뷰 없이 테스트 통과로 품질 판단 | `code-reviewer` (Opus) + `security-reviewer` (Opus)로 전수 검사 |
| 장점 | 빠른 개발 속도 유지 | 코드 품질, 보안 취약점 사전 발견. 프로덕션 배포 전 필수 |
| 단점 | 잠재적 코드 스멜, 보안 이슈 미발견 가능 | Opus 2회 추가 호출. 지적 사항 수정 시간 |
| 이 프로젝트 영향 | API 키가 .env에 있고 Mock 기반이라 당장 보안 리스크 낮음 | 실제 키움 API 연동 전에는 security-review 필수 |

### 2.7 Git/문서

| 항목 | Minimal | Full |
|------|---------|------|
| 방법 | 사용자 요청 시 수동 commit/push. CLAUDE.md 수동 업데이트 | `git-master`가 Sprint별 atomic commit, `writer`가 문서 자동 유지 |
| 장점 | 사용자가 커밋 시점 완전 제어 | 커밋 히스토리 깔끔. 문서가 코드와 항상 동기화 |
| 단점 | 대규모 변경이 하나의 커밋에 묶임 (163 files changed) | 자동 커밋이 너무 잦을 수 있음 |
| 이 프로젝트 영향 | Sprint 0~6 전체가 1커밋 -> 리뷰/롤백 어려움 | Sprint별 또는 태스크별 커밋이면 변경 추적 용이 |

---

## 3. 종합 비교표

| 평가 항목 | Minimal | Full |
|-----------|---------|------|
| **개발 속도** | 빠름 (계획/리뷰 생략) | 느림 (각 단계 Agent 호출) |
| **비용** | 낮음 (Sonnet 위주) | 높음 (Opus 다수 호출) |
| **코드 품질** | 양호 (테스트 기반 검증) | 우수 (다층 검증) |
| **보안** | 미검증 | 검증됨 |
| **설계 정합성** | 설계 문서 의존 | Agent 검증 |
| **테스트 커버리지** | 3라운드 수동 개선 필요 | 1라운드 자동 달성 |
| **커밋 히스토리** | 대규모 단일 커밋 | 태스크별 atomic 커밋 |
| **문서 동기화** | 수동 업데이트 | 자동 유지 |
| **확장성** | 36 태스크에서 효율적 | 100+ 태스크에서도 관리 가능 |
| **재현성** | Orchestrator 판단 의존 | 파이프라인 패턴화 가능 |

---

## 4. 결론

### 이 프로젝트에서는 Minimal 방식이 효율적이었다

이유:
- 설계 문서(v1.0)와 태스크 계획서(StockAgent_Task.md)가 이미 상세했음
- 36개 태스크는 관리 가능한 규모
- Mock 기반 개발로 보안 리스크가 낮았음
- 단일 개발자 프로젝트로 리뷰 부담 낮음

### Full 방식이 필수적인 상황

| 상황 | 필요한 Agent/Skill |
|------|-------------------|
| 설계 문서가 불완전하거나 없을 때 | `ralplan` + `analyst` |
| 50+ 태스크의 대규모 프로젝트 | `ultrawork` + tier별 Agent 분배 |
| 프로덕션 배포 직전 | `security-review` + `code-review` |
| 팀 개발 시 | `git-master`로 커밋 히스토리 관리 |
| 실제 API 연동 시 | `qa-tester`로 E2E 통합 검증 |
| 커스텀 UI 디자인 필요 시 | `designer` + `frontend-ui-ux` |
| 복잡한 비즈니스 로직 | `executor-high` (Opus) |

### 권장 전략: 하이브리드

```
Phase 1 (초기 개발): Minimal
  - 빠르게 MVP 구현
  - executor (Sonnet) 중심

Phase 2 (품질 강화): 선택적 Full
  - security-review: 프로덕션 배포 전
  - code-review: 주요 모듈 리뷰
  - ultraqa: 커버리지 목표 달성

Phase 3 (운영 전환): Full
  - qa-tester: E2E 통합 테스트
  - architect: 성능/확장성 검증
  - git-master: 릴리스 관리
```

이 하이브리드 접근이 속도와 품질의 최적 균형을 제공한다.
