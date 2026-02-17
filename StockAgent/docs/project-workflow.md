# 주식 거래 시스템 설계 작업 플로우

## 전체 작업 흐름

```mermaid
flowchart TD
    Start([시작: 주식 투자 시뮬레이터 개발 요청]) --> Step1

    Step1[Step 1: 시뮬레이터 기능 정의]
    Step1 --> Step1a[Tasks 정의]
    Step1 --> Step1b[Agents 정의]
    Step1 --> Step1c[Skills 정의]

    Step1a --> Output1[📄 시뮬레이터 요구사항]
    Step1b --> Output1
    Step1c --> Output1

    Output1 --> Decision1{실제 거래 기능 추가?}

    Decision1 -->|Yes| Step2[Step 2: 실전 거래 확장 설계]
    Decision1 -->|No| End1[시뮬레이터만 개발]

    Step2 --> Step2a[Dual-Mode 설계]
    Step2 --> Step2b[증권사 API 연동 계획]
    Step2 --> Step2c[보안/리스크 관리 추가]

    Step2a --> Output2[📄 통합 플랫폼 설계]
    Step2b --> Output2
    Step2c --> Output2

    Output2 --> Decision2{아키텍처 선택}

    Decision2 -->|엔터프라이즈| Step3[Step 3: 마이크로서비스 설계]
    Decision2 -->|개인용| Step4[Step 4: 심플 아키텍처 설계]

    Step3 --> Step3a[11개 마이크로서비스 분할]
    Step3 --> Step3b[인프라 구성]
    Step3 --> Step3c[30주 개발 로드맵]

    Step3a --> Output3[📄 엔터프라이즈 아키텍처 문서]
    Step3b --> Output3
    Step3c --> Output3

    Output3 --> Review1{복잡도 평가}
    Review1 -->|너무 복잡| Step4
    Review1 -->|적합| Tech1[기술 스택 선택]

    Step4 --> Step4a[3개 서비스로 단순화]
    Step4 --> Step4b[Modular Monolith 패턴]
    Step4 --> Step4c[10주 개발 로드맵]
    Step4 --> Step4d[비용 최적화: $2000 → $20]

    Step4a --> Output4[📄 개인용 아키텍처 문서]
    Step4b --> Output4
    Step4c --> Output4
    Step4d --> Output4

    Output4 --> Tech1[Step 5: 기술 스택 선택]

    Tech1 --> Tech1a{Python vs Node.js}

    Tech1a -->|Python FastAPI| Reason1[이유: 증권사 SDK 지원]
    Tech1a -->|Node.js NestJS| Reason2[이유: 타입 안정성]

    Reason1 --> Compare[시장 조사 & 비교 분석]
    Reason2 --> Compare

    Compare --> Compare1[채용 시장 분석]
    Compare --> Compare2[금융 분야 점유율]
    Compare --> Compare3[라이브러리 생태계]

    Compare1 --> Output5[📊 기술 스택 비교 분석]
    Compare2 --> Output5
    Compare3 --> Output5

    Output5 --> Final{최종 결정}

    Final -->|실전 거래 목표| Rec1[✅ Python FastAPI 추천]
    Final -->|취업 포트폴리오| Rec2[⚖️ NestJS 고려 가능]

    Rec1 --> Next[다음 단계: 구현 시작]
    Rec2 --> Next

    Next --> End([🎯 설계 완료, 개발 준비])

    style Start fill:#e1f5ff
    style End fill:#c8e6c9
    style End1 fill:#fff9c4
    style Output1 fill:#fff3e0
    style Output2 fill:#fff3e0
    style Output3 fill:#fff3e0
    style Output4 fill:#fff3e0
    style Output5 fill:#fff3e0
    style Rec1 fill:#c8e6c9
    style Rec2 fill:#fff9c4
```

---

## 각 단계별 상세 플로우

### Step 1: 시뮬레이터 기능 정의

