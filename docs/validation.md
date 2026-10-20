# 기업 기본 분석 추가 — 2026-10-20 Asia/Seoul

## 실제 결과

- 기본 분석 실행 `skhynix-baseline-20261020t170559-kst`, report_kind BASELINE. 최근7일 주간 분석과 다른 보고기간을 가진 별도 JSON·Markdown을 저장했다. 기존 주간 보고서2개는 바이트 비교로 변경 없음을 확인했다.
- 실제 Researcher `/root/baseline_researcher` 웹 도구6회, 별도 Reviewer `/root/baseline_reviewer` 웹 도구3회, Manager 수정1회. 재게시본 일부 사업 설명과 공식 OPENDART 연간/반기/1분기 목차 및 SEC 색인을 확인했다.
- DART 개별 보고서 원문은502/Internal Error. OPENDART는 접수정보·목차만 확인했고 수치표·주석 본문은 미확인이다. SEC색인은 열리지만 실제 첨부는 웹 도구의400 Content length is too large:4194305+ 오류로 미확인이다. 도구가 반환한 오류이며 금융감독원 전체 차단이나 실제 문서 크기를 확정하는 진단이 아니다.
- 공식 접수번호를 찾아도 원본 본문 검증 성공은 아니다. 최종 기본 분석의 모든 original_verified는 false다. Researcher raw기록의 true는 공식 목차 페이지 확인 의미였으나 Reviewer 요청에 따라 최종 데이터는 ‘보고서 원본 본문 확인’ 의미로 통일해 false로 보정했다. raw기록은 그대로 보존하고 manager.json에 수정 기록을 남겼다.
- Reviewer 요청에 따라 미확인 구체 설비 항목을 제외했다. 실제 재무 수치·증감률·시장 전망을 채택하지 않았다. 원본 대조·정정·최신성 검증은 미완료로 PARTIAL/INSUFFICIENT_EVIDENCE, 최종 확정 보류다.

## 이번 검증

| 검사 | 결과 | 범위 |
|---|---|---|
| Python 단위 테스트 | PASS ·22개 | 주간168시간 유지, 기본 보고기간 분리, 재게시/목차만으로 완료 금지, 출처 참조, 분리 빌드·보존 |
| 실제 JSON 검증 | PASS ·3개 | 주간2개+기본1개, 형식 검증과 금융 원본 검증은 별개 |
| Markdown 일치·정적 빌드 | PASS | 주간2개와 기본1개 목록 분리, 배포 없음 |
| Chromium 브라우저 | PASS ·17개 | 실제 기본 화면·출처·목차/재게시 안내,320/390px, 기본 목록404에도 주간 유지, 손상 기본자료 안내, 기존 메모·오류·주간 회귀 |
| JavaScript 문법·git diff --check | PASS | 최신 코드 |
| 기존 주간 기록·가상자료 제외 | PASS | 이전 JSON·Markdown 바이트 보존, dist/data에 가상자료/테스트메모 미포함 |
| 금융 원본 본문 대조·정정·최신성 | 미완료 | 실패/미확인 기록을 기본 분석에 보존 |
| 공개 배포·정기 실행 | 미실행 | 별도 승인 전 활성화하지 않음 |

초기 기본 분석 조립에서 access_status 누락을 검증기가 거부했고 저장 전에 중단했다. 기본 자료에는 ACCESSED(접근 성공) 상태를 사용하도록 명확히 한 후 새 기록 저장·전체검증에 통과했다. 기존 보고서와 주간 원문 검증 기준은 바꾸지 않았다.

별도 유료 API·가입·LLM 호출·권한 확장은 하지 않았다. 웹 자료 조회는 제공된 공개 웹 도구, 개발·브라우저 검증은 클라우드에서 수행했다. 기존 초안 PR #1을 갱신하며 main 병합·공개 배포는 하지 않는다.

---

# 검증 기록

## 조사 재개 및 기존 버전 보완 — 2026-10-20 Asia/Seoul

새 실행: `skhynix-20261020t165559-kst`. 범위: 2026-10-13T16:55:59+09:00 ~ 2026-10-20T16:55:59+09:00. 기존 차단 실행의 JSON·Markdown을 Git HEAD와 바이트 비교해 변경 없음을 확인했다.

### 실제 조사·검토

