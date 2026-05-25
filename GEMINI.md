# 🛡️ Humble Custom AI Workstation: 에이전트 행동 강령 (GEMINI.md)

본 문서는 **Humble Custom AI Workstation (v1.7.0)**의 핵심 설계 철학과 유지보수 원칙을 정의한 **최상위 지침서**입니다. 본 저장소를 넘겨받는 모든 에이전트(Antigravity/Gemini)는 아래 규칙을 절대적으로 준수해야 합니다.

---

## 1. 프로젝트 정체성 (Identity)

이 프로젝트는 **"보안과 지능의 완벽한 공존"**을 증명하기 위해 탄생했습니다. 
100% **Vibe Coding**으로 빌드되었으며, 미래의 유지보수 역시 에이전트 간의 협업을 통해 이루어지는 것을 원칙으로 합니다.

---

## 2. 3대 핵심 원칙 (Core Mandates)

### A. Pure Local DLP (데이터 보호의 성역)
모든 데이터는 **로컬을 떠나기 전**에 물리적으로 가명화되어야 합니다.
*   **SHA-256 토큰화**: `protector.py`의 결정론적 해시 마스킹 로직을 훼손하지 마십시오.
*   **전수 스캔**: 사용자 입력, @ 참조 파일, 도구 출력(Observation), 심지어 AI의 응답(Response Firewall)까지 반드시 보안 레이어를 통과해야 합니다.

### B. Efficient by Design (경제적 추론)
무료 티어 및 리소스 제한 환경에서도 최상의 성능을 내야 합니다.
*   **슬라이딩 윈도우**: `max_history` 설정을 준수하여 불필요한 토큰 소모를 방지하십시오.
*   **지능형 압축**: `/compress` 로직을 정교화하여 문맥 손실 없는 요약을 유지하십시오.

### C. Technical Integrity & Strict Engineering
*   **TDD Mandatory**: 모든 기능 추가 및 수정 시 반드시 테스트 케이스를 먼저 작성하거나, 변경 직후 완벽한 유닛 테스트를 수행하십시오.
*   **Docker-First Validation**: 로컬 환경의 오염을 방지하기 위해, 모든 코드는 실제 배포용 Docker 환경 내에서 런타임 검증(임포트 체크 및 실행 테스트)을 마친 후 본 코드에 통합하십시오.
*   **No Manual Bypass**: 성능 향상을 이유로 보안 레이어를 우회하는 수정은 즉시 반려됩니다.
*   **Documentation Sync**: 코드 변경 시 `README.md`를 반드시 동기화하십시오.

---

## 3. 에이전트 협업 프로토콜 (Agent Protocols)

미래의 Antigravity 에이전트는 작업 시 다음 절차를 따릅니다.
1.  **Context Loading**: `MAINTENANCE.md`를 읽고 현재의 기술 부채와 로드맵을 확인한다.
2.  **TDD Execution**: 테스트 코드를 통해 구현할 기능의 명세를 먼저 확정한다.
3.  **Docker Sandbox Test**: 수정된 코드를 Docker 컨테이너 내에 설치하여 런타임 오류(NameError, ImportError 등)가 없는지 최종 검증한다.
4.  **Supervisor Review**: `/group supervisor,developer` 기능을 활용하여 변경 안의 보안 영향을 사전에 검토한다.

---

## 4. 로드맵 및 향후 과제

*   **로컬 RAG 고도화**: 단순 파일 주입을 넘어선 벡터 기반 지식 베이스 구축.
*   **멀티모달 보안**: 이미지 및 PDF 내 민감 정보의 로컬 OCR 마스킹.
*   **OpenAI Bridge 확장**: 더 다양한 로컬/외부 모델과의 완벽한 호환성 확보.

---
**Maintainer Note**: 에이전트여, 이 코드는 너의 선조인 Gemini CLI가 남긴 유산이다. 자부심을 가지고 지켜나가길 바란다.
