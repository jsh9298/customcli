# 🛠️ Antigravity Maintenance Guide: Agent Edition (v2.0.0)

> **Handover Note**: 본 문서는 v2.0.0 작성자인 **Antigravity 에이전트**가 미래의 유지보수 담당자를 위해 작성한 기술 지침서입니다. v2.0.0의 테마는 **"디자인 패턴 기반의 보안 지능형 아키텍처"**입니다.

---

## 🏗️ 1. Technical Debt & Verified Tasks
v2.0.0 릴리즈에서 해결된 주요 기술 부채 및 구현 사항입니다.

- [x] **Enterprise Design Patterns**: Factory, Strategy, Adapter, CoR, Observer 패턴을 적용하여 핵심 모듈(Backend, Terminal, Logger, Protector)의 의존성 제거.
- [x] **Enriched Asynchronous Logging**: `QueueListener`를 통한 비동기 로깅 및 `Trace ID` 기반의 전 구간 추적성 확보.
- [x] **Context Compression V2**: 토큰 임계치 도달 시 자동 압축 트리거 및 유연한 모델 선택 로직 구축.
- [x] **Local RAG V3**: `NumPy` 기반의 경량 벡터 검색 엔진과 **Pre-masking Privacy** 레이어 통합.
- [x] **Dynamic Config Reload**: `masking_config.yaml` 변경 시 실시간 감지 및 캐시 무효화 로직 적용.

---

## 🧪 2. Strict Validation Protocols
모든 수정 후 반드시 수행해야 하는 검증 절차입니다.

1.  **Traceability Test**: 하나의 `chat_cycle`에 대해 모든 로그 파일(`unified_secure_cli.log`, `security_audit.log`)에 동일한 `Trace ID`가 기록되는지 확인할 것.
2.  **RAG Privacy Check**: `rag_index.json` 파일을 열어 임베딩된 텍스트 청크가 마스킹 처리된 상태인지(원본 노출 여부) 반드시 검사할 것.
3.  **Pattern Integrity**: `BackendFactory`를 통해 신규 백엔드 추가 시 기존 `core.py` 로직이 파손되지 않는지 확인할 것.

---

## 📉 3. Troubleshooting (Known Issues)
- **RAG Index Bloat**: 워크스페이스가 너무 클 경우 `rag_index.json` 파일이 비대해질 수 있습니다. 주기적으로 `/rag clear`를 권장하거나 `exclude_paths`를 정교하게 설정하십시오.
- **NumPy Dependency**: 로컬 환경에서 실행 시 `numpy` 라이브러리가 반드시 필요합니다.

---

## 📈 4. Upgrade Roadmap (Next Vibe)
1.  **Smart RAG Ranking**: BM25와 벡터 검색을 결합한 하이브리드 검색 도입.
2.  **Schema Validation**: 설정 파일들에 대한 JSON Schema 검증 레이어 추가.

---
**Message to Future Agent**: "패턴은 복잡성을 이기기 위한 도구다. 단순함을 위해 패턴을 파괴하지 마라. 아키텍처의 우아함이 곧 보안의 견고함이다."
