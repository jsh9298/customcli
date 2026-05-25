# 🛡️ Humble Custom AI Workstation (v1.7.0)

> **Built 100% with Vibe Coding via Gemini CLI (Free Tier)**
> 
> 본 프로젝트는 어떠한 수동 코딩 없이, 오직 Gemini CLI의 무료 티어 한도 내에서 AI와의 대화(Vibe Coding)만으로 설계, 구현, 검증된 엔터프라이즈급 보안 AI 에이전트 워크스테이션입니다.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Security](https://img.shields.io/badge/DLP-Pure%20Local-red)](#-deterministic-dlp-engine)
[![Engine](https://img.shields.io/badge/Engine-Gemini%20%7C%20Antigravity-orange)](#)

---

## 💎 Project Philosophy: "Humble yet Powerful"

**Humble Custom AI Workstation**은 가장 강력한 AI 에이전트 성능을 누리면서도, 기업의 민감한 데이터가 로컬 환경을 단 1바이트도 벗어나지 않도록 보호하는 것을 최우선 가치로 삼습니다.

### 🌟 Why This Project?
기존의 AI 툴들은 편의성을 위해 보안을 희생하거나 복잡한 설정을 요구합니다. 본 프로젝트는 **"메모리 내 인라인 스트림 가로채기"** 기술과 **결정론적 해시 마스킹**을 통해 오버헤드 없는 완벽한 로컬 DLP를 구현했습니다.

---

## 🚀 Key Features (v1.7.0)

### 🔐 Advanced DLP Engine (Core)
*   **Truncated SHA-256 Masking**: 동일한 민감 정보는 항상 동일한 8글자 해시 토큰(`[EMAIL_5e884898]`)으로 변환되어 에이전트의 문맥 인지 능력을 극대화합니다.
*   **Response Firewall**: AI의 답변 속에 포함된 잠재적 민감 정보까지 출력 직전 실시간 필터링하는 양방향 방화벽.
*   **Hard Drop Guardrails**: 마스킹 규칙 우회 시도(Prompt Injection)를 감지하여 API 호출을 원천 차단.

### 🤖 Intelligent Agentic Control
*   **Smart Autocomplete (Context-Aware)**: `/model`, `/agents`, `/load`, `/skills` 입력 시 현재 환경에 맞는 최적의 인자를 지능적으로 제어합니다.
*   **Background Model Sync**: 백엔드 전환 시 조용히 서버에서 사용 가능한 최신 모델 목록을 가져와 자동완성에 즉시 반영합니다.
*   **MAS & Supervisor Pattern**: 거대 목표를 하위 태스크로 자동 분해하고 병렬 서브에이전트에게 위임 및 검토 루프 수행.

### 💻 Professional Terminal UX
*   **Visual Rewind**: `Esc+Esc`를 통해 과거 대화 시점으로 안전하게 롤백.
*   **Hardened Layout**: `Rich.Panel` 기반의 구조화된 UI를 통해 도커 및 다양한 터미널 환경에서 레이아웃 깨짐을 방지합니다.
*   **Kernel Sandbox**: 에이전트의 셸 명령 실행을 macOS/Linux 커널 레벨에서 물리적으로 격리.

---

## 🛠️ Working Modes

`Shift + Tab`을 통해 실시간으로 전환 가능합니다.

1.  **Default Mode**: 자유롭게 대화하며 도구 사용 시 매번 사용자의 승인을 받습니다.
2.  **Auto-Edit Mode**: 에이전트가 코드를 직접 수정할 수 있는 권한이 부여됩니다. 수정 전 시각적 Diff를 제공합니다.
3.  **Plan Mode**: **강력한 읽기 전용 모드**. 시스템 변경 시도를 코드 레벨에서 차단하여 안전한 코드 분석을 보장합니다.

---

## ⌨️ Productivity Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Shift + Tab` | **Work Mode Cycle** (Default -> Auto-Edit -> Plan) |
| `Tab + Tab` | **UI Density Toggle** (Full <-> Minimal) |
| `Esc + Esc` | **Visual Rewind UI** 호출 (과거 시점으로 롤백) |
| `Ctrl + Y` | **Autonomy Toggle** (Always Approve 모드 전환) |
| `Ctrl + K` | **Bulk Approve**: 모든 대기 중인 도구 실행 일괄 승인 |
| `Ctrl + J` | **Mission Control**: 현재 MAS(멀티 에이전트) 작업 상태 확인 |
| `Ctrl + I` | **Inline Command**: 대화 흐름을 방해하지 않는 원샷 명령 창 호출 |
| `?` | 도움말 패널 출력 (입력창이 비었을 때) |

---

## 🛠️ Installation & Setup

**Windows 사용자**: 커널 격리 기능을 위해 반드시 Docker를 사용하십시오.

```bash
# Clone & Install
git clone https://github.com/your-repo/custom-cli.git
cd custom-cli
pip install -e .

# Run
custom-cli
```

### Docker 실행 (권장)
```bash
docker build -t custom-cli .
docker run -it --rm --env-file .env -v $(pwd):/app/workspace custom-cli
```

---

## 💡 Best Practices

1.  **Context Pinning**: 중요한 아키텍처 설명은 `/pin <index>`를 사용하여 압축 대상에서 영구 제외하십시오.
2.  **@파일 참조**: 질문 시 `@src/core.py`와 같이 입력하면 해당 파일 내용이 자동으로 보안 마스킹 후 지식 베이스에 주입됩니다.
3.  **Smart Suggestion**: 명령어 입력 후 `Tab` 키를 활용하여 모델 이름이나 세션 파일명을 오타 없이 빠르게 선택하십시오.

---

## 🤖 Authorship & Maintenance Notice

*   **Written by**: **Gemini CLI** (100% Autonomous Authoring)
*   **Vibe Orchestrator**: [Your Name/Handle]
*   **Maintenance Policy**: 
    본 프로젝트의 모든 코드, 로직, 문서는 **Gemini CLI**가 직접 작성했습니다. 인간 관리자는 '의도(Vibe)'만을 제공합니다. 
    **"에이전트가 만들었으니, 에이전트가 고친다."** 이것이 본 프로젝트의 핵심 유지보수 철학입니다.
    이슈 발생 시 즉시 **Antigravity/Gemini 에이전트**를 소환하여 해결하십시오.

---

## 📜 License
본 프로젝트는 MIT 라이선스에 따라 자유롭게 사용, 수정, 배포할 수 있습니다. 
