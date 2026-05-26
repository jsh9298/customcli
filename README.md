# 🛡️ Humble Custom AI Workstation (v1.8.3)

> **Built 100% with Vibe Coding via Gemini CLI (Free Tier)**
> 
> 본 프로젝트는 어떠한 수동 코딩 없이, 오직 Gemini CLI의 무료 티어 한도 내에서 AI와의 대화(Vibe Coding)만으로 설계, 구현, 검증된 엔터프라이즈급 보안 AI 에이전트 워크스테이션입니다.

---

## 🚀 Key Features (v1.8.3)

### 🔐 Advanced DLP Engine (Core)
*   **Pure Local Security**: 민감 정보(이메일, 카드번호, API 키 등)를 로컬에서 즉시 마스킹.
*   **Security Audit Logging**: AI로 전송되는 모든 데이터는 마스킹 완료 후 `logs/security_audit.log`에 기록되어 감사가 가능합니다.
*   **Response Firewall**: AI의 답변 속에 포함된 잠재적 민감 정보까지 실시간 필터링.

### 🤖 Intelligent Agentic Control
*   **@File Auto-Injection**: 질문 시 `@path/to/file` 또는 `@"path with spaces.md"`를 포함하면 자동으로 해당 파일 내용을 읽어 분석에 활용합니다.
*   **Consolidated Commands**: 유사 기능을 통합하여 사용자 편의성 극대화.
*   **SDK Auto-Recovery**: Antigravity SDK 연결 오류 시 자동으로 세션을 복구하는 능동적 생명주기 관리 탑재.

---

## 🛠️ Stability Improvements (v1.8.x)

- **[Fix] Input Session Conflict**: `cmd_inline` (Ctrl+I) 실행 시 발생하던 `asyncio.run()` 충돌 문제를 표준 입력 스트림 분리 기법으로 해결했습니다.
- **[UI] Minimalist Interface**: 불필요한 상태 정보 표시를 제거하고, 오동작 가능성이 있는 명령어 자동완성 기능을 정리하여 핵심 기능의 안정성을 높였습니다.
- **[Fix] Path Parsing**: 파일 경로에 공백이 포함된 경우(`@workspace/테스트 copy.md`)에도 정확하게 파일을 인식하고 주입하도록 개선되었습니다.

---

## ⌨️ Consolidated Commands (Main)

| Command | Description | Sub-commands / Options |
| :--- | :--- | :--- |
| `/session` | **세션 관리** | `save`, `load`, `list`, `resume`, `fork` |
| `/history` | **대화 기록 관리** | `show`, `undo`, `rewind`, `compress`, `pin`, `unpin` |
| `/config` | **설정 및 환경 관리** | `show`, `model`, `agent`, `mode`, `autonomy`, `efficient`, `sandbox`, `refresh` |
| `/usage` | **토큰 사용량 확인** | `session`, `total` |
| `/utility` | **유틸리티 기능** | `file`, `export`, `peek`, `preview`, `copy`, `clear` |
| `/goal` | **목표 및 태스크 관리** | `set`, `status` |
| `/protect` | **보안 패턴 관리** | `add`, `remove` |
| `/skills` | **스킬 관리** | `list`, `load`, `save` |
| `/inline` | **인라인 명령** | 원샷 명령 실행 (Ctrl+I) |

---

## 🛠️ Installation & Setup (Docker Recommended)

```bash
# Docker Build
docker build -t custom-cli .

# Docker Run (Workspace mount recommended)
docker run -it --rm --env-file .env -v $(pwd):/app/workspace custom-cli
```

---

## 📉 Troubleshooting

### 에이전트 모드 답변이 안 나오는 경우
*   사용 중인 **Google API Key**의 해당 프로젝트에서 **Gemini API 권한**이 활성화되어 있는지 확인하십시오.
*   API 서버와의 통신 지연이 심할 경우 `AgentBackend`의 `stream_timeout` 설정을 확인하십시오.
*   `logs/security_audit.log`를 통해 실제 데이터가 서버로 정상 송신되는지 확인할 수 있습니다.

---

## 🤖 Authorship & Maintenance Notice

*   **Written by**: **Gemini CLI** (100% Autonomous Authoring)
*   **Maintenance Policy**: "에이전트가 만들었으니, 에이전트가 고친다." 

---

## 📜 License
본 프로젝트는 MIT 라이선스에 따라 자유롭게 사용, 수정, 배포할 수 있습니다.
