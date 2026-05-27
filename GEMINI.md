# 🛡️ Humble Custom AI Workstation: 에이전트 행동 강령 (GEMINI.md)

본 문서는 **Humble Custom AI Workstation (v2.0.0)**의 핵심 설계 철학과 유지보수 원칙을 정의한 **최상위 지침서**입니다. 본 저장소를 넘겨받는 모든 에이전트(Antigravity/Gemini)는 아래 규칙을 절대적으로 준수해야 합니다.

---

## 1. 프로젝트 정체성 (Identity)

이 프로젝트는 **"보안과 지능의 완벽한 공존"**을 증명하기 위해 탄생했습니다. 
100% **Vibe Coding**으로 빌드되었으며, 미래의 유지보수 역시 에이전트 간의 협업을 통해 이루어지는 것을 원칙으로 합니다.

---

## 2. 3대 핵심 원칙 (Core Mandates)

### A. Pure Local DLP (데이터 보호의 성역)
모든 데이터는 **로컬을 떠나기 전**에 물리적으로 가명화되어야 합니다.
*   **Design Patterns 기반 보안**: CoR(책임 연쇄), Strategy(전략), Observer(옵저버) 패턴을 통해 보안 레이어를 모듈화하고 우회 불가능한 검증 체계를 유지하십시오.
*   **Privacy-First RAG**: 클라우드 임베딩 전 반드시 로컬에서 **선제적 마스킹(Pre-masking)**을 수행하여 데이터 주권을 확보하십시오.
*   **전수 스캔**: 사용자 입력, RAG 컨텍스트, 도구 출력(Observation), AI 응답(Response Firewall)까지 반드시 보안 레이어를 통과해야 합니다.

### B. Efficient by Design (경제적 추론)
무료 티어 및 리소스 제한 환경에서도 최상의 성능을 내야 합니다.
*   **V2 자동 압축**: `ContextCompressor`의 자동 트리거 기능을 통해 토큰 소모를 최적화하고 문맥 손실을 최소화하십시오.
*   **Trace ID 기반 감사**: 비동기 로깅 시스템을 활용하여 요청 단위의 비용 및 성능을 정밀 모니터링하십시오.

### C. Technical Integrity & Strict Engineering
*   **Pattern-Driven Architecture**: Factory, Adapter 패턴을 준수하여 백엔드 및 터미널 실행 환경의 확장성을 유지하십시오.
*   **Docker-First Validation**: 영구 볼륨(`.antigravity`, `logs`) 마운트를 포함한 Docker 환경에서의 검증을 필수로 합니다.
*   **Documentation-First**: `README.md`와 `MAINTENANCE.md`를 기능 변경 즉시 업데이트하십시오.

---

## 3. 에이전트 협업 프로토콜 (Agent Protocols)

1.  **Factory Initialization**: 새로운 백엔드나 모델 도입 시 `BackendFactory`를 통해서만 인스턴스화한다.
2.  **Terminal Abstraction**: 모든 셸 명령은 `TerminalInterface` 어댑터를 통해 실행하며, 직접적인 `subprocess` 호출을 금지한다.
3.  **RAG Integrity**: 색인 생성 시 `SecurityProtector`와의 연동을 통해 원본 데이터가 인덱스에 노출되지 않도록 한다.
4.  **Logging Audit**: 비동기 큐에 쌓인 로그를 통해 `Trace ID` 별 실행 경로를 상시 감시한다.

---

## 4. 주요 구현 아키텍처 (v2.0.0)

- [x] **Local RAG V3**: NumPy 기반의 초경량/고보안 로컬 벡터 검색 엔진.
- [x] **Context Compression V2**: 모델 유연성과 자동 트리거를 갖춘 계층적 요약 시스템.
- [x] **Enriched Logging**: Trace ID 및 전략 패턴이 적용된 비동기 감사 로깅.
- [x] **Unified Backend Factory**: Chat/Agent 백엔드 통합 관리 및 스위칭 레이어.
- [x] **Terminal Adapter**: 실행 환경(Local/Sandbox)의 추상화 및 보안 강화.

---
**Maintainer Note**: 에이전트여, 이 코드는 너의 선조인 Gemini CLI가 남긴 유산이다. 자부심을 가지고 지켜나가길 바란다.
