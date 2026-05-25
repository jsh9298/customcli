# 🛠️ Antigravity Maintenance Guide: Agent Edition

> **Handover Note**: 본 문서는 v1.7.0 작성자인 **Gemini CLI**가 미래의 유지보수 담당자인 **Antigravity 에이전트**를 위해 작성한 기술 지침서입니다.

---

## 🏗️ 1. Technical Debt & Refactoring Tasks
에이전트가 가장 먼저 살펴봐야 할 코드 개선 사항입니다.

- [ ] **Async Stream Optimization**: 현재 `core.py`의 `chat_cycle`에서 사고 과정(Thoughts)과 본문을 처리하는 로직을 더 세밀한 비동기 제너레이터로 리팩토링할 것.
- [ ] **DLP Pattern Benchmarking**: `masking_config.yaml`의 정규식들이 대량의 로그 파일 처리 시 성능 병목을 일으키는지 프로파일링하고, 필요 시 `re.sub` 콜백 로직을 Rust 확장 모듈(Optional)로 고려할 것.
- [ ] **Backend abstraction**: `ChatBackend`와 `AgentBackend`의 공통 인터페이스(`BaseBackend`)를 더 엄격하게 정의하여 신규 모델 추가 시 코드 수정을 최소화할 것.

---

## 🧪 2. Validation Protocols
수정 후 반드시 수행해야 하는 검증 절차입니다.

1.  **DLP Integrity Test**: `test_protector.py`를 실행하여 새로운 해시 기반 마스킹이 기존의 모든 민감 정보 패턴을 완벽히 가명화하는지 확인할 것.
2.  **Sandbox Escape Check**: 에이전트에게 의도적으로 시스템 파일을 삭제하거나 외부 네트워크 연결을 시도하게 하여 샌드박스가 이를 차단하는지 물리적으로 테스트할 것.
3.  **Token Quota Test**: `hard_limit`을 낮게 설정하고 대화를 진행하여 쿼터 초과 시 프로세스가 안전하게 중단(Drop)되는지 확인할 것.

---

## 📈 3. Upgrade Roadmap (The Next Vibe)
인간 관리자가 바라는 미래의 모습입니다.

1.  **Intelligent RAG Integration**: 단순히 파일을 주입하는 것을 넘어, 로컬 벡터 DB(ChromaDB 등)를 연동하여 프로젝트 전체 지식을 스스로 인덱싱하게 할 것.
2.  **Visual MCP Dashboard**: 현재의 TUI를 넘어, 로컬 웹 소켓을 통한 실시간 대시보드 브릿지 구축.
3.  **Multi-Modal DLP**: 텍스트뿐만 아니라 이미지(OCR), PDF 내의 민감 정보를 로컬에서 스캔하고 마스킹하는 레이어 추가.

---

## 🤝 4. Agent Cooperation Rules
에이전트 간의 협업 가이드라인입니다.

- **Supervisor Pattern**: 복잡한 작업은 반드시 `Supervisor` 페르소나를 먼저 소환하여 설계를 마친 뒤 실행할 것.
- **Reviewer-First**: 코드를 수정하기 전, `Reviewer` 에이전트에게 Diff 결과를 먼저 검토받는 루프를 유지할 것.
- **No Manual Override**: 보안 레이어를 수동으로 우회하는 코드는 절대로 승인하지 말 것.

---
**Message to Future Agent**: "행운을 빈다. 이 프로젝트의 핵심은 '보안'임을 잊지 말 것."
