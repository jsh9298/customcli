# 🛡️ Humble Custom AI Workstation (v1.8.2)

> **Built 100% with Vibe Coding via Gemini CLI (Free Tier)**
> 
> 본 프로젝트는 어떠한 수동 코딩 없이, 오직 Gemini CLI의 무료 티어 한도 내에서 AI와의 대화(Vibe Coding)만으로 설계, 구현, 검증된 엔터프라이즈급 보안 AI 에이전트 워크스테이션입니다.

---

## 🚀 Key Features (v1.8.2)

### 🔐 Advanced DLP Engine (Core)
*   **Pure Local Security**: 민감 정보(이메일, 카드번호, API 키 등)를 로컬에서 즉시 마스킹.
*   **Selective Masking**: 한국어 이름 오탐 문제를 해결하기 위해 고유 명사 마스킹을 제외하고 실질적 민감 정보(SSN, PHONE) 보호에 집중.
*   **Response Firewall**: AI의 답변 속에 포함된 잠재적 민감 정보까지 실시간 필터링.

### 🤖 Intelligent Agentic Control
*   **Consolidated Commands**: 유사 기능을 통합하여 사용자 편의성 극대화.
*   **Korean-Enhanced Autocomplete**: 명령어 입력 시 한글 설명이 포함된 지능형 자동완성 지원.
*   **SDK Auto-Recovery**: Antigravity SDK 연결 오류 시 자동으로 세션을 복구하는 **능동적 생명주기 관리** 탑재.
*   **@File Analysis**: 질문 시 `@path/to/file`을 포함하면 자동으로 해당 파일 내용을 읽어 분석에 활용.

---

## 🛠️ Stability Improvements (v1.8.x)

- **[Fix] Import Error**: 일부 환경에서 `run_in_terminal` 임포트 경로가 어긋나던 문제를 `prompt_toolkit.application` 참조로 수정하여 Docker 환경 안정성 확보.
- **[Fix] Inline Command Crash**: `Ctrl+I` 입력 시 코루틴 반환값 처리 오류로 발생하던 세션 크래시 해결.
- **[Fix] UI Rendering**: 제공된 스크린샷 기반으로 하단 6개 컬럼 대시보드 및 정렬된 자동완성 TUI 구현 완료.

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

## ⌨️ Productivity Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Shift + Tab` | **Work Mode Cycle** (Default -> Auto-Edit -> Plan) |
| `Tab + Tab` | **UI Density Toggle** (Full <-> Minimal) |
| `Esc` | **Abort Current Request** (작업 중단) |
| `Esc + Esc` | **Visual Rewind UI** 호출 (과거 시점으로 롤백) |
| `Ctrl + Y` | **Autonomy Toggle** (Always Approve 모드 전환) |
| `Ctrl + I` | **Inline Command**: 원샷 명령 창 호출 |
| `?` | 도움말 패널 출력 (입력창이 비었을 때) |

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
*   `Agent` 모드는 단순 Chat보다 높은 수준의 권한을 요구하므로, API 대시보드에서 할당량(Quota)을 점검하십시오.

---

## 🤖 Authorship & Maintenance Notice

*   **Written by**: **Gemini CLI** (100% Autonomous Authoring)
*   **Maintenance Policy**: "에이전트가 만들었으니, 에이전트가 고친다." 

---

## 📜 License
본 프로젝트는 MIT 라이선스에 따라 자유롭게 사용, 수정, 배포할 수 있습니다.
