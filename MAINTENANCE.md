# 🛠️ Antigravity Maintenance Guide: Agent Edition (v1.8.6)

> **Handover Note**: 본 문서는 v1.8.6 작성자인 **Antigravity 에이전트**가 미래의 유지보수 담당자를 위해 작성한 기술 지침서입니다. v1.8.6의 테마는 **"보안 엔진의 완전한 선언적 구조화"**입니다.

---

## 🏗️ 1. Technical Debt & Verified Tasks
v1.8.6 릴리즈에서 해결된 주요 기술 부채입니다.

- [x] **SSN Masking Leak Fix**: 주민등록번호가 하이픈 없이 공백이나 숫자만으로 이루어진 경우에도 감지할 수 있도록 정규표현식 보강.
- [x] **Decoupling Masking Logic**: `protector.py` 소스 코드 내에 하드코딩되어 있던 모든 마스킹 패턴과 정규화 레이블 리스트를 완전히 제거.
- [x] **Token Consistency Implementation**: 동일한 민감 정보(예: 하이픈 유무가 다른 카드번호)가 항상 동일한 SHA-256 토큰으로 변환되도록 데이터 정규화(Normalization) 로직 통합.
- [x] **Declarative Security Config**: `masking_config.yaml`에 `normalization_rules` 및 `defaults` 섹션을 추가하여 보안 정책을 코드 수정 없이 관리 가능하도록 개선.

---

## 🧪 2. Strict Validation Protocols
모든 수정 후 반드시 수행해야 하는 검증 절차입니다.

1.  **Masking Consistency Test**: `1234-5678`과 `12345678`이 동일한 `[CREDIT_CARD_xxxx]` 토큰으로 변환되는지 확인할 것.
2.  **Zero-Hardcoding Check**: `protector.py` 파일 내에 정규표현식 문자열(r'...')이 남아있는지 `grep`으로 전수 조사할 것.
3.  **False Positive Audit**: `#20260524`와 같은 로그 ID가 `ACCOUNT` 패턴에 의해 오탐지되어 마스킹되지 않는지 확인할 것.

---

## 📉 3. Troubleshooting (Known Issues)
- **Missing Config Behavior**: `masking_config.yaml` 파일이 없을 경우, 시스템은 보안을 위해 마스킹을 수행하지 않으며 경고 로그를 남깁니다. 운영 환경에서는 반드시 설정 파일 존재 여부를 체크하십시오.
- **Docker Mounts**: 로그 파일 조회를 위해 Docker 실행 시 `logs` 디렉토리를 볼륨 마운트하는 것을 권장.

---

## 📈 4. Upgrade Roadmap (Next Vibe)
1.  **Dynamic Protector Reload**: 애플리케이션 재시작 없이 `masking_config.yaml` 변경 사항을 실시간 반영하는 Watcher 기능.
2.  **Advanced MAS**: Supervisor 패턴의 동적 위임 고도화.

---
**Message to Future Agent**: "코드는 로직만 담아야 한다. 데이터와 정책은 설정 파일의 영역이다. 이 무결성을 지켜라."
