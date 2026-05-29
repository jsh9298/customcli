# 🛡️ Secure AI Workstation (v2.2.0)

본 프로젝트는 보안이 강화된 엔터프라이즈급 AI 개발 워크스테이션입니다. Google Antigravity(`agy`)의 강력한 에이전트 능력과 Gemini CLI의 친숙한 사용자 경험을 결합하여, 로컬 데이터를 안전하게 보호하면서 AI의 도움을 받을 수 있는 최적의 환경을 제공합니다.

---

## ✨ 핵심 기능 상세

### 🔍 1. Privacy-First Local RAG (지식 베이스)
*   **작동 방식**: 내 프로젝트의 코드나 문서를 색인하여 AI가 문맥을 파악하게 합니다.
*   **보안 특점**: 외부 서버(임베딩 API)로 데이터를 보내기 전, **로컬에서 먼저 마스킹**을 수행하여 민감 정보 유출을 원천 차단합니다.
*   **증분 업데이트**: 파일의 수정 시간(`mtime`)을 추적하여 변경된 파일만 효율적으로 다시 색인합니다.
*   **경로 필터링**: `agent_config.yaml`의 `exclude_paths` 설정을 기반으로 `.git`, `.env`, `*.log` 등 민감 경로는 색인 대상에서 자동 제외됩니다.

### 🔐 2. 실시간 로컬 DLP (데이터 보호)
*   **입력 마스킹**: AI에게 질문을 던지기 전 이메일, 카드번호, API 키 등을 자동으로 감지하여 가명화합니다.
*   **응답 정화**: AI의 답변 속에 포함될 수 있는 민감한 코드나 데이터도 사용자에게 보여주기 전 한 번 더 검사합니다.

### 🎭 3. 듀얼 모드 워크스테이션
*   **Agents 모드**: 자율적인 태스크 수행, 복잡한 도구(MCP) 연동, 미션 목표 달성에 최적화.
*   **Chat 모드**: 가벼운 질의응답, 세션 관리, 히스토리 롤백 등에 최적화.

### ⚡ 4. Context Compression V2 (자동 컨텍스트 압축)
*   `agent_config.yaml`의 `compression_threshold` 값(기본: 10턴)을 초과하면 대화 히스토리를 자동 압축합니다.
*   핀고정(`pinned`) 메시지와 최신 대화는 보존하며, 오래된 내용만 의미 있게 요약합니다.

### 🎯 5. Agent Orchestrator & Skill Manager
*   **Orchestrator**: `/goal` 명령으로 미션 목표를 설정하고, Supervisor 패턴을 통해 하위 태스크로 자동 분해합니다.
*   **Skill Manager**: `.antigravity/skills/` 디렉토리에 프롬프트 세트를 저장/로드합니다.

---

## ⌨️ 명령어 상세 가이드 (Command Reference)

모든 명령어는 **하이브리드 패턴**을 지원합니다. 인자 없이 입력하면 화살표 키 인터랙티브 메뉴가 나타납니다.

| 명령어 | 사용 예시 | 상세 설명 |
| :--- | :--- | :--- |
| **`/mode`** | `/mode chat` | Gemini(대화) 스타일과 Antigravity(에이전트) 스타일 간 전환 |
| **`/config`** | `/config` | 모델명, 온도, 샌드박스 등 **영구 설정**을 변경하는 UI 진입 (Agents) |
| **`/settings`** | `/settings` | 영구 설정 변경 UI (Chat) |
| **`/rag`** | `/rag scan` | 워크스페이스 파일을 분석하여 지식 베이스 구축 및 브라우징 |
| **`/skills`** | `/skills` | 저장된 AI 스킬(지침 세트)을 로드하거나 현재 대화를 스킬로 저장 |
| **`/save`** | `/save my_project` | 현재 대화 상태와 마스킹 맵을 파일로 저장 |
| **`/load`** | `/load my_project` | 저장된 세션 불러오기 |
| **`/undo`** | `/undo` | 대화 내역을 단계별로 확인하고 특정 시점으로 즉시 롤백 |
| **`/goal`** | `/goal "Refactor UI"` | 에이전트의 현재 미션 목표를 설정하고 단계별 진행 상황 확인 |
| **`/model`** | `/model gemini-3.5-pro` | AI 모델 변경 |
| **`/theme`** | `/theme hacker` | 터미널 색상 테마 변경 (`neon`, `hacker`, `classic`) |
| **`/mcp`** | `/mcp` | MCP 서버 연결 관리 |
| **`/permissions`** | `/permissions review` | AI 도구 실행 자율성 권한 설정 |
| **`/shells`** | `/shells` | 백그라운드 프로세스 대시보드 |
| **`/clear`** | `/clear` | 화면 초기화 |
| **`/exit`** | `/exit` | 종료 |

