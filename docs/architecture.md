# 전체 구조

Financial Research Desk는 Codex에서 만든 연구 결과를 GitHub Pages용 정적 파일로 보여준다. 웹사이트 안에서는 AI가 실행되지 않는다.

```text
사용자 → Codex Research Manager
          ├─ Researcher → 원문 확인·분석 초안
          ├─ Reviewer   → 독립 원문 검증·수정 요청
          └─ Designer & Developer → 고정된 사이트·검증 도구
                         ↓
research/reports/<run_id>/report.json + report.md
                         ↓ Python 검증·빌드
dist/ → 공개 배포 승인 후 GitHub Pages
```

## 구성 선택

순수 HTML/CSS/JavaScript는 이번에 필요한 보고서 조회·목록·메모에 충분하다. React/Vite보다 의존성과 빌드 관리가 적다. 화면의 상호작용이 크게 늘어나면 도입을 다시 검토한다. Python 실행 도구는 표준 라이브러리만 사용하고 브라우저 테스트에만 Playwright를 쓴다.

| 위치 | 역할 |
|---|---|
| `research/reports/<run_id>/` | 불변 연구 기록 JSON·Markdown |
| `research/runs/` | 실제 접근 시도·검토 원본 기록 |
| `site/` | 홈·기업·보고서 화면과 스타일·동작 |
| `scripts/` | 데이터 검증·Markdown 생성·정적 빌드 |
| `tests/` | 데이터·실제 브라우저 테스트, 가상 데이터는 테스트 안에만 존재 |
| `docs/` | 조사 기준·운영·테스트 결과·배포 템플릿 |
| `dist/` | 재생성 가능한 배포 산출물, Git 저장 제외 |

## 데이터 인터페이스

`scripts/reports.py`가 보고서 계약을 검증한다. 보고서에는 회사·실행시각·168시간 범위·연구상태·사건·검증 출처·검토·실제 역할 이력·실패가 있다. 사건에는 근거 출처를 참조하는 사실과 해석, 재무 영향 경로와 성립 조건, 반대 근거, 후속 지표를 둔다. 조회 실패한 URL은 확인된 출처로 쓰지 않고 실패와 접근 시도 기록에 둔다.

빌드는 검증한 JSON을 `dist/data/reports/<run_id>.json`에 복사하고, `dist/data/reports.json`에 최신순 목록을 만든다. 목록 항목은 `run_id`, `company_name`, `executed_at`, `summary`, `research_status`, `review_status`, `path`다. 브라우저는 목록에 등록된 실행만 조회한다. 모든 자산 경로는 GitHub Pages 프로젝트 하위 경로를 지원한다.

연구 상태는 `COMPLETED`, `PARTIAL`, `BLOCKED`다. Reviewer 결과는 `PASS`, `REVISE`, `INSUFFICIENT_EVIDENCE`이며 미실행은 결과 `null`과 `NOT_RUN`으로 구분한다. 실제 검토는 했지만 원문을 읽지 못하면 검토 실행은 완료, 결과는 `INSUFFICIENT_EVIDENCE`다. 이는 사실 확인 완료를 뜻하지 않는다.

## 확정 보고서와 조사 기록

기존 JSON 계약을 유지하며 `research_status=COMPLETED`와 `review.status=PASS`를 모두 만족할 때만 확정 보고서다. 홈·기업 화면은 최신 확정 보고서를 별도로 선택한다. 더 최근의 PARTIAL·BLOCKED·REVISE·검토 미실행 기록이 이를 대체하지 않는다. 확정본이 없으면 없다고 표시한다. 모든 실행은 이력에서 계속 열 수 있고 상세 화면도 초안·차단 여부를 표시한다.

PARTIAL은 실제 자료를 일부 확인한 조사 초안이며 최종 확정을 보류한다. 공식 자료와 기간 내 DART 공시 확인이 빠지면 Reviewer는 INSUFFICIENT_EVIDENCE를 기록한다. 기존 차단 이력과 데이터 계약은 변경하지 않는다.

## 개인 메모와 공개 경계

메모는 보고서 실행별 localStorage에만 저장한다. 네트워크·Git에 메모를 보내는 코드가 없다. 같은 브라우저의 같은 사이트에서만 보이며, 기기 동기화가 없고 브라우저 데이터 삭제 시 사라질 수 있다. 해당 브라우저 프로필을 공유하는 사람도 볼 수 있으므로 민감정보 저장소로 쓰지 않는다. 보고서 JSON·실행 이력은 배포 시 공개될 자료다.

## 배포와 비용

서버·DB·LLM API가 필요하지 않다. 배포는 별도 승인 이후 공개 저장소의 GitHub Pages 무료 기능으로 진행한다. 현재는 활성 워크플로 없이 수동 배포 템플릿만 제공한다. 설치 상태 스냅샷과 환경 설정 저장은 웹사이트 공개 배포와 다른 절차다.