```mermaid
flowchart LR
    A[요구사항 수집] --> B[기능 분류]
    B --> C1[핵심 기능]
    B --> C2[UI/UX]
    B --> C3[고급 기능]

    C1 --> D[Tasks 정의]
    C2 --> D
    C3 --> D

    D --> E[Agents 역할 배정]
    E --> F[Skills 추출]

    F --> G[산출물: 초기 설계서]

    style G fill:#c8e6c9
```

---

### Step 2: 실전 거래 확장

```mermaid
flowchart TD
    A[시뮬레이터 기능] --> B{확장 전략}

    B --> C[Trading Abstraction Layer]
    B --> D[증권사 API 연동]
    B --> E[보안 강화]

    C --> F[Simulator Engine]
    C --> G[Live Trading Engine]

    D --> H[키움증권]
    D --> I[이베스트]
    D --> J[Alpaca]

    E --> K[2FA]
    E --> L[API Key 암호화]
    E --> M[리스크 관리]

    F --> N[통합 인터페이스]
    G --> N

    H --> O[Broker Connector]
    I --> O
    J --> O

    K --> P[보안 계층]
    L --> P
    M --> P

    N --> Q[확장된 설계서]
    O --> Q
    P --> Q

    style Q fill:#c8e6c9
```

---

### Step 3: 마이크로서비스 아키텍처

```mermaid
flowchart TD
    A[도메인 분석] --> B[서비스 분할]

    B --> C1[User Service]
    B --> C2[Account Service]
    B --> C3[Trading Service]
    B --> C4[Market Data Service]
    B --> C5[Portfolio Service]
    B --> C6[Risk Service]
    B --> C7[Broker Service]
    B --> C8[Notification Service]
    B --> C9[Analytics Service]
    B --> C10[Settlement Service]
    B --> C11[Audit Service]

    C1 --> D[인프라 설계]
    C2 --> D
    C3 --> D
    C4 --> D
    C5 --> D
    C6 --> D
    C7 --> D
    C8 --> D
    C9 --> D
    C10 --> D
    C11 --> D

    D --> E1[API Gateway]
    D --> E2[Service Mesh]
    D --> E3[Kafka + RabbitMQ]
    D --> E4[Database per Service]
    D --> E5[Kubernetes]

    E1 --> F[30주 로드맵]
    E2 --> F
    E3 --> F
    E4 --> F
    E5 --> F

    F --> G{비용 분석}
    G --> H[$2000/월]
    H --> I{평가}
    I -->|개인용으로 과함| J[재설계 필요]

    style H fill:#ffcdd2
    style J fill:#fff9c4
```

---

### Step 4: 심플 아키텍처로 재설계

```mermaid
flowchart TD
    A[11개 서비스] --> B{통합 전략}

    B --> C[Backend API<br/>Modular Monolith]
    B --> D[Market Data Service<br/>독립]
    B --> E[Broker Connector<br/>독립]

    C --> C1[Auth Module]
    C --> C2[Trading Module]
    C --> C3[Portfolio Module]
    C --> C4[Risk Module]
    C --> C5[Analytics Module]
    C --> C6[Notification Module]

    C1 --> F[단일 배포 단위]
    C2 --> F
    C3 --> F
    C4 --> F
    C5 --> F
    C6 --> F

    D --> G[실시간 데이터 처리]
    E --> H[증권사 API 통합]

    F --> I[통합 데이터베이스]
    G --> I
    H --> I

    I --> J[Docker Compose]
    J --> K[배포 전략]

    K --> L1[VPS: $20/월]
    K --> L2[관리형: $45/월]
    K --> L3[홈서버: $6/월]

    L1 --> M[10주 로드맵]
    L2 --> M
    L3 --> M

    M --> N[개인용 아키텍처 완성]

    style N fill:#c8e6c9
```

---

### Step 5: 기술 스택 비교

