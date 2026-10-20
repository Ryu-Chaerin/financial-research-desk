# Financial Research Desk

SK하이닉스를 시작으로 공개 자료를 조사하고, 독립 검토와 근거를 함께 보여주는 **금융 리서치 학습·취업 포트폴리오**입니다. 실제 투자 권유 서비스가 아닙니다.

## 첫 버전

- 최근 7일·주요 사건 최대 3개, 사실과 해석·영향 경로·반대 근거를 분리합니다.
- 실제 Codex Researcher와 Reviewer의 수행 이력·검토 상태를 기록합니다.
- JSON과 Markdown 보고서를 실행별로 보존합니다.
- 정적 사이트에서 최신·과거 보고서, 출처, 검토 지적과 실행 실패를 확인합니다.
- 공부 메모는 브라우저에만 저장하며 서버에 올리지 않습니다. 기기 동기화·영구 보존은 지원하지 않습니다.

**현재 연구 상태:** 공식 자료 및 선정 언론의 공개 원문 접근이 프록시 403으로 차단되어 첫 실행은 `BLOCKED`입니다. “최근 사건 없음”이라는 결론이 아닙니다. 원문 조사와 금융 사실 검증은 미완료이며, 사건·수치·출처를 가상으로 채우지 않았습니다.

## 사용 방법

사용자 PC에 Python·Git·에디터를 설치할 필요가 없습니다. Codex Cloud에서 이 저장소를 선택하고 “SK하이닉스 최근 7일 리서치를 업데이트하고 테스트한 뒤 PR을 준비해 주세요”라고 요청하세요. GitHub에서 `research/reports/`의 `report.md`를 클릭하면 연구 기록을 읽을 수 있습니다.

사이트는 순수 HTML/CSS/JavaScript이고 LLM API를 호출하지 않습니다. 공개 GitHub Pages 무료 배포를 위한 템플릿은 있지만, **공개 배포·정기 실행은 활성화하지 않았습니다.** 배포는 별도 승인 후 진행합니다.

## 구조와 문서

- [운영 절차](docs/runbook.md): 클릭·요청 중심 안내, 네트워크 복구와 배포 절차
- [전체 구조](docs/architecture.md): 사이트·데이터·역할 구성
- [조사 기준](docs/research-methodology.md): 원문·사실·해석·검토 기준
- [Codex 규칙](AGENTS.md): 비용·안전·작업·검증 기준
- [검증 기록](docs/validation.md): 실제 실행한 검사와 미완료 항목

개발·검증 명령은 Codex가 저장소 루트에서 실행합니다.

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate.py
python3 scripts/build.py
python3 tests/browser_smoke.py
```

빌드와 데이터 도구는 Python 3.12 표준 라이브러리만 사용합니다. 브라우저 테스트는 Python Playwright와 시스템 Chromium을 사용합니다. 의존성 설치, 실행, 검증은 클라우드에서 처리하며 유료 데이터·LLM API·호스팅은 사용하지 않습니다. Codex 작업은 계정의 사용량을 소비하며 사용량 한도나 잔액을 이 저장소에서 조회하지 않습니다.
