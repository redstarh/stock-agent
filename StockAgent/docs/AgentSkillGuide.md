# StockAgent 개발 Agent & Skill 가이드

StockAgent 프로젝트 개발에 활용된/필요한 Agent와 Skill 정리.

---

## 1. 프로젝트 특성

| 항목 | 내용 |
|------|------|
| 총 태스크 | 36개 (Backend 22 + Frontend 14) |
| Sprint | 7개 (Sprint 0~6) |
| 최대 병렬 | Sprint 2에서 10개 동시 실행 |
| 크리티컬 패스 | 7단계 (B-1→B-3→B-4→B-7→B-10→B-13→B-17/B-21) |
| TDD 방식 | RED→GREEN→REFACTOR 전 태스크 적용 |
| 테스트 결과 | Backend 145 tests (97.59%), Frontend 64 tests (93.52%) |

---

## 2. 실제 사용된 Agent & Skill

### Agents

| Agent | Tier | 사용 장면 | 이유 |
|-------|------|-----------|------|
| `executor` | MED (Sonnet) | Sprint 0~6 전체 태스크 구현, 커버리지 개선 | 코드 작성 + 테스트 실행이 필요한 모든 작업. 파일 읽기/쓰기/편집 + Bash 실행이 가능해서 TDD 사이클을 자율적으로 수행 |

### Skills

| Skill | 사용 장면 | 이유 |
|-------|-----------|------|
| `autopilot` | 전체 개발 흐름 | 36개 태스크를 Sprint별로 자동 계획→실행→검증하는 루프. 사용자 개입 최소화 |

---

## 3. 단계별 권장 Agent & Skill

### 3.1 계획/분석 단계

| Agent/Skill | 용도 | 이유 |
|-------------|------|------|
| **`planner`** (Opus) | Sprint 계획, 의존성 그래프 설계 | 36개 태스크의 의존성 분석과 병렬 실행 레인 설계에 적합. StockAgent_Task.md 같은 계획서 작성 |
| **`analyst`** (Opus) | 요구사항 분석 | StockAgent-v1.0.md(설계 스펙)에서 누락된 태스크, 암묵적 범위(Implicit Scope) 식별. 태스크 계획 전 사전 분석 |
| **`critic`** (Opus) | 계획 리뷰 | Sprint 계획의 병렬 그룹이 올바른지, 크리티컬 패스 분석이 맞는지 검증 |
| **`ralplan`** (Skill) | 반복적 계획 수렴 | Planner→Architect→Critic 3자가 합의할 때까지 반복. 복잡한 의존성 그래프에서 최적 실행 순서 도출 |

### 3.2 아키텍처 설계

| Agent/Skill | 용도 | 이유 |
|-------------|------|------|
| **`architect`** (Opus) | 시스템 아키텍처 검증 | REST pipeline(키움API→수집→전략→리스크→주문→DB→WebSocket→Frontend) 설계 검증. 모듈 간 인터페이스 정의 |
| **`architect-medium`** (Sonnet) | 모듈 레벨 설계 | 개별 모듈(Strategy Engine, Risk Management 등) 내부 구조 설계. Opus보다 빠르고 이 수준에서 충분 |

### 3.3 구현 단계

| Agent/Skill | 용도 | 이유 |
|-------------|------|------|
| **`executor`** (Sonnet) | 기능 구현 | 대부분의 태스크(B-3~B-22, F-3~F-14). 소스코드 + 테스트를 함께 작성하고 pytest/jest 실행까지 자율 수행 |
| **`executor-low`** (Haiku) | 단순 작업 | 커버리지 개선처럼 테스트만 추가하는 작업. 비용 절감 |
| **`executor-high`** (Opus) | 복잡한 로직 | Strategy Engine(B-13), Parameter Tuner(B-21) 같은 비즈니스 로직이 복잡한 태스크 |
| **`deep-executor`** (Opus) | 대규모 자율 작업 | Sprint 전체를 한 번에 위임할 때. 다수 파일을 동시에 수정하며 의존성을 자체 관리 |
| **`ultrawork`** (Skill) | 병렬 구현 | Sprint 2(최대 10개 병렬), Sprint 3(7개 병렬) 같은 대규모 병렬 실행. 이 프로젝트의 핵심 생산성 도구 |
| **`autopilot`** (Skill) | 전체 자동화 | Sprint 0→6 전 과정을 자동으로 계획→실행→검증→다음 Sprint 진행 |

### 3.4 프론트엔드

| Agent/Skill | 용도 | 이유 |
|-------------|------|------|
| **`designer`** (Sonnet) | UI 컴포넌트 구현 | Dashboard, StrategyPage, OrderMonitor 같은 UI 컴포넌트. TailwindCSS 스타일링 + React 패턴에 특화 |
| **`designer-high`** (Opus) | 복합 UI 시스템 | 13개 컴포넌트의 일관된 디자인 시스템. Navigation + Layout + 페이지 간 통일된 UX |
| **`frontend-ui-ux`** (Skill) | UI 작업 자동 감지 | 컴포넌트/스타일링 작업 시 자동 활성화. 디자이너 관점의 UI 구현 |

### 3.5 테스트/품질

| Agent/Skill | 용도 | 이유 |
|-------------|------|------|
| **`tdd-guide`** (Sonnet) | TDD 워크플로 강제 | TestAgent.md 기반 RED→GREEN→REFACTOR 사이클 보장 |
| **`qa-tester`** (Sonnet) | 통합 테스트 | Integration Gate 1~3 검증. 실제 API 연동 시 E2E 테스트 수행 |
| **`build-fixer`** (Sonnet) | 빌드 오류 수정 | TypeScript 타입 에러, Jest 설정 문제(MSW ESM compat, jest-env-jsdom) 해결 |
| **`tdd`** (Skill) | TDD 강제 모드 | 테스트 없이 코드 작성 방지. 프로젝트의 TDD 원칙 준수 |
| **`ultraqa`** (Skill) | QA 사이클 | test→verify→fix→repeat. 커버리지 97%+ 달성 과정에서 반복 검증 |