```mermaid
flowchart TD
    A[기술 스택 선택] --> B{후보군}

    B --> C[Python FastAPI]
    B --> D[Node.js NestJS]

    C --> C1[증권사 SDK 지원]
    C --> C2[데이터 분석 생태계]
    C --> C3[백테스팅 라이브러리]

    D --> D1[TypeScript 타입 안정성]
    D --> D2[높은 채용 수요]
    D --> D3[풍부한 npm 생태계]

    C1 --> E{금융 분야<br/>적합도}
    C2 --> E
    C3 --> E

    D1 --> F{범용<br/>개발 적합도}
    D2 --> F
    D3 --> F

    E --> G[Python 점유율: 70%]
    F --> H[Node.js 채용: 더 많음]

    G --> I{프로젝트 목표}
    H --> I

    I -->|실전 거래| J[✅ Python FastAPI]
    I -->|취업 포트폴리오| K[⚖️ NestJS 고려]

    J --> L[최종 결정]
    K --> L

    style J fill:#c8e6c9
    style K fill:#fff9c4
```

---

## 의사결정 트리

```mermaid
flowchart TD
    Start([주식 거래 시스템 개발]) --> Q1{목적?}

    Q1 -->|개인 사용| Q2{실전 거래?}
    Q1 -->|상용 서비스| Enterprise[엔터프라이즈 설계]

    Q2 -->|Yes| Q3{예산?}
    Q2 -->|No| Simple1[시뮬레이터만<br/>심플 설계]

    Q3 -->|$20-50/월| Personal[개인용 설계<br/>3 Services]
    Q3 -->|$500+/월| Enterprise

    Enterprise --> Tech1[Java/Go<br/>Kubernetes]
    Personal --> Tech2{선호 언어?}
    Simple1 --> Tech2

    Tech2 -->|Python 경험| Python[FastAPI 선택]
    Tech2 -->|JavaScript 경험| Node[NestJS 선택]
    Tech2 -->|모름| Q4{증권사 연동?}

    Q4 -->|필요| Python
    Q4 -->|불필요| Node

    Python --> Impl1[Python 구현 시작]
    Node --> Impl2[Node.js 구현 시작]
    Tech1 --> Impl3[MSA 구현 시작]

    style Personal fill:#c8e6c9
    style Python fill:#81c784
    style Impl1 fill:#4caf50
```

---

## 산출물 요약

```mermaid
flowchart LR
    A[작업 과정] --> B[산출물]

    B --> C1[📄 시뮬레이터 설계<br/>Tasks/Agents/Skills]
    B --> C2[📄 실전 거래 확장<br/>Dual-Mode 설계]
    B --> C3[📄 마이크로서비스 아키텍처<br/>11 Services, 30주, $2000/월]
    B --> C4[📄 개인용 아키텍처<br/>3 Services, 10주, $20/월]
    B --> C5[📊 기술 스택 비교<br/>Python vs Node.js]

    C1 --> D[현재 위치]
    C2 --> D
    C3 --> D
    C4 --> D
    C5 --> D

    D --> E[다음 단계:<br/>구현 시작]

    style D fill:#fff9c4
    style E fill:#c8e6c9
```

---

## 타임라인

```mermaid
gantt
    title 설계 작업 타임라인
    dateFormat HH:mm
    axisFormat %H:%M

    section 요구사항 분석
    시뮬레이터 기능 정의    :done, req1, 00:00, 30m
    Tasks/Agents/Skills     :done, req2, 00:30, 30m

    section 기능 확장
    실전 거래 기능 추가      :done, exp1, 01:00, 40m
    보안/리스크 설계        :done, exp2, 01:40, 20m

    section 아키텍처 설계
    마이크로서비스 설계     :done, arch1, 02:00, 60m
    개인용 재설계          :done, arch2, 03:00, 50m

    section 기술 선택
    기술 스택 비교         :done, tech1, 03:50, 40m
    최종 추천             :done, tech2, 04:30, 20m

    section 문서화
    플로우차트 작성        :active, doc1, 04:50, 30m
```

---

## 핵심 의사결정 포인트

