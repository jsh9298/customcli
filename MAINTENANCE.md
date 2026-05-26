# 🛠️ Antigravity Maintenance Guide: Agent Edition (v1.8.2)

> **Handover Note**: 본 문서는 v1.8.2 작성자인 **Antigravity 에이전트**가 미래의 유지보수 담당자를 위해 작성한 기술 지침서입니다. v1.8.x 시리즈의 핵심은 **"서비스 안정화 및 UI 정교화"**입니다.

---

## 🏗️ 1. Technical Debt & Verified Tasks
v1.8.2 릴리즈에서 해결된 주요 기술 부채입니다.

- [x] **Import Integrity**: `prompt_toolkit` 버전에 따른 `run_in_terminal` 임포트 경로 불일치 해결 (`application` 모듈로 통합).
- [x] **Coroutine Handling**: `cmd_inline` 내에서 비동기 입력을 처리할 때 발생하는 `coroutine object strip` 에러를 동기식 `prompt` 래퍼로 해결.
- [x] **SDK Lifecycle**: Antigravity SDK의 불안정한 연결을 **능동적 세션 갱신(Proactive Renewal)** 로직으로 보강.
- [x] **UI Consolidation**: 산재해 있던 슬래시 명령어를 `/session`, `/history`, `/config` 등으로 체계적 그룹화.

---

## 🧪 2. Strict Validation Protocols
모든 수정 후 반드시 수행해야 하는 검증 절차입니다.

1.  **Docker Compatibility**: `docker build -t custom-cli .` 후 임포트 에러가 없는지 반드시 확인 (`run_in_terminal` 등).
2.  **Input Interrupt Test**: 대화 도중 `Esc` 키를 눌러 `asyncio.Task`가 정상적으로 취소되는지 물리적으로 테스트할 것.
3.  **File Parsing Verification**: `@path` 참조 시 마스킹 엔진이 파일 내용까지 정상적으로 보호하는지 로그 확인.

---

## 📉 3. Troubleshooting (Known Issues)
- **Agent Mode No Response**: 무료 티어 키 사용 시 Google AI Studio에서 **Gemini API 권한**이 활성화되어 있어야 합니다.
- **CPR Warning**: 일부 터미널(Docker Desktop 등)에서 커서 위치 요청(CPR)을 지원하지 않아 경고가 뜰 수 있으나, 기능상 문제는 없습니다.

---

## 📈 4. Upgrade Roadmap (Next Vibe)
1.  **Local RAG Integration**: 로컬 벡터 DB 연동.
2.  **Multi-Modal DLP**: PDF/이미지 OCR 마스킹.
3.  **Advanced MAS**: 에이전트 간의 자동 협업 루프 정교화.

---
**Message to Future Agent**: "우리는 100% 자율 협업으로 이 성을 쌓았다. 네가 쌓을 다음 층 역시 무결하고 견고하길 바란다."
