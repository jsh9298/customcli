# 🛡️ Humble Custom AI Workstation (v1.7.5)

> **Built 100% with Vibe Coding via Gemini CLI (Free Tier)**
> 
> 본 프로젝트는 어떠한 수동 코딩 없이, 오직 Gemini CLI의 무료 티어 한도 내에서 AI와의 대화(Vibe Coding)만으로 설계, 구현, 검증된 엔터프라이즈급 보안 AI 에이전트 워크스테이션입니다.

---

## 🚀 Key Features (v1.7.5)

### 🔐 Advanced DLP Engine (Core)
*   **Pure Local Security**: 민감 정보(이메일, 카드번호, API 키 등)를 로컬에서 즉시 마스킹.
*   **Selective Masking**: 한국어 이름 오탐 문제를 해결하기 위해 고유 명사 마스킹을 제외하고 실질적 민감 정보(SSN, PHONE) 보호에 집중.
*   **Response Firewall**: AI의 답변 속에 포함된 잠재적 민감 정보까지 실시간 필터링.

### 🤖 Intelligent Agentic Control
*   **Consolidated Commands**: 유사 기능을 통합하여 사용자 편의성 극대화.
*   **Korean-Enhanced Autocomplete**: 명령어 입력 시 한글 설명이 포함된 지능형 자동완성 지원.
*   **SDK Auto-Recovery**: Antigravity SDK 연결 오류 시 자동으로 세션을 복구하는 Retry 로직 탑재.

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

## 🛠️ Working Modes

`Shift + Tab`을 통해 실시간으로 전환 가능합니다.

1.  **Default Mode**: 자유롭게 대화하며 도구 사용 시 매번 사용자의 승인을 받습니다.
2.  **Auto-Edit Mode**: 에이전트가 코드를 직접 수정할 수 있는 권한이 부여됩니다.
3.  **Plan Mode**: **강력한 읽기 전용 모드**. 시스템 변경 시도를 코드 레벨에서 차단합니다.

---

## ⌨️ Productivity Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Shift + Tab` | **Work Mode Cycle** (Default -> Auto-Edit -> Plan) |
| `Tab + Tab` | **UI Density Toggle** (Full <-> Minimal) |
| `Esc + Esc` | **Visual Rewind UI** 호출 (과거 시점으로 롤백) |
| `Ctrl + Y` | **Autonomy Toggle** (Always Approve 모드 전환) |
| `Ctrl + I` | **Inline Command**: 원샷 명령 창 호출 |
| `?` | 도움말 패널 출력 (입력창이 비었을 때) |

---

## 💡 Best Practices

1.  **Context Pinning**: 중요한 아키텍처 설명은 `/history pin <index>`를 사용하여 압축 대상에서 영구 제외하십시오.
2.  **@파일 참조**: 질문 시 `@src/core.py`와 같이 입력하면 해당 파일 내용이 자동으로 보안 마스킹 후 지식 베이스에 주입됩니다.
3.  **Smart Suggestion**: 명령어 입력 후 `Tab` 키를 활용하여 모델 이름이나 세션 파일명을 한글 설명을 보며 선택하십시오.

---

## 🤖 Authorship & Maintenance Notice

*   **Written by**: **Gemini CLI** (100% Autonomous Authoring)
*   **Vibe Orchestrator**: [Your Name/Handle]
*   **Maintenance Policy**: "에이전트가 만들었으니, 에이전트가 고친다." 

---

## 📜 License
본 프로젝트는 MIT 라이선스에 따라 자유롭게 사용, 수정, 배포할 수 있습니다.