```mermaid
mindmap
  root((주식 거래<br/>시스템))
    Architecture
      Microservices
        11 Services
        $2000/월
        30주
        ❌ 개인용 과함
      Modular Monolith
        3 Services
        $20/월
        10주
        ✅ 개인용 최적
    Technology
      Backend
        Python FastAPI
          증권사 SDK
          데이터 분석
          백테스팅
          ✅ 금융 특화
        Node.js NestJS
          TypeScript
          채용 유리
          생태계 풍부
          ⚖️ 범용 개발
      Frontend
        React + TypeScript
        TailwindCSS
        Recharts
    Deployment
      VPS
        $20/월
        완전 제어
      Managed
        $45/월
        관리 편함
      Home Server
        $6/월
        최저 비용
```

---

## 다음 단계 로드맵

```mermaid
flowchart TD
    Now[현재: 설계 완료] --> Phase1[Phase 1: 환경 설정]

    Phase1 --> P1T1[프로젝트 구조 생성]
    Phase1 --> P1T2[Docker Compose 설정]
    Phase1 --> P1T3[DB 스키마 구현]

    P1T1 --> Phase2[Phase 2: Backend 개발]
    P1T2 --> Phase2
    P1T3 --> Phase2

    Phase2 --> P2T1[인증 모듈]
    Phase2 --> P2T2[거래 모듈]
    Phase2 --> P2T3[포트폴리오 모듈]

    P2T1 --> Phase3[Phase 3: Market Data]
    P2T2 --> Phase3
    P2T3 --> Phase3

    Phase3 --> P3T1[실시간 시세]
    Phase3 --> P3T2[WebSocket]

    P3T1 --> Phase4[Phase 4: Frontend]
    P3T2 --> Phase4

    Phase4 --> P4T1[React 앱]
    Phase4 --> P4T2[차트 컴포넌트]

    P4T1 --> MVP[MVP 완성<br/>시뮬레이터 동작]
    P4T2 --> MVP

    MVP --> Phase5[Phase 5: 증권사 연동]
    Phase5 --> Phase6[Phase 6: 고급 기능]
    Phase6 --> Final[완성]

    style Now fill:#fff9c4
    style MVP fill:#81c784
    style Final fill:#4caf50
```

---

## 프로젝트 구조 (최종)

```mermaid
flowchart TD
    Root[personal-trading-system/]

    Root --> Backend[backend/<br/>Python FastAPI]
    Root --> Market[market-data-service/<br/>Python/Go]
    Root --> Broker[broker-connector/<br/>Python]
    Root --> Frontend[frontend/<br/>React + TS]
    Root --> Docker[docker-compose.yml]
    Root --> Docs[docs/]

    Backend --> B1[src/<br/>모듈별 디렉토리]
    Backend --> B2[tests/]
    Backend --> B3[requirements.txt]

    B1 --> B1a[auth/]
    B1 --> B1b[trading/]
    B1 --> B1c[portfolio/]
    B1 --> B1d[risk/]
    B1 --> B1e[analytics/]

    Market --> M1[api/]
    Market --> M2[providers/]
    Market --> M3[cache/]

    Broker --> Br1[brokers/<br/>증권사별 구현]
    Broker --> Br2[adapters/]

    Frontend --> F1[src/<br/>components/]
    Frontend --> F2[pages/]
    Frontend --> F3[hooks/]

    style Root fill:#e1f5ff
    style Backend fill:#fff3e0
    style Market fill:#fff3e0
    style Broker fill:#fff3e0
    style Frontend fill:#fff3e0
```

---

## 요약: 작업 과정

1. **Step 1**: 시뮬레이터 기능 정의 → Tasks, Agents, Skills 도출
2. **Step 2**: 실전 거래 확장 → Dual-Mode 설계, 보안 강화
3. **Step 3**: 마이크로서비스 설계 → 11개 서비스, 복잡도 높음 ❌
4. **Step 4**: 개인용 재설계 → 3개 서비스, 비용/시간 90% 절감 ✅
5. **Step 5**: 기술 스택 선택 → Python (금융 특화) vs Node.js (범용)

**현재 상태**: 설계 완료, 구현 준비 완료
**다음 단계**: 개발 환경 설정 및 구현 시작