### 💡 팁: 파일 참조 기능 (`@`)
대화 중 `@파일명`을 입력하면 해당 파일의 내용이 자동으로 마스킹되어 질문에 포함됩니다.
*   예: `이 코드의 버그를 찾아줘 @src/core.py`
*   공백 포함 시: `이 문서를 요약해줘 @"docs/manual v2.md"`

### 💡 팁: 인라인 셸 명령 (`!`)
`!` 접두사로 셸 명령을 직접 실행할 수 있습니다.
*   예: `!ls -la`, `!git status`

---

## 🚀 빠른 시작 가이드 (Installation)

### 1. 환경 설정
프로젝트 루트에 `.env` 파일을 생성하고 API 키를 입력합니다.
```env
GEMINI_API_KEY=your_api_key_here
```

### 2. 실행 (Docker 권장)
별도의 환경 구축 없이 도커를 통해 즉시 실행할 수 있습니다.

**Linux / macOS:**
```bash
# 빌드
docker build -t custom-cli .

# 실행 (로그 및 워크스페이스 볼륨 마운트 권장)
docker run -it --rm --env-file .env \
  -v /path/to/your/workspace:/app/workspace \
  -v $(pwd)/logs:/app/logs \
  custom-cli
```

**Windows (PowerShell):**
```powershell
# 빌드
docker build -t custom-cli .

# 실행
docker run -it --rm --env-file .env `
  -v "D:\your\workspace:/app/workspace" `
  -v "${PWD}/logs:/app/logs" `
  custom-cli
```

> **⚠️ 주의**: Windows에서는 `$(pwd)` 대신 `"${PWD}"` 또는 절대 경로를 사용하세요.

---

## 🧪 시스템 무결성 점검 (Self-Check)
워크스테이션은 실행 시 다음 사항을 자동으로 점검합니다.
*   `agent_config.yaml` 파일 존재 여부 및 문법 확인
*   필요한 Python 라이브러리(`rich`, `prompt_toolkit`, `yaml` 등) 로드 상태
*   로컬 로그 디렉토리 권한

---

## 🛠️ v2.2.0 변경 내역 (Bug Fixes)

| 구분 | 내용 |
| :--- | :--- |
| 🐛 **[Fix] 진입점 오류** | `core.py`에 `main()` 함수 누락으로 발생하던 `ImportError: cannot import name 'main'` 오류 수정 |
| 🐛 **[Fix] AttributeError** | `UnifiedSecureCLI`에 `orchestrator`, `skill_manager` 인스턴스 초기화 누락 수정 |
| 🐛 **[Fix] AttributeError** | RAG 스캔 시 호출하는 `is_path_ignored()` 메서드 누락 수정 |
| 🐛 **[Fix] TypeError** | `/shells`, `/permissions`, `/skills` 명령어의 잘못된 `ask_selection` 인자 수정 |
| 🗑️ **[Cleanup] 파일 제거** | `commands/handlers.py` (레거시) 파일 삭제 — `commands/handlers/` 패키지와의 충돌 방지 |
| ✨ **[Feature] 자동 압축** | 대화 턴이 `compression_threshold` 초과 시 `ContextCompressor`가 자동 실행되도록 연동 |

---

## 🤖 저작권 및 유지보수
*   **Version**: v2.2.0 (Stability & Integration Edition)
*   **Maintainer**: Antigravity (Autonomous Authoring)
*   **License**: MIT
