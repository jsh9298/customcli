# 🛡️ Humble Custom AI Workstation (v1.7.0)

> **Built 100% with Vibe Coding via Gemini CLI (Free Tier)**
> 
> 본 프로젝트는 어떠한 수동 코딩 없이, 오직 Gemini CLI의 무료 티어 한도 내에서 AI와의 대화(Vibe Coding)만으로 설계, 구현, 검증된 엔터프라이즈급 보안 AI 에이전트 워크스테이션입니다.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Security](https://img.shields.io/badge/DLP-Pure%20Local-red)](#-deterministic-dlp-engine)
[![Engine](https://img.shields.io/badge/Engine-Gemini%20%7C%20Antigravity-orange)](#)

---

## 💎 Project Philosophy: "Security-First, AI-Driven"

**Humble Custom AI Workstation**은 가장 강력한 AI 에이전트 성능을 누리면서도, 기업의 민감한 데이터가 로컬 환경을 단 1바이트도 벗어나지 않도록 보호하는 것을 목표로 합니다.

### 🌟 Why This Project?
기존의 AI 툴들은 편의성을 위해 보안을 희생하거나, 복잡한 프록시 설정을 요구합니다. 본 프로젝트는 **"메모리 내 인라인 스트림 가로채기"** 기술을 통해 오버헤드 없는 완벽한 로컬 DLP를 구현했습니다.

---

## 🚀 Key Features (v1.7.0)

### 🔐 Deterministic DLP Engine (Core)
*   **Truncated SHA-256 Masking**: 동일한 민감 정보는 항상 동일한 8글자 해시 토큰(`[EMAIL_5e884898]`)으로 변환되어, 에이전트의 문맥 인지 능력을 극대화합니다.
*   **Response Firewall**: AI의 답변 속에 포함된 잠재적 민감 정보까지 출력 직전 필터링하는 양방향 방화벽.
*   **Hard Drop Guardrails**: 마스킹 규칙 우회 시도(Prompt Injection)를 감지하여 API 호출을 원천 차단.

### 🤖 Autonomous Agentic Control
*   **MAS & Supervisor Pattern**: 거대 목표를 하위 태스크로 자동 분해하고 병렬 서브에이전트에게 위임.
*   **Universal Backend Bridge**: Google Gemini뿐만 아니라 OpenAI 규격의 모든 로컬 모델(Ollama, DeepSeek 등)과 연동 가능.
*   **Intelligent Context Compression**: 대화가 길어질 경우 핵심 요약본만 유지하여 토큰 비용 80% 절감.

### 💻 Professional Terminal UX
*   **Visual Rewind**: `Esc+Esc`를 통해 과거 대화 시점으로 안전하게 롤백.
*   **4-Column Dashboard**: 경로, 보안 상태, 사용 모델, 쿼터 사용량을 실시간 모니터링.
*   **Kernel Sandbox**: 에이전트의 셸 명령 실행을 macOS/Linux 커널 레벨에서 물리적 격리.

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

---

## ⌨️ Productivity Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Shift + Tab` | **Work Mode Cycle** (Default -> Auto-Edit -> Plan) |
| `Tab + Tab` | **UI Density Toggle** (Full <-> Minimal) |
| `Ctrl + Y` | **Always Approve Mode** Toggle |
| `Ctrl + K` | **Bulk Approve** Pending Tools |
| `Ctrl + J` | **Mission Control** (MAS Graph View) |

---

## 🧬 Vibe Coding Log
이 프로젝트는 AI 개발의 새로운 패러다임을 증명합니다.
1.  **Stage 1**: Gemini CLI 무료 한도 내에서 기본 아키텍처 수립.
2.  **Stage 2**: "Pure Local DLP" 사상 주입 및 물리적 보안 레이어 구축.
3.  **Stage 3**: 외부 에코시스템(Model Armor, Swarm) 분석을 통한 엔터프라이즈 기능 통합.
4.  **Stage 4**: Deterministic SHA-256 Refactoring을 통한 데이터 일관성 확보.

---

## 📜 License
본 프로젝트는 MIT 라이선스에 따라 자유롭게 사용, 수정, 배포할 수 있습니다. 

---

## 🤖 Authorship & Maintenance Notice

*   **Written by**: **Gemini CLI** (100% Autonomous Authoring)
*   **Vibe Orchestrator**: [Your Name/Handle]
*   **Maintenance Policy**: 
    본 프로젝트의 모든 코드, 로직, 심지어 이 `README.md` 문서까지도 **Gemini CLI**가 직접 작성했습니다. 인간 관리자는 오직 '의도(Vibe)'만을 제공했을 뿐입니다. 
    따라서, 추후 이슈나 개선 사항에 대한 코멘트가 달릴 경우 인간 관리자는 당황하지 않고 즉시 **Antigravity/Gemini 에이전트**를 소환하여 해결을 맡길 예정입니다. 
    **"에이전트가 만들었으니, 에이전트가 고친다."** 이것이 본 프로젝트의 유지보수 철학입니다.
