# 🛠️ Antigravity Maintenance Guide: v2.1.0

> **Release Note**: v2.1.0은 **"계층형 아키텍처 완성 및 UX 표준화"**를 테마로 합니다. 모든 핵심 로직이 도메인별 모듈로 분리되었습니다.

---

## 🏗️ 1. System Architecture (Layered)

프로젝트 구조는 다음과 같은 엄격한 계층을 따릅니다. 의존성은 위에서 아래로만 흘러야 합니다.

### **A. Presentation Layer (`ui/`, `commands/`)**
*   **`ui/controller.py`**: TUI 렌더링 및 테마 관리 (Facade).
*   **`ui/keybindings.py`**: 단축키 로직 캡슐화 (Observer).
*   **`ui/completer.py`**: 지능형 자동완성 엔진 (Strategy).
*   **`commands/handlers/`**: 도메인별 명령어 실행 로직 (Command).

### **B. Application Layer (`core.py`)**
*   **`UnifiedSecureCLI`**: 각 모듈을 인스턴스화하고 전체 흐름(Chat Pipeline)을 조율 (Facade & Orchestrator).

### **C. Domain/Service Layer (`security/`, `agent/`)**
*   **`security/protector.py`**: 마스킹 전략 실행 (Strategy & CoR).
*   **`agent/backends/`**: 모델 통신 추상화 (Factory).

### **D. Infrastructure Layer (`utils/`, `state/`)**
*   **`utils/rag.py`**: 로컬 벡터 검색 엔진.
*   **`state/session.py`**: 세션 영속화 관리.

---

## 🔐 2. Coding Standards & Patterns

1.  **Hybrid Command Pattern**: 신규 명령어 추가 시 `handlers/*.py`에 구현하며, 인자가 없을 경우 인터랙티브 메뉴(`ask_selection`)를 띄우는 로직을 반드시 포함하십시오.
2.  **Strict Masking**: 모든 입출력은 `Protector`를 거쳐야 하며, 응답 스트리밍 시에도 `Live.update` 전 마스킹을 수행해야 합니다.
3.  **Persistence**: 설정 변경 시 `SystemHandlers.save_config_to_file()`을 호출하여 `agent_config.yaml`에 즉시 반영되도록 하십시오.

---

## 🧪 3. Validation Protocols

1.  **Modular Check**: `core.py`를 수정하지 않고 신규 명령어를 `handlers/`에 추가하여 자동완성 및 실행이 되는지 확인.
2.  **UI Consistency**: 메뉴 호출 시 화살표 키 내비게이션과 `Esc` 취소가 전역적으로 작동하는지 확인.
3.  **Hot-swap Test**: `agent_config.yaml` 수동 수정 또는 명령어를 통한 수정 시 시스템이 중단 없이 리로드되는지 확인.

---

## 📈 4. Next Roadmap
1.  **Subagent Delegation**: `@specialist` 라우팅 로직의 실질적 구현.
2.  **Enhanced Telemetry**: 실시간 토큰 사용량에 따른 과금(추정) 알림 기능.

---
**Message to Maintainer**: "파일이 많아졌다고 복잡해진 것이 아니다. 각자의 자리를 찾은 것이다. 질서가 곧 성능이다."
