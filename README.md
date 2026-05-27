# 🛡️ Humble Custom AI Workstation (v2.0.0)

> **Built 100% with Vibe Coding via Gemini CLI (Free Tier)**
> 
> 본 프로젝트는 어떠한 수동 코딩 없이, 오직 Gemini CLI의 무료 티어 한도 내에서 AI와의 대화(Vibe Coding)만으로 설계, 구현, 검증된 엔터프라이즈급 보안 AI 에이전트 워크스테이션입니다.

---

## 🚀 Key Features (v2.0.0)

### 🧠 Local RAG V3 (Intelligence) - **New**
*   **Privacy-First Search**: 임베딩 전 **선제적 마스킹(Pre-masking)**을 통해 민감 정보 유출 없이 클라우드 임베딩 활용.
*   **Lightweight Engine**: `NumPy` 기반의 벡터 연산으로 별도의 DB 서버 없이 수천 개의 문서를 실시간 검색.
*   **Incremental Indexing**: 파일 변경 사항만 감지하여 효율적으로 색인 업데이트.

### 🔐 Pattern-Driven Security (Architecture)
*   **Design Patterns**: Factory, Strategy, Adapter, CoR, Observer 패턴이 적용되어 모듈성과 확장성이 극대화되었습니다.
*   **Enriched Logging**: 비동기 큐 기반 로깅, `Trace ID` 전파, 계층적 레벨링 적용.
*   **Context Compression V2**: 자동 압축 트리거 및 유연한 요약 모델 선택 기능.
*   **Dynamic Reloading**: `masking_config.yaml` 변경 사항의 실시간 무중단 반영.

### 🤖 Intelligent Agentic Control
*   **Aligned Autocomplete**: 명령어와 설명을 시각적으로 깔끔하게 정렬한 자동완성 메뉴를 제공합니다.
*   **Robust @File Parsing**: 질문 시 `@path/to/file` 분석 지원.

---

## ⌨️ Consolidated Commands (Main)

| Command | Description | Sub-commands / Options |
| :--- | :--- | :--- |
| `/rag` | **로컬 RAG 관리** | `scan`, `status`, `clear` |
| `/compress`| **컨텍스트 압축** | 수동 압축 실행 (V2 자동화 포함) |
| `/session` | **세션 관리** | `save`, `load`, `list`, `resume`, `fork` |
| `/history` | **대화 기록 관리** | `show`, `undo`, `rewind`, `pin`, `unpin` |
| `/config` | **설정 및 환경 관리** | `show`, `model`, `agent`, `mode`, `autonomy`, `efficient`, `sandbox` |
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

# Docker Run (Workspace & Persistence mount recommended)
docker run -it --rm --env-file .env \
  -v $(pwd):/app/workspace \
  -v $(pwd)/.antigravity:/app/.antigravity \
  -v $(pwd)/logs:/app/logs \
  custom-cli
```

---

## 📉 Troubleshooting

### RAG 검색 결과가 나오지 않는 경우
*   `/rag scan` 명령어를 통해 워크스페이스를 먼저 색인했는지 확인하십시오.
*   `agent_config.yaml`에서 `rag.enabled`가 `true`인지 확인하십시오.
*   `numpy` 라이브러리가 정상 설치되었는지 확인하십시오.

---

## 🤖 Authorship & Maintenance Notice

*   **Written by**: **Gemini CLI** (100% Autonomous Authoring)
*   **Maintenance Policy**: "에이전트가 만들었으니, 에이전트가 고친다." 

---

## 📜 License
본 프로젝트는 MIT 라이선스에 따라 자유롭게 사용, 수정, 배포할 수 있습니다.
