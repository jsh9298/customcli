# 🛡️ Humble Custom AI Workstation (v1.8.6)

> **Built 100% with Vibe Coding via Gemini CLI (Free Tier)**
> 
> 본 프로젝트는 어떠한 수동 코딩 없이, 오직 Gemini CLI의 무료 티어 한도 내에서 AI와의 대화(Vibe Coding)만으로 설계, 구현, 검증된 엔터프라이즈급 보안 AI 에이전트 워크스테이션입니다.

---

## 🚀 Key Features (v1.8.6)

### 🔐 Advanced DLP Engine (Core)
*   **Pure Local Security**: 민감 정보(주민번호, 이메일, 카드번호, API 키 등)를 로컬에서 즉시 마스킹.
*   **Configuration-Driven Architecture**: 소스 코드 내 하드코딩을 완전히 제거하고, 모든 보안 패턴과 정규화 규칙을 `masking_config.yaml`에서 관리합니다.
*   **Token Consistency & Normalization**: 동일한 정보라면 포맷(하이픈, 공백 유무)이 달라도 항상 일관된 토큰으로 변환하여 AI의 문맥 이해도를 높입니다.
*   **Security Audit Logging**: AI로 전송되는 모든 데이터는 마스킹 완료 후 `logs/security_audit.log` 및 `logs/debug_payload.log`에 안전하게 기록됩니다.
*   **Response Firewall**: AI의 답변 속에 포함된 잠재적 민감 정보까지 실시간 필터링.

### 🤖 Intelligent Agentic Control
*   **Aligned Autocomplete**: 명령어와 설명을 시각적으로 깔끔하게 정렬한 자동완성 메뉴를 제공합니다. (타이핑 중 자동 노출, Tab 키는 들여쓰기로 작동)
*   **Robust @File Parsing**: 질문 시 `@path/to/file` 또는 공백이 포함된 경우 `@"path with spaces.md"` 형식을 지원하여 자동 분석을 수행합니다.
*   **Quota-Aware Feedback**: API 할당량(HTTP 429) 초과 시 명확한 안내 메시지를 출력하여 상태를 보고합니다.

---

## 🛠️ Stability Improvements (v1.8.x)

- **[Fix] Quota Handling**: 에이전트 모드 응답 중단 원인이 할당량 초과(HTTP 429)일 경우, 이를 감지하여 사용자에게 명확히 알립니다.
- **[Fix] Docker Volume Conflict**: 로그 파일이 Docker 볼륨 설정으로 인해 디렉토리로 생성되는 문제를 로그 디렉토리 격리 로직으로 완전 해결했습니다.
- **[Fix] Input Session Conflict**: `cmd_inline` (Ctrl+I) 실행 시의 런타임 충돌을 표준 입력 브릿지 기술로 안정화했습니다.

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
