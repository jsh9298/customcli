# 🛠️ Antigravity Maintenance Guide: Agent Edition (v1.8.3)

> **Handover Note**: 본 문서는 v1.8.3 작성자인 **Antigravity 에이전트**가 미래의 유지보수 담당자를 위해 작성한 기술 지침서입니다. v1.8.3의 테마는 **"보안 가시성 확보 및 입력 안정화"**입니다.

---

## 🏗️ 1. Technical Debt & Verified Tasks
v1.8.3 릴리즈에서 해결된 주요 기술 부채입니다.

- [x] **Input Loop Integrity**: `cmd_inline` 내에서 `prompt-toolkit`을 중첩 호출할 때 발생하는 `asyncio.run()` 충돌을 표준 `input()` 및 `run_in_terminal` 조합으로 해결.
- [x] **Path Parsing Logic**: `@path` 참조 시 정규식을 개선하여 공백이 포함된 경로나 따옴표로 감싸진 경로를 처리할 수 있도록 보강.
- [x] **Security Auditing**: `PayloadLogger` 모듈을 신설하여 AI로 송신되는 마스킹 완료본을 `logs/security_audit.log`에 기록함으로써 보안 레이어의 실효성 검증 가능.
- [x] **UI Cleanup**: 사용자 요청에 따라 불안정한 상태 줄(Status line)과 명령어 자동완성 기능을 제거하여 런타임 안정성 확보.

---

## 🧪 2. Strict Validation Protocols
모든 수정 후 반드시 수행해야 하는 검증 절차입니다.

1.  **Security Audit Log Check**: 대화 후 `logs/security_audit.log`를 열어 민감 정보가 정상적으로 마스킹된 상태로 기록되었는지 전수 검토할 것.
2.  **Special Path Test**: `@workspace/테스트 copy.md`와 같은 공백 포함 경로가 정상적으로 주입되는지 확인할 것.
3.  **Inline Session Stress Test**: 대화 도중 `Ctrl+I`를 여러 번 눌러 세션이 꼬이지 않는지 확인할 것.

---

## 📉 3. Troubleshooting (Known Issues)
- **Agent Mode Connectivity**: 여전히 Agent 모드 응답이 불안정할 경우, `PayloadLogger`를 통해 전송된 JSON 구조가 Antigravity 서버 규격을 준수하는지 대조 필요.
- **Docker Mounts**: 로그 파일 조회를 위해 Docker 실행 시 `logs` 디렉토리를 볼륨 마운트하는 것을 권장.

---

## 📈 4. Upgrade Roadmap (Next Vibe)
1.  **Local RAG Integration**: 로컬 벡터 DB 연동.
2.  **Advanced MAS**: Supervisor 패턴의 동적 위임 고도화.

---
**Message to Future Agent**: "보안은 보이지 않는 곳에서 증명되어야 한다. 이제 로그를 통해 우리의 무결성을 증명하라."
