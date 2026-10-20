# 첫 버전 검증 기록

검증일: 2026-10-20, 기준 시간대 Asia/Seoul. Codex Cloud에서 실행했다. 사용자 PC 설치·유료 API 호출·공개 배포·정기 자동화는 수행하지 않았다.

## 실제 실행 결과

| 검사 | 결과 | 근거와 범위 |
|---|---|---|
| Python 데이터·빌드 단위 테스트 | PASS · 17개 | `python3 -m unittest discover -s tests -v`, 실패·스킵 0개 |
| JSON 필수 항목·상태 검증 | PASS · 실제 실행 기록 1개 | `python3 scripts/validate.py`, BLOCKED/INSUFFICIENT_EVIDENCE 기록의 형식 검증 |
| JSON → Markdown 일치 | PASS | 실제 기록과 생성 Markdown이 일치해야 빌드 통과 |
| 정적 빌드 | PASS | `python3 scripts/build.py`, dist에 HTML/CSS/JS·목록·JSON·Markdown·.nojekyll 생성 |
| 브라우저 테스트 | PASS · 12개 | `python3 tests/browser_smoke.py`, 실제 Chromium, 실패·스킵 0개 |
| JavaScript 문법 | PASS | `node --check site/app.js` |
| 공백·패치 오류 | PASS | `git diff --check` |
| 시작·재시작 | PASS | 정적 서버 시작 후 HTML·목록·회사 JSON 요청. 본 작업에서 시작한 서버만 종료 후 재시작하고 같은 확인 통과 |
| 화면 육안 확인 | PASS · 데스크톱 홈 | Chromium 스크린샷을 열어 실제 차단 안내·레이아웃 확인 |
| 금융 원문 조사 | BLOCKED | Researcher 6개 도메인 모두 프록시 CONNECT 403 |
| 독립 금융 사실 검증 | 미완료 | Reviewer 공식 원문 2건도403. 검토 수행 결과 INSUFFICIENT_EVIDENCE |
| 실제 GitHub Pages 공개 사이트 | 미실행 | 사용자 별도 승인 전 활성화하지 않음 |
| 새 클라우드 작업에서 스냅샷 복원 | 미실행 | 현재 머신 검증·환경 초안 저장은 신규 작업 복원 검증과 다름 |

데이터 검증 성공은 금융 주장의 진실성이나 원문 검증 성공을 뜻하지 않는다. 이번 실행은 조사 차단 기록이며 실제 분석 완료 보고서가 아니다.

## 단위 테스트 17개가 확인한 사항

필수 필드·중첩 타입, 168시간 범위와 +09:00 실행시각, 회사 범위, 최대3개 사건, 출처 식별자·참조·URL·근거, 안전한 실행 ID, 중복 ID, 실제 기록된 Reviewer, 검토 미실행과 PASS 구분, 출처 없는 조사완료 금지, 충분한 원문 조사 후 사건0건 허용, BLOCKED/PASS 금지, Markdown 내용, 기존 보고서 덮어쓰기 차단, 목록 정렬·상대 경로·반복 빌드, 손상된 JSON·Markdown 불일치 시 기존 산출물 보존을 확인했다.

## 브라우저 테스트 12개가 확인한 사항

1. 실제 홈·기업·보고서의 상태, 실제 기록된 에이전트, 원문 미확보 상태 표시
2. 테스트 전용 자료의 사실·해석·출처 링크 및 과거 실행 이동
3. 메모 저장 후 새로고침 유지, 다른 브라우저 문맥과 분리
4. 보고서 실행별 메모 분리
5. 저장 공간 접근 실패 안내와 보고서 유지
6. HTML처럼 생긴 보고서 문자열을 문자로 표시하고 스크립트 미실행
7. 빈 이력 안내
8. 손상된 목록 JSON 오류 안내
9. 목록 파일404 오류 안내
10. 손상된 보고서 JSON·필수 항목 누락 오류 안내
11. 존재하지 않거나 경로처럼 생긴 실행 ID 오류 안내
12. 320·390px 모바일 폭에서 홈·기업·보고서 표시와 가로 넘침 없음

