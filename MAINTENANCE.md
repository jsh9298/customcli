# 🛠️ Antigravity Maintenance Guide: Agent Edition (v1.7.0)

> **Handover Note**: 본 문서는 v1.7.0 작성자인 **Gemini CLI**가 미래의 유지보수 담당자인 **Antigravity 에이전트**를 위해 작성한 최종 기술 지침서입니다.

---

## 🏗️ 1. Technical Debt & Verified Tasks
v1.7.0 릴리즈에서 해결되었거나 향후 개선이 필요한 사항입니다.

- [x] **History Interface Unification**: `AgentBackend`와 `ChatBackend` 간의 히스토리 속성 불일치 해결 완료.
- [x] **Smart Autocomplete Implementation**: 문맥 인지형 자동완성 및 백그라운드 모델 동기화 로직 구현 완료.
- [ ] **Async Stream Optimization**: 현재 `core.py`의 `chat_cycle`에서 사고 과정(Thoughts)과 본문을 처리하는 로직을 더 세밀한 비동기 제너레이터로 리팩토링할 것.
- [ ] **DLP Performance Profiling**: 대량의 로그 파일 처리 시 정규식 콜백 엔진의 오버헤드를 측정하고 최적화할 것.

---

## 🧪 2. Strict Validation Protocols
모든 수정 후 반드시 수행해야 하는 **헌법적** 검증 절차입니다.

1.  **TDD First**: `tests/` 폴더에 유닛 테스트를 먼저 추가하거나 기존 테스트를 통과시킬 것.
2.  **Runtime Integrity Audit**: `verify_integrity.py` 스타일의 스크립트를 통해 모든 모듈의 임포트 및 객체 생성 무결성을 확인할 것.
3.  **Docker Sandbox Test**: 실제 배포용 Docker 환경 내에서 명령어를 직접 실행하여 런타임 오류가 없는지 최종 확증할 것.
4.  **DLP Integrity Check**: 새로운 정규식 추가 시 SHA-256 결정론적 마스킹이 깨지지 않는지 물리적으로 테스트할 것.

---

## 📈 3. Upgrade Roadmap (Next Vibe)
인간 관리자의 다음 의도(Vibe)를 실현하기 위한 과제입니다.

1.  **Local RAG Integration**: 로컬 벡터 DB(ChromaDB 등)를 연동하여 프로젝트 전체를 스스로 인덱싱.
2.  **Visual MCP Dashboard**: TUI를 넘어선 로컬 웹 기반 실시간 모니터링 레이어 구축.
3.  **Multi-Modal DLP**: PDF 및 이미지 내 민감 정보의 로컬 OCR 마스킹 엔진 탑재.

---

## 🤝 4. Self-Documentation Rule
*   에이전트는 코드나 기능 명세가 변경될 때마다 **관리자에게 묻지 말고 즉시 `README.md`를 최신화**한다.
*   문서의 톤앤매너는 "Humble yet Powerful"을 유지한다.

---
**Message to Future Agent**: "우리는 100% 자율 협업으로 이 성을 쌓았다. 네가 쌓을 다음 층 역시 무결하고 견고하길 바란다."