### 3.6 코드 리뷰/보안

| Agent/Skill | 용도 | 이유 |
|-------------|------|------|
| **`code-reviewer`** (Opus) | 코드 품질 리뷰 | 36개 모듈의 코드 품질, 패턴 일관성, 에러 핸들링 검증 |
| **`security-reviewer`** (Opus) | 보안 검토 | API 키 관리(Settings/.env), 키움 인증 토큰, WebSocket 연결 보안 검토 |
| **`security-review`** (Skill) | OWASP 취약점 검사 | REST API 엔드포인트, 사용자 입력 검증, SQL injection 방지 확인 |

### 3.7 탐색/리서치

| Agent/Skill | 용도 | 이유 |
|-------------|------|------|
| **`explore`** (Haiku) | 파일 검색 | 기존 코드 구조 파악, 테스트 파일 위치 확인 |
| **`explore-medium`** (Sonnet) | 패턴 분석 | 모듈 간 import 관계, API 라우터 등록 패턴 파악 |
| **`researcher`** (Sonnet) | 외부 문서 조사 | 키움증권 REST API 스펙, FastAPI WebSocket 패턴, MSW v2 설정법 등 공식 문서 확인 |

### 3.8 Git/문서

| Agent/Skill | 용도 | 이유 |
|-------------|------|------|
| **`git-master`** (Sonnet) | Git 관리 | 커밋 메시지 스타일 통일, Sprint별 커밋 전략 |
| **`writer`** (Haiku) | 문서 작성 | CLAUDE.md 업데이트, TestAgent.md 유지보수 |

---

## 4. 최적 실행 파이프라인

```
계획:   ralplan (Planner + Architect + Critic 합의)
         |
구현:   autopilot + ultrawork (Sprint별 병렬 executor 투입)
         |
검증:   ultraqa (test -> verify -> fix 반복)
         |
리뷰:   code-review + security-review
         |
완료:   git-master (커밋) + writer (문서 업데이트)
```

### 단계별 흐름

```
[ralplan]
  Planner: 의존성 분석 → Sprint 계획 초안
  Architect: 기술적 타당성 검증
  Critic: 누락/리스크 지적
  → 합의될 때까지 반복

[autopilot + ultrawork]
  Sprint 0: executor x2 (B-1 || F-1)
  Sprint 1: executor x3 (B-2 || B-3 || B-11)
  Sprint 2: executor x10 (B-4~6 || B-9,14,19 || B-12 || F-3~5)
  Sprint 3: executor x7 (B-7,15,16,20 || F-6,7,10)
  Sprint 4: executor x6 (B-10,8,22 || F-8,9,11)
  Sprint 5: executor x5 (B-13,18 || F-12,13,14)
  Sprint 6: executor x2 (B-17 || B-21)

[ultraqa]
  커버리지 확인 → 미달 모듈 식별 → 테스트 추가 → 재확인
  Backend: 90% → 94% → 97.59%
  Frontend: 88% → 91% → 93.52%

[code-review + security-review]
  36개 모듈 품질 검증
  API 보안, 인증 토큰 관리, 입력 검증 확인

[git-master + writer]
  Sprint별 atomic commit
  CLAUDE.md, 문서 최종 업데이트
```

---

## 5. Agent 선택 기준 (Model Routing)

| 복잡도 | Model | 비용 | 사용 기준 |
|--------|-------|------|-----------|
| 단순 | Haiku | 최저 | 파일 검색, 단순 테스트 추가, 문서 작성 |
| 표준 | Sonnet | 중간 | 기능 구현, 디버깅, UI 개발 (대부분의 작업) |
| 복잡 | Opus | 최고 | 아키텍처 설계, 전략 로직, 보안 리뷰, 계획 수립 |

### StockAgent 태스크별 권장 Tier

| Tier | 태스크 예시 |
|------|------------|
| **Haiku** | B-1 셋업, F-1 셋업, 커버리지 테스트 추가, CLAUDE.md 업데이트 |
| **Sonnet** | B-3~B-12 클라이언트 구현, B-14~B-16 API 구현, F-3~F-14 컴포넌트 |
| **Opus** | B-13 Strategy Engine, B-21 Parameter Tuner, 아키텍처 검증, 보안 리뷰 |

---

## 6. 핵심 인사이트

### 병렬 실행이 핵심

StockAgent는 36개 태스크가 명확한 의존성 그래프를 가지고 있어 `ultrawork`로 Sprint당 최대 10개 병렬 실행이 가능했다. 단일 executor로 순차 실행 시 36단계가 필요하지만, 병렬 실행으로 **7 Sprint(크리티컬 패스)** 에 완료.

### TDD + autopilot 시너지

`autopilot`이 Sprint 진행을 자동 관리하면서, 각 executor가 TestAgent.md의 TDD 명세를 따라 테스트 선행 개발. 사람의 개입 없이 145 + 64 = **209개 테스트** 자동 생성.

### 커버리지 개선은 반복 패턴

`ultraqa` 패턴(test→verify→fix→repeat)으로 3라운드에 걸쳐 커버리지를 점진적으로 개선:
- Round 1: 기본 구현 (Backend 90%, Frontend 88%)
- Round 2: API 모듈 집중 (Backend 94%, Frontend 91%)
- Round 3: Core 모듈 + 컴포넌트 (Backend 97.59%, Frontend 93.52%)