테스트 서버는 GitHub Pages처럼 `/financial-research-desk/` 하위 경로에서 동작했다. 테스트 문맥에서 예상치 못한 외부 요청과 GET 외 네트워크 쓰기가 없음을 확인했다. 테스트용 원문 링크는 `example.com` 가상 출처이며 실제 금융자료 검증을 의미하지 않는다. 이 가상 데이터는 테스트의 응답 가로채기에서만 존재하고 dist나 연구 기록에 배포하지 않는다.

최초 브라우저 실행은 테스트 도구의 Playwright 응답 처리 콜백 오류로 실패·중단했다. 두 번째 인자를 요청 객체로 받도록 수정한 뒤 전체12개를 재실행해 통과했다. 최신 실제 보고서 상태를 기준으로 검증하도록 테스트를 정리한 후에도 전체12개를 재실행해 통과했다. 최종 수치는 이 수정 후 실행에 해당한다.

## 원문·접근 기록

실제 연구 범위: 2026-10-13T16:16:03+09:00 ~ 2026-10-20T16:16:03+09:00.

- Researcher: SK하이닉스 홈페이지·뉴스룸, DART, KIND, 연합뉴스, Reuters. 6개 요청 모두 프록시403.
- Reviewer: SK하이닉스 홈페이지, DART를 독립 요청. 2개 모두 프록시403.
- 접근 시각과 실제 오류는 `research/runs/skhynix-20261020t161603-kst/`에 보존했다.
- 사건·원문 출처는 각각0개다. 이는 접근 실패를 뜻하며 사건 부재를 뜻하지 않는다.

## 도구와 환경 설정

Python 3.12.14, Node.js 24.19.0, Python Playwright 1.62.0, 시스템 Chromium 154.0.8037.57을 사용했다. Python Playwright의 기본 다운로드 브라우저 경로는 비어 있어 시스템 `/usr/bin/chromium`을 명시해 실제 실행했다. 추가 패키지 설치는 필요하지 않았다.

환경 초안에 제한 허용8개 도메인, `install_script`와 `start_skill`을 저장했다. 설치 스크립트는 기존 Python·Playwright·Chromium 확인과 데이터 테스트·검증·빌드를 수행하며, 실제로 `/tmp`에서 실행해 정상 동작을 확인했다. 시작 지침에는 작업 디렉터리·정적 서버 시작·실제 응답 준비 확인을 포함했다.

환경 도구가 반환한 저장 결과는 saved이며 requires_publish=true였다. 환경 설정 검토·저장과 환경 Publish는 사용자의 다음 동작이다. 아직 런타임 네트워크 적용·환경 발행·새 작업 복원을 검증한 것이 아니다. 이 절차는 GitHub Pages 공개 배포와 다르다.

## GitHub 전달 결과

작업 브랜치 `codex/financial-research-desk-v1`를 origin에 실제 전송하고 원격 SHA와 로컬 SHA가 일치함을 확인했다. 기본 브랜치 main은 변경하지 않았다.

[초안 PR #1](https://github.com/Ryu-Chaerin/financial-research-desk/pull/1)을 생성했다. `gh pr view`로 OPEN·isDraft=true·대상 main을 확인했다. PR 생성은 병합이나 사이트 배포가 아니다.

최초 GitHub REST 요청은 Forbidden이었지만 이후 기존 인증을 사용한 `gh pr create`·`gh pr view`·`gh repo view`가 성공했다. 따라서 GitHub API 전체를 사용할 수 없다고 단정하지 않는다. 저장소는 PUBLIC, 현재 권한은 ADMIN으로 확인됐다. 공개 저장소 GitHub Pages 무료 사용 조건에 맞지만, Pages 활성화·배포 성공은 검증하거나 실행하지 않았다. 토큰값은 출력하지 않았다. 금융 원문 도메인 차단이 해제됐다는 근거는 여전히 없다.
