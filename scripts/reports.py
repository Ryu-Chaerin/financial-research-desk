"""Report contract, immutable storage, and Markdown presentation.

Validation establishes structural consistency, not financial truth. A human or
an independently executed Reviewer must still inspect the cited originals.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

SLUG = re.compile(r"[a-z0-9][a-z0-9_-]{0,99}\Z")


def validate_report(report: object) -> list[str]:
    errors: list[str] = []

    def err(path: str, message: str) -> None:
        errors.append(f"{path}: {message}")

    def obj(value: object, path: str, keys: list[str]) -> dict:
        if not isinstance(value, dict):
            err(path, "must be an object")
            return {}
        for key in keys:
            if key not in value:
                err(f"{path}.{key}", "required field missing")
        return value

    def text(value: object, path: str) -> None:
        if not isinstance(value, str) or not value.strip():
            err(path, "must be a nonempty string")

    def seq(value: object, path: str) -> list:
        if not isinstance(value, list):
            err(path, "must be an array")
            return []
        return value

    def strings(value: object, path: str) -> list:
        result = seq(value, path)
        for i, item in enumerate(result):
            text(item, f"{path}[{i}]")
        return result

    def timestamp(value: object, path: str) -> datetime | None:
        try:
            if not isinstance(value, str) or "T" not in value:
                raise ValueError
            parsed = datetime.fromisoformat(value)
            if parsed.utcoffset() != timedelta(hours=9):
                raise ValueError
            return parsed
        except (ValueError, TypeError):
            err(path, "must be an ISO datetime with +09:00 offset")
            return None

    def day(value: object, path: str, nullable: bool = True) -> None:
        if nullable and value is None:
            return
        try:
            if not isinstance(value, str):
                raise ValueError
            if "T" in value:
                timestamp(value, path)
            elif date.fromisoformat(value).isoformat() != value:
                raise ValueError
        except (ValueError, TypeError):
            err(path, "must be an ISO date or datetime, or null")

    def choice(value: object, path: str, allowed: set) -> None:
        if not isinstance(value, (str, type(None))) or value not in allowed:
            err(path, f"invalid value; expected one of {sorted(str(v) for v in allowed)}")

    def url(value: object, path: str) -> None:
        try:
            if not isinstance(value, str):
                raise ValueError
            parsed = urlsplit(value)
            if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                    or parsed.password or any(c.isspace() or c in '<>"\\' for c in value)):
                raise ValueError
            _ = parsed.port
        except ValueError:
            err(path, "must be an HTTPS URL without credentials or whitespace")

    top_keys = ["schema_version", "run_id", "company", "executed_at", "timezone",
                "period", "topic", "summary", "research_status", "events", "sources",
                "limitations", "follow_up", "review", "agents", "failures"]
    r = obj(report, "report", top_keys)
    if not r:
        return errors
    if type(r.get("schema_version")) is not int or r.get("schema_version") != 1:
        err("schema_version", "must be integer 1")
    if not isinstance(r.get("run_id"), str) or not SLUG.fullmatch(r.get("run_id", "")):
        err("run_id", "must be a safe lowercase slug of at most 100 characters")
    company = obj(r.get("company"), "company", ["name", "ticker"])
    if company.get("name") != "SK하이닉스" or company.get("ticker") != "000660":
        err("company", "v1 supports only SK하이닉스 (000660)")
    kind = r.get("report_kind", "WEEKLY")
    choice(kind, "report_kind", {"WEEKLY", "BASELINE"})
    baseline = kind == "BASELINE"
    executed = timestamp(r.get("executed_at"), "executed_at")
    if r.get("timezone") != "Asia/Seoul":
        err("timezone", "must be Asia/Seoul")
    period = obj(r.get("period"), "period", ["start", "end"])
    start = timestamp(period.get("start"), "period.start")
    end = timestamp(period.get("end"), "period.end")
    if not baseline and start and end and end - start != timedelta(hours=168):
        err("period", "must cover exactly 168 hours")
    if not baseline and executed and end and executed != end:
        err("period.end", "must equal executed_at")
    if baseline and start and end and executed and not start <= end <= executed:
        err("period", "baseline reporting period must end no later than execution")
    for key in ["topic", "summary"]:
        text(r.get(key), key)
    choice(r.get("research_status"), "research_status", {"COMPLETED", "PARTIAL", "BLOCKED"})
    strings(r.get("limitations"), "limitations")
    strings(r.get("follow_up"), "follow_up")

    sources = seq(r.get("sources"), "sources")
    source_ids: set[str] = set()
    for i, raw in enumerate(sources):
        p = f"sources[{i}]"
        s = obj(raw, p, ["id", "title", "published_at", "url", "accessed_at", "evidence", "access_status"])
        for k in ["id", "title", "evidence"]:
            text(s.get(k), f"{p}.{k}")
        sid = s.get("id")
        if isinstance(sid, str):
            if sid in source_ids:
                err(f"{p}.id", "duplicate source id")
            source_ids.add(sid)
        if baseline:
            choice(s.get("source_type"), f"{p}.source_type", {"ORIGINAL", "REPOST"})
            if type(s.get("original_verified")) is not bool:
                err(f"{p}.original_verified", "must be a boolean")
            if s.get("original_verified") is True and (s.get("source_type") != "ORIGINAL" or s.get("access_scope") != "FULL_TEXT"):
                err(p, "original_verified requires official full body verification")
            if s.get("source_type") == "REPOST" and s.get("original_verified") is not False:
                err(p, "REPOST remains unverified against original in v1")
            choice(s.get("access_scope"), f"{p}.access_scope", {"FULL_TEXT", "EXCERPTS_READ", "METADATA_ONLY"})
            text(s.get("reporting_period"), f"{p}.reporting_period")
        day(s.get("published_at"), f"{p}.published_at")
        timestamp(s.get("accessed_at"), f"{p}.accessed_at")
        url(s.get("url"), f"{p}.url")
        choice(s.get("access_status"), f"{p}.access_status", {"ACCESSED"} if baseline else {"VERIFIED"})
    if baseline:
        coverage = obj(r.get("baseline_coverage"), "baseline_coverage", ["annual_source_id", "interim_source_id", "freshness_verified"])
        for field in ["annual_source_id", "interim_source_id"]:
            value = coverage.get(field)
            if value is not None and (not isinstance(value, str) or value not in source_ids):
                err(f"baseline_coverage.{field}", "must reference an accessed source or be null")
        if type(coverage.get("freshness_verified")) is not bool:
            err("baseline_coverage.freshness_verified", "must be a boolean")
        if r.get("research_status") == "COMPLETED":
            if not coverage.get("annual_source_id") or not coverage.get("interim_source_id") or coverage.get("freshness_verified") is not True:
                err("baseline_coverage", "completed baseline requires annual, interim and verified freshness")
            if any(not isinstance(s, dict) or s.get("original_verified") is not True or s.get("access_scope") != "FULL_TEXT" for s in sources):
                err("sources", "completed baseline requires verified originals")
    if r.get("research_status") == "COMPLETED" and not sources:
        err("sources", "COMPLETED research requires directly accessed source evidence")

    def references(value: object, path: str, required: bool = False) -> list:
        result = strings(value, path)
        if required and not result:
            err(path, "at least one verified source is required")
        for ref in result:
            if isinstance(ref, str) and ref not in source_ids:
                err(path, f"unknown source id {ref!r}")
        return result

    events = seq(r.get("events"), "events")
    if len(events) > 3:
        err("events", "at most 3 events are supported")
    event_ids: set[str] = set()
    event_source_ids: set[str] = set()
    for i, raw in enumerate(events):
        p = f"events[{i}]"
        e = obj(raw, p, ["id", "title", "event_date", "scope", "facts", "interpretations",
                         "impact_channels", "counter_evidence", "watch_items"])
        for k in ["id", "title"]:
            text(e.get(k), f"{p}.{k}")
        eid = e.get("id")
        if isinstance(eid, str):
            if eid in event_ids:
                err(f"{p}.id", "duplicate event id")
            event_ids.add(eid)
        day(e.get("event_date"), f"{p}.event_date")
        choice(e.get("scope"), f"{p}.scope", {"DIRECT", "INDUSTRY"})
        for k in ["facts", "interpretations"]:
            items = seq(e.get(k), f"{p}.{k}")
            if k == "facts" and not items:
                err(f"{p}.{k}", "an event requires at least one sourced fact")
            for j, raw_item in enumerate(items):
                q = f"{p}.{k}[{j}]"
                item = obj(raw_item, q, ["text", "source_ids"])
                text(item.get("text"), f"{q}.text")
                refs = references(item.get("source_ids"), f"{q}.source_ids", required=True)
                event_source_ids.update(ref for ref in refs if isinstance(ref, str))
        for j, raw_channel in enumerate(seq(e.get("impact_channels"), f"{p}.impact_channels")):
            q = f"{p}.impact_channels[{j}]"
            c = obj(raw_channel, q, ["area", "mechanism", "conditions"])
            choice(c.get("area"), f"{q}.area", {"매출", "수익성", "현금흐름", "설비투자", "위험요인"})
            text(c.get("mechanism"), f"{q}.mechanism")
            strings(c.get("conditions"), f"{q}.conditions")
        strings(e.get("counter_evidence"), f"{p}.counter_evidence")
        strings(e.get("watch_items"), f"{p}.watch_items")
    if r.get("research_status") == "BLOCKED" and events:
        err("events", "BLOCKED research cannot publish events")

    review = obj(r.get("review"), "review", ["execution_status", "status", "reviewer_agent",
                 "findings", "checked_source_ids", "limitations"])
    choice(review.get("execution_status"), "review.execution_status", {"COMPLETED", "NOT_RUN"})
    choice(review.get("status"), "review.status", {"PASS", "REVISE", "INSUFFICIENT_EVIDENCE", None})
    checked = references(review.get("checked_source_ids"), "review.checked_source_ids")
    strings(review.get("limitations"), "review.limitations")
    if review.get("execution_status") == "COMPLETED":
        text(review.get("reviewer_agent"), "review.reviewer_agent")
        if review.get("status") is None:
            err("review.status", "completed review requires an outcome")
    if review.get("execution_status") == "NOT_RUN":
        if review.get("status") is not None or review.get("reviewer_agent") is not None or checked:
            err("review", "NOT_RUN cannot claim a reviewer, checked sources, or outcome")
    if review.get("status") == "PASS":
        if r.get("research_status") != "COMPLETED" or not sources or not checked:
            err("review.status", "PASS requires completed research, sources, and checked sources")
        if not event_source_ids.issubset(set(ref for ref in checked if isinstance(ref, str))):
            err("review.checked_source_ids", "PASS requires checking every cited event source")
    for i, raw in enumerate(seq(review.get("findings"), "review.findings")):
        p = f"review.findings[{i}]"
        finding = obj(raw, p, ["severity", "message", "event_id", "source_ids"])
        choice(finding.get("severity"), f"{p}.severity", {"INFO", "WARNING", "ERROR"})
        text(finding.get("message"), f"{p}.message")
        if finding.get("event_id") is not None and (not isinstance(finding.get("event_id"), str)
                                                   or finding.get("event_id") not in event_ids):
            err(f"{p}.event_id", "must refer to an event id, or be null")
        references(finding.get("source_ids"), f"{p}.source_ids")
        if review.get("status") == "PASS" and finding.get("severity") == "ERROR":
            err("review.status", "PASS cannot contain unresolved ERROR findings")

    agent_ids: set[str] = set()
    for i, raw in enumerate(seq(r.get("agents"), "agents")):
        p = f"agents[{i}]"
        agent = obj(raw, p, ["role", "agent_id", "task", "status", "started_at", "completed_at", "output_summary"])
        for k in ["role", "agent_id", "task", "output_summary"]:
            text(agent.get(k), f"{p}.{k}")
        if isinstance(agent.get("agent_id"), str):
            agent_ids.add(agent["agent_id"])
        choice(agent.get("status"), f"{p}.status", {"COMPLETED", "BLOCKED", "PARTIAL"})
        started = timestamp(agent.get("started_at"), f"{p}.started_at")
        completed = timestamp(agent.get("completed_at"), f"{p}.completed_at")
        if started and completed and completed < started:
            err(p, "completed_at cannot precede started_at")
    if review.get("execution_status") == "COMPLETED" and (not isinstance(review.get("reviewer_agent"), str)
                                                        or review.get("reviewer_agent") not in agent_ids):
        err("review.reviewer_agent", "must identify an actually recorded agent")
    for i, raw in enumerate(seq(r.get("failures"), "failures")):
        p = f"failures[{i}]"
        failure = obj(raw, p, ["stage", "url", "reason", "resolution"])
        for k in ["stage", "reason", "resolution"]:
            text(failure.get(k), f"{p}.{k}")
        if failure.get("url") is not None:
            url(failure.get("url"), f"{p}.url")
    return errors


def require_valid(report: object) -> None:
    errors = validate_report(report)
    if errors:
        raise ValueError("Invalid report:\n" + "\n".join(errors))


def load_report(path: Path) -> dict:
    report = json.loads(path.read_text(encoding="utf-8"))
    require_valid(report)
    if path.parent.name != report["run_id"]:
        raise ValueError(f"{path}: parent directory must match run_id")
    return report


def render_markdown(report: dict) -> str:
    require_valid(report)
    r = report
    # Escape HTML and Markdown metacharacters in collected text. URLs are kept as
    # plain text rather than interpolated into Markdown link syntax.
    def safe(value: object) -> str:
        value = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return re.sub(r"([\\`*_{}\[\]()#!|])", r"\\\1", value)

    lines: list[str] = []

    def heading(label: str) -> None:
        lines.extend(["", f"## {label}", ""])

    def items(values: list) -> None:
        lines.extend(f"- {safe(v)}" for v in values)
        if not values:
            lines.append("- 없음 / 확인되지 않음")

    lines.extend([f"# {safe(r['company']['name'])} 리서치", "",
                  f"실행 ID: {safe(r['run_id'])}", "",
                  f"기업 코드: {safe(r['company']['ticker'])}", "",
                  f"실행 시각: {safe(r['executed_at'])} ({safe(r['timezone'])})", "",
                  f"대상 기간: {safe(r['period']['start'])} ~ {safe(r['period']['end'])}", "",
                  f"조사 상태: {safe(r['research_status'])}"])
    if r.get("report_kind") == "BASELINE":
        heading("기업 기본 분석 · 자료 범위")
        lines.append("최근7일 사건 보고서와 별도로 보관하는 기본 자료입니다. 대상 기간은 확인한 자료의 보고기간이며, 최신성·정정 여부의 검증 상태를 함께 확인하세요.")
        lines.append("최신성 확인: " + ("확인" if r["baseline_coverage"]["freshness_verified"] else "미완료"))
    heading("분석 주제")
    lines.append(safe(r["topic"]))
    heading("요약")
    lines.append(safe(r["summary"]))
    heading("기업 기본 분석 · 사실과 해석" if r.get("report_kind") == "BASELINE" else "주요 사건 · 사실과 해석")
    if not r["events"]:
        lines.append("조사기간 내 선정 기준을 충족한 검증 사건이 없습니다." if r["research_status"] == "COMPLETED"
                     else "검증된 사건 없음. 이는 중요한 새 소식이 없다는 결론이 아닙니다.")
    for event in r["events"]:
        lines.extend(["", f"### {safe(event['title'])}", "",
                      f"사건 ID: {safe(event['id'])} · 사건일: {safe(event['event_date'] or '미확인')} · 범위: {safe(event['scope'])}"])
        for field, label in [("facts", "확인된 사실"), ("interpretations", "분석적 해석")]:
            lines.extend(["", f"**{label}**", ""])
            items([f"{v['text']} [출처: {', '.join(v['source_ids'])}]" for v in event[field]])
        lines.extend(["", "**영향 경로와 성립 조건**", ""])
        for channel in event["impact_channels"]:
            lines.append(f"- {safe(channel['area'])}: {safe(channel['mechanism'])}")
            lines.extend(f"  - 조건: {safe(c)}" for c in channel["conditions"])
        lines.extend(["", "**반대 근거 및 한계**", ""])
        items(event["counter_evidence"])
        lines.extend(["", "**추후 확인할 항목**", ""])
        items(event["watch_items"])
    heading("전체 한계")
    items(r["limitations"])
    heading("후속 확인")
    items(r["follow_up"])
    heading("사용한 원문 자료")
    if not r["sources"]:
        lines.append("직접 확인한 원문이 없습니다.")
    for s in r["sources"]:
        if r.get("report_kind") == "BASELINE":
            lines.extend(["", "자료 구분: " + ("공식 페이지 · 접수정보/목차만 확인" if s["access_scope"] == "METADATA_ONLY" else "공식 원문 확인" if s["source_type"] == "ORIGINAL" else "외부 재게시 · 원본 대조 미완료"), "보고기간: " + safe(s["reporting_period"]), ""])
        lines.extend([f"- {safe(s['id'])}: {safe(s['title'])}",
                      f"  - 게시일: {safe(s['published_at'] or '미확인')}",
                      f"  - URL: <{s['url']}>",
                      f"  - 조회 시각: {safe(s['accessed_at'])} · 상태: {safe(s['access_status'])}",
                      f"  - 확인 근거: {safe(s['evidence'])}"])
    heading("Reviewer 검증 결과")
    review = r["review"]
    lines.extend([f"실행 상태: {safe(review['execution_status'])}", "",
                  f"검증 결과: {safe(review['status'] or '미실행')}", "",
                  f"검토자: {safe(review['reviewer_agent'] or '없음')}", "",
                  f"직접 확인한 출처: {safe(', '.join(review['checked_source_ids']) or '없음')}", ""])
    items([f"{f['severity']}: {f['message']} (사건: {f['event_id'] or '전체'}, 출처: {', '.join(f['source_ids']) or '없음'})"
           for f in review["findings"]])
    lines.extend(["", "검토의 한계:", ""])
    items(review["limitations"])
    heading("실제 에이전트 수행 이력")
    for a in r["agents"]:
        lines.extend([f"- {safe(a['role'])} ({safe(a['agent_id'])}) · {safe(a['status'])}",
                      f"  - 요청: {safe(a['task'])}",
                      f"  - 실행: {safe(a['started_at'])} ~ {safe(a['completed_at'])}",
                      f"  - 수행 결과: {safe(a['output_summary'])}"])
    heading("실패 또는 미완료 항목")
    items([f"{f['stage']}: {f['reason']} | URL: {f['url'] or '해당 없음'} | 해결: {f['resolution']}"
           for f in r["failures"]])
    lines.extend(["", "금융 리서치 학습 및 개발 포트폴리오이며 개인투자 권유가 아닙니다.", ""])
    return "\n".join(lines)


def save_report(report: dict, root: Path) -> Path:
    """Save a new run atomically at directory creation; never replace a run.

    root is the report collection directory, normally research/reports.
    """
    require_valid(report)
    markdown = render_markdown(report)
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    run_dir = root / report["run_id"]
    run_dir.mkdir(exist_ok=False)
    try:
        (run_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (run_dir / "report.md").write_text(markdown, encoding="utf-8")
    except BaseException:
        # Leave a partial run visible for diagnosis; do not pretend it succeeded.
        raise
    return run_dir