- 실제 Researcher `/root/researcher_resume`: 공개 웹 도구3회. 공식 OCP 글·Reuters 원문·과거 연구 재소개 글을 확인했다. 사건2개 초안을 작성하고 과거 연구 재소개는 새 사건에서 제외했다.
- 별도 Reviewer `/root/reviewer_resume`: 공개 웹 도구3회. 같은 원문3개를 직접 다시 확인했고 DART 기간검색을 독립 시도했다. 최종 제목·요약에 보도와 회사 반론을 명시하도록 요청했다.
- Manager가 요청을 한 차례 반영했다. 추가 재검토는 하지 않았다. DART 기간 공시·핵심 IR 미확인 문제는 미해결로 남겼다.
- 결과는 `PARTIAL / INSUFFICIENT_EVIDENCE`, 조사 초안이며 최종 확정 보류다. 금융 원문 일부 확보와 사이트 구현은 완료했지만 전체 조사 완료 조건은 충족하지 않았다.
- 공개 웹 조회 경로는 공식 뉴스룸·Reuters 원문에 성공했다. DART 홈502·기간검색 Internal Error, 공식 공시/실적 목록 내용 미추출, KIND0줄을 기록했다. Reviewer의 Reuters 최초 URL 열기는 실패했으나 같은 공식 도메인의 검색 결과를 열어 원문 확인에 성공했다.
- 클라우드 관리 도구는 cloud/running/connected 및 제한 네트워크 enforced를 반환했다. 터미널 기본 실행은 소켓 권한 제한으로 GitHub 요청에 실패했고 허용된 실행에서는 기존 PR 읽기가 성공했다. 웹 도구 접근과 터미널 소켓 권한은 구분한다.

### 이번 실제 검증 결과

| 검사 | 결과 | 범위 |
|---|---|---|
| Python 단위 테스트 | PASS ·17개 | 기존 데이터 계약·보존·빌드 테스트 |
| 실제 JSON 형식 검증 | PASS ·2개 실행 | 기존 BLOCKED·새 PARTIAL, 금융 사실의 진실성 검증과 별개 |
| Markdown 일치·정적 빌드 | PASS | 실제 보고서2개 포함 dist 생성, 배포 없음 |
| JavaScript 문법·git diff --check | PASS | 최종 사이트 코드와 패치 |
| Chromium 브라우저 | PASS ·14개 | 새 실제 보고서·이전 이력 이동·원문 링크·모바일320/390px·오류·메모 |
| 확정/초안 구분 | PASS | 새 초안이 이전 확정본을 대체하지 않음, 확정본 부재, REVISE·미검토·차단 제외 |
| 기존 보고서 보존 | PASS | 이전 JSON·Markdown 바이트 일치 |
| 산출물 가상자료·테스트메모 제외 | PASS | dist/data 전체 검사, 실제 실행2개 |
| 알려진 비밀키 패턴 검사 | PASS | 알려진 토큰·개인키 서명, 모든 비밀정보 탐지를 보장하는 검사는 아님 |
| 공개 Pages 배포·정기 실행 | 미실행 | 별도 승인 전 활성화하지 않음 |

브라우저 첫 시도는 기본 실행의 소켓 생성 권한 제한으로0개 실행·실패했다. 허용된 클라우드 내부 서버/Chromium 실행으로14개를 통과했고, 새 보고서 추가 후 실제 데이터·모바일·이전 이력 이동을 포함한 최종14개도 통과했다. 테스트 전용 가상 자료는 응답 가로채기에만 존재하며 공개 보고서나 배포 데이터에 포함되지 않는다. 메모 전송과 예상치 못한 외부 요청이 없음을 확인했다.

개발은 Manager와 동일한 `/root`가 수행했다. 별도 개발 AI를 실행했다고 표시하지 않았다. 추가 유료 서비스·LLM API·사용자 PC 설치·공개 배포·정기 자동화는 사용하지 않았다. Researcher1회·Reviewer1회·Manager 수정1회다. Codex 계정의 남은 사용량/Plus 한도는 조회할 수 없다.

### GitHub 전달

기존 작업 브랜치 `codex/financial-research-desk-v1`에 구현 커밋 `2b3b0137f3f8396bd608346c47387347d09e7b6f`를 만들고 origin으로 전송했다. `gh pr view`의 headRefOid와 로컬 HEAD 일치를 확인했다. [초안 PR #1](https://github.com/Ryu-Chaerin/financial-research-desk/pull/1)의 제목·설명을 최신 구현과 조사 한계로 갱신했으며 상태는 OPEN / isDraft=true다. main 병합·공개 배포는 수행하지 않았다. 이 전달 증거 문서는 후속 문서 커밋으로 보존한다.

브라우저에서는 PR의 Files changed를 클릭하거나, [새 조사 초안 Markdown](https://github.com/Ryu-Chaerin/financial-research-desk/blob/codex/financial-research-desk-v1/research/reports/skhynix-20261020t165559-kst/report.md)을 열면 된다. 공개 웹사이트는 활성화하지 않았으며 배포 성공을 주장하지 않는다.

---

# 과거 첫 버전 검증 기록 — 이전 실행

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
