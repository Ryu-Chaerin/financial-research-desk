# 비개발자를 위한 운영 절차

## 평소에는 Codex에 요청하기

사용자 PC에 설치하거나 명령을 입력할 필요가 없다. Codex에서 이 저장소를 선택하고 아래처럼 요청한다.

> SK하이닉스 최근 7일 리서치를 실행해 주세요. AGENTS.md를 따르고 실제 Researcher와 Reviewer를 분리하세요. 이전 기록은 보존하고 새 JSON·Markdown을 추가한 뒤 사이트와 테스트를 검증하고 PR을 준비하세요. 공개 배포는 하지 마세요.

그다음 Codex가 제공하는 GitHub PR 링크를 클릭해 **Files changed**에서 보고서·사이트·테스트 기록을 확인한다. PR이 없으면 Codex가 보고한 차단 이유를 먼저 해결한다. 웹사이트를 매 조사마다 다시 개발할 필요는 없다.

## 자료 접근이 차단된 경우

현재 차단은 웹사이트가 반환한 기사 오류가 아니라 네트워크 프록시의 403이다. Codex 환경 설정에서 저장된 제한 허용 도메인 초안을 검토하고 저장한다. `www.skhynix.com`, `news.skhynix.com`, `dart.fss.or.kr`, `kind.krx.co.kr`, `www.yna.co.kr`, `www.reuters.com`, `api.github.com`, `docs.github.com`이 대상이다. 기존 패키지 설치용 허용 목록은 유지한다.

설정 적용 후 Codex에 “자료 접근을 다시 확인하고 중단된 조사를 재개해 주세요”라고 요청한다. 추가 호스트가 필요하면 Codex가 이유를 설명해야 한다. 비밀값을 채팅에 입력하지 않는다. 무제한 인터넷 허용이나 별도 유료 키는 필요하지 않다.

환경 초안 저장은 현재 머신의 네트워크를 바로 바꾸거나 웹사이트를 공개하지 않는다. 환경 도구가 요구하는 환경 Publish는 개발환경 스냅샷 저장이며, 아래 GitHub Pages 공개 배포와 별개다.

## 브라우저에서 결과 보기

공개 배포 전에는 GitHub의 보고서 `report.md` 파일을 클릭하면 읽기 쉬운 연구 기록을 볼 수 있다. 차단 실행이면 분석 결론 대신 접근 실패·Reviewer 결과가 보인다. 이 단계에서는 공개 웹사이트 주소가 없다.

공개 사이트가 필요해지면 먼저 “GitHub Pages 공개 배포를 승인합니다”라고 별도로 요청한다. Codex가 저장소 공개 여부와 무료 이용 가능 여부를 확인한 후 진행해야 한다. 비공개 저장소를 자동으로 공개 전환하지 않는다.

승인 이후의 절차:

1. 검토한 PR을 GitHub에서 병합한다.
2. Codex가 `docs/pages-workflow.yml.example`을 활성 워크플로로 추가한 PR을 준비한다. 검토 후 병합한다.
3. 저장소 **Settings → Pages → Build and deployment → Source → GitHub Actions**를 선택한다.
4. **Actions → Deploy research desk manually → Run workflow**에서 기본 브랜치를 선택해 실행한다.
5. 성공한 실행의 배포 결과 또는 **Settings → Pages**가 제공하는 실제 사이트 링크를 클릭한다.

이 템플릿에는 예약·push 자동 실행이 없다. 보고서 업데이트를 공개하려면 매번 검토 후 수동 배포한다. Actions가 실패하면 Pages가 성공했다고 간주하지 말고 Codex에 해당 실행 링크를 전달한다.

## 공부 메모

보고서 화면에서 메모를 입력하고 저장 버튼을 누른다. 메모는 현재 브라우저에만 저장되고 GitHub나 서버로 전송되지 않는다. 다른 기기나 브라우저와 동기화되지 않으며 브라우저 데이터 삭제 시 사라질 수 있다. 중요한 공부 기록은 본인이 사용하는 별도 비공개 노트에 보관한다.

## Codex가 클라우드에서 실행할 명령

아래는 사용자가 PC에서 실행할 명령이 아니다. Codex가 `/workspace/financial-research-desk` 저장소에서 재현·검증할 때 사용한다.

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate.py
python3 scripts/build.py
python3 tests/browser_smoke.py
```

빌드는 검증한 보고서를 포함한 `dist/` 폴더를 만든다. 로컬 확인이 필요하면 Codex가 이 폴더를 정적 서버로 제공하고 자동 브라우저 요청으로 검증한다. 온보딩 화면에는 localhost 미리보기 링크를 제공하지 않는다.
