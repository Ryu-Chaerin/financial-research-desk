"use strict";

(() => {
  const content = document.getElementById("content");
  const page = document.body.dataset.page;
  const researchLabels = {COMPLETED: "조사 완료", PARTIAL: "조사 초안 · 최종 확정 보류", BLOCKED: "자료 접근 차단 · 조사 미완료"};
  const reviewLabels = {PASS: "PASS · 검토 통과", REVISE: "REVISE · 수정 필요", INSUFFICIENT_EVIDENCE: "INSUFFICIENT_EVIDENCE · 근거 부족"};
  const roleLabels = {"Research Manager": "Research Manager", Researcher: "Researcher", Reviewer: "Reviewer", "Designer & Developer": "Designer & Developer"};
  const text = value => typeof value === "string" ? value : "";
  const array = value => Array.isArray(value) ? value : [];
  const slugPattern = /^[A-Za-z0-9][A-Za-z0-9_-]*$/;
  let entries = [];

  function el(tag, className, value) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (value !== undefined) node.textContent = String(value);
    return node;
  }
  function append(parent, ...children) { children.filter(Boolean).forEach(child => parent.append(child)); return parent; }
  function link(label, href, className = "") {
    const node = el("a", className, label);
    node.href = href;
    return node;
  }
  function safeExternal(url) {
    try {
      const parsed = new URL(url);
      return parsed.protocol === "https:" && !parsed.username && !parsed.password ? parsed.href : null;
    } catch { return null; }
  }
  function external(label, url, className = "") {
    const href = safeExternal(url);
    if (!href) return el("span", "muted", `${label} (유효한 HTTPS 링크 없음)`);
    const node = link(label, href, className);
    node.target = "_blank";
    node.rel = "noopener noreferrer";
    return node;
  }
  function formatted(value, includeTime = true) {
    const date = new Date(value);
    if (!value || Number.isNaN(date.valueOf())) return "날짜 미확인";
    const options = {timeZone: "Asia/Seoul", year: "numeric", month: "2-digit", day: "2-digit"};
    if (includeTime) Object.assign(options, {hour: "2-digit", minute: "2-digit", hour12: false});
    return new Intl.DateTimeFormat("ko-KR", options).format(date);
  }
  function badge(value, type = "research") {
    const label = type === "research" ? researchLabels[value] : reviewLabels[value];
    const positive = value === "PASS" || value === "COMPLETED";
    return el("span", `badge ${positive ? "good" : "warning"}`, label || (type === "review" ? "검토 미실행" : "상태 미확인"));
  }
  function section(id, title) {
    return append(el("section", "report-section"), el("h2", "", title));
  }
  function identifiedSection(id, title) {
    const node = section(id, title);
    node.id = id;
    return node;
  }
  function bullets(items, empty = "기록된 항목이 없습니다.") {
    if (!array(items).length) return el("p", "muted", empty);
    const list = el("ul", "compact-list");
    items.forEach(item => list.append(el("li", "", typeof item === "string" ? item : text(item.text))));
    return list;
  }
  function metadata(items) {
    const node = el("div", "metadata");
    items.forEach(value => node.append(el("span", "", value)));
    return node;
  }
  function isFinal(item) {
    return item.research_status === "COMPLETED" && (item.review_status ?? item.review?.status) === "PASS";
  }
  function recordLabel(item) {
    return isFinal(item) ? "확정 보고서" : item.research_status === "BLOCKED" ? "조사 차단 기록" : "조사 초안 · 최종 확정 보류";
  }
  function finalSection() {
    const node = identifiedSection("latest-final", "최신 확정 보고서");
    const latest = entries.find(isFinal);
    node.append(latest ? summaryCard(latest, "최신 확정 보고서") : el("p", "empty-state", "아직 확정된 보고서가 없습니다. 조사 초안과 차단 기록은 최종 분석이 아닙니다."));
    return node;
  }
  function reportUrl(item) { return `${item.report_kind === "BASELINE" ? "baseline" : "report"}.html?id=${encodeURIComponent(item.run_id)}`; }
  function errorState(message) {
    content.replaceChildren();
    const box = append(el("section", "error-panel"), el("p", "eyebrow", "RESEARCH RECORD UNAVAILABLE"), el("h2", "", "기록을 표시할 수 없습니다"), el("p", "", message), el("p", "muted", "불러오지 못한 내용을 분석 결과로 대신 표시하지 않습니다. 잠시 후 다시 시도하거나 리포트 목록을 확인해 주세요."));
    box.id = "page-status";
    box.setAttribute("role", "alert");
    const retry = el("button", "button", "다시 시도");
    retry.type = "button";
    retry.addEventListener("click", load);
    box.append(append(el("div", "actions"), retry, link("리포트 목록", "company.html#history")));
    content.append(box);
  }
  async function fetchJson(path) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(path, {signal: controller.signal, cache: "no-cache"});
      if (!response.ok) throw new Error("HTTP");
      return await response.json();
    } finally { clearTimeout(timer); }
  }
  function validateIndex(index, collection = "reports") {
    if (!index || !Array.isArray(index.reports)) throw new Error("INDEX");
    const ids = new Set();
    return index.reports.map(item => {
      if (!item || !slugPattern.test(item.run_id) || ids.has(item.run_id) || typeof item.company_name !== "string" || typeof item.summary !== "string" || !researchLabels[item.research_status] || !Number.isFinite(Date.parse(item.executed_at)) || item.path !== `data/${collection}/${item.run_id}.json` || (collection === "baselines" && item.report_kind !== "BASELINE")) throw new Error("INDEX");
      ids.add(item.run_id);
      return item;
    }).sort((a, b) => Date.parse(b.executed_at) - Date.parse(a.executed_at));
  }
  function validateReport(report, runId) {
    if (!report || report.schema_version !== 1 || report.run_id !== runId || !report.company || typeof report.company.name !== "string" || !report.period || !Number.isFinite(Date.parse(report.period.start)) || !Number.isFinite(Date.parse(report.period.end)) || !Number.isFinite(Date.parse(report.executed_at)) || report.timezone !== "Asia/Seoul" || typeof report.topic !== "string" || typeof report.summary !== "string" || !researchLabels[report.research_status] || !report.review) throw new Error("REPORT");
    for (const key of ["events", "sources", "limitations", "follow_up", "agents", "failures"]) {
      if (!Array.isArray(report[key])) throw new Error("REPORT");
    }
    if (!Array.isArray(report.review.findings) || !Array.isArray(report.review.limitations) || !Array.isArray(report.review.checked_source_ids) || !["COMPLETED", "NOT_RUN"].includes(report.review.execution_status)) throw new Error("REPORT");
    if (report.review.execution_status === "COMPLETED" && !reviewLabels[report.review.status]) throw new Error("REPORT");
    if (report.review.execution_status === "NOT_RUN" && report.review.status !== null) throw new Error("REPORT");
    report.events.forEach(event => {
      if (!event || typeof event.id !== "string" || typeof event.title !== "string") throw new Error("REPORT");
      ["facts", "interpretations", "impact_channels", "counter_evidence", "watch_items"].forEach(key => { if (!Array.isArray(event[key])) throw new Error("REPORT"); });
      [...event.facts, ...event.interpretations].forEach(item => { if (!item || typeof item.text !== "string" || !Array.isArray(item.source_ids)) throw new Error("REPORT"); });
      event.impact_channels.forEach(item => { if (!item || !Array.isArray(item.conditions)) throw new Error("REPORT"); });
    });
    for (const key of ["sources", "agents", "failures"]) { if (report[key].some(item => !item || typeof item !== "object")) throw new Error("REPORT"); }
    if (page === "baseline" && (report.report_kind !== "BASELINE" || !report.baseline_coverage || typeof report.baseline_coverage.freshness_verified !== "boolean" || report.sources.some(source => !["ORIGINAL", "REPOST"].includes(source.source_type) || !["FULL_TEXT", "EXCERPTS_READ", "METADATA_ONLY"].includes(source.access_scope) || typeof source.original_verified !== "boolean"))) throw new Error("REPORT");
    return report;
  }
  function summaryCard(item, heading = "최근 실행 기록") {
    const node = el("article", "card");
    node.append(append(el("div", "card-top"), el("span", "small-label", heading), el("span", `badge ${isFinal(item) ? "good" : "warning"}`, recordLabel(item))));
    node.append(el("h3", "", item.company_name), el("p", "ticker", "000660 · SK hynix"), el("p", "report-summary", item.summary));
    node.append(metadata([`실행 ${formatted(item.executed_at)} KST`, item.review_status ? reviewLabels[item.review_status] : "검토 미실행"]));
    node.append(link("근거와 검토 기록 확인 →", reportUrl(item), "card-action"));
    return node;
  }
  function home() {
    content.replaceChildren();
    const heading = append(el("div", "section-heading"), el("h2", "", "리서치 데스크"), link("모든 실행 기록 보기 →", "company.html#history"));
    content.append(heading);
    if (!entries.length) {
      content.append(el("div", "empty-state", "아직 저장된 리포트가 없습니다. 실제 공개자료 조사와 검토가 완료되면 이곳에서 확인할 수 있습니다."));
      return;
    }
    content.append(finalSection());
    const latest = entries[0];
    const panel = append(el("aside", "card"), el("span", "small-label", "DESK OVERVIEW"), el("h3", "", "확인 가능한 기록"));
    for (const [label, value] of [["분석 대상", "SK하이닉스 1개 기업"], ["조사 범위", "실행 시점 기준 최근 7일"], ["보존된 실행", `${entries.length}회`], ["최근 검토", latest.review_status ? reviewLabels[latest.review_status] : "검토 미실행"]]) {
      panel.append(append(el("div", "stat-row"), el("span", "", label), el("strong", "", value)));
    }
    content.append(append(el("div", "dashboard-grid"), summaryCard(latest, "최근 실행 · " + recordLabel(latest)), panel));
  }
  function history() {
    const node = el("section", "history-section");
    node.id = "history";
    node.append(append(el("div", "section-heading"), el("h2", "", "전체 리포트 이력"), el("span", "muted", `${entries.length}개 실행 기록`)));
    if (!entries.length) return append(node, el("div", "empty-state", "저장된 실행 기록이 없습니다. 실제 조사를 수행한 후 기록을 추가합니다."));
    const list = el("div", "history-list");
    list.id = "report-list";
    entries.forEach(item => {
      const row = el("article", "card history-item");
      const date = append(el("div", "history-date"), el("p", "", `${formatted(item.executed_at)} KST`), el("span", `badge ${isFinal(item) ? "good" : "warning"}`, recordLabel(item)));
      const description = append(el("div"), el("h3", "", `${item.company_name} · 공개자료 리서치`), el("p", "report-summary", item.summary));
      row.append(date, description, link("리포트 보기 →", reportUrl(item), "card-action"));
      list.append(row);
    });
    return append(node, list);
  }
  async function baselineOverview() {
    const box = document.getElementById("baseline-overview");
    if (!box) return;
    box.replaceChildren(el("h2", "", "기업 기본 분석 · 사업보고서와 후속 보고서"));
    try {
      const records = validateIndex(await fetchJson("data/baselines.json"), "baselines");
      box.append(el("p", "muted", "최근7일 뉴스와 별도로 보관하는 기본 자료입니다. 최신 수집 기록이 최신 공시의 확인 완료를 뜻하지는 않습니다."));
      if (!records.length) return box.append(el("p", "empty-state", "아직 기본 분석 기록이 없습니다."));
      box.append(summaryCard(records[0], "기업 기본 분석 · 최근 수집 기록"));
      if (records.length > 1) {
        const archive = el("ul");
        records.slice(1).forEach(item => archive.append(append(el("li"), link(formatted(item.executed_at) + " · " + recordLabel(item), reportUrl(item)))));
        box.append(archive);
      }
    } catch {
      box.append(el("p", "notice warning", "기업 기본 자료를 불러오지 못했습니다. 아래 주간 조사 이력은 계속 확인할 수 있습니다."));
    }
  }
  function company() {
    content.replaceChildren();
    content.append(finalSection());
    if (entries.length) {
      const latest = entries[0];
      content.append(summaryCard(latest, "최근 실행 · " + recordLabel(latest)));
      if (latest.research_status === "BLOCKED") content.append(append(el("div", "notice warning sub-section"), el("h2", "", "최신 조사 상태를 먼저 확인해 주세요"), el("p", "", "자료 접근이 차단되어 원문 조사가 완료되지 않았습니다. 중요한 사건이 없다는 뜻이 아니며, 새로운 분석이나 투자 판단의 근거로 사용할 수 없습니다.")));
    }
    content.append(history());
  }
  function sourceRefs(ids, report) {
    if (!array(ids).length) return null;
    const block = el("span", "source-refs");
    block.append(el("span", "", "근거: "));
    ids.forEach(id => {
      const found = report.sources.find(source => source.id === id);
      block.append(found ? link(`[${id}]`, `#source-${encodeURIComponent(id)}`) : el("span", "muted", `[${id}: 출처 미확인]`));
    });
    return block;
  }
  function eventsSection(report) {
    const node = identifiedSection("events", report.report_kind === "BASELINE" ? "기업 기본 분석과 영향 경로" : "주요 사건과 기업 영향");
    if (!report.events.length) {
      node.append(el("div", "empty-state", report.research_status === "BLOCKED" ? "원문을 확인하지 못해 사건과 재무 영향을 작성하지 않았습니다. 이는 최근 중요한 사건이 없었다는 결론이 아닙니다." : "이번 실행에서 보고할 사건이 기록되지 않았습니다. 조사 범위와 검토의 한계를 함께 확인해 주세요."));
      return node;
    }
    report.events.forEach((event, i) => {
      const card = el("article", "card event-card");
      card.id = `event-${encodeURIComponent(event.id)}`;
      card.append(append(el("div"), el("span", "event-number", String(i + 1).padStart(2, "0")), el("h3", "", event.title)));
      card.append(el("p", "event-meta", `${event.scope === "DIRECT" ? "기업 직접 변화" : "산업 전반 변화"} · 사건 발생일 ${event.event_date || "미확인"}`));
      const evidenceGrid = el("div", "evidence-grid");
      [["확인된 사실", event.facts, false], ["분석적 해석", event.interpretations, true]].forEach(([title, items, inferred]) => {
        const block = append(el("section", `evidence-block${inferred ? " inference" : ""}`), el("h4", "", title));
        const list = el("ul");
        array(items).forEach(item => list.append(append(el("li", "", item.text), sourceRefs(item.source_ids, report))));
        block.append(items.length ? list : el("p", "muted", "기록된 내용이 없습니다."));
        evidenceGrid.append(block);
      });
      card.append(evidenceGrid, el("h4", "", "영향 경로와 성립 조건"));
      const impacts = el("div", "impact-list");
      event.impact_channels.forEach(impact => {
        impacts.append(append(el("div", "impact-item"), el("span", "badge", text(impact.area)), el("p", "", text(impact.mechanism)), el("strong", "", "성립 조건"), bullets(impact.conditions, "성립 조건이 기록되지 않았습니다.")));
      });
      card.append(impacts, append(el("div", "sub-section"), el("h4", "", "반대 근거 · 판단의 한계"), bullets(event.counter_evidence)), append(el("div", "sub-section"), el("h4", "", "향후 확인할 지표 · 사건"), bullets(event.watch_items)));
      node.append(card);
    });
    return node;
  }
  function reviewSection(report) {
    const node = identifiedSection("review", "Reviewer 독립 검토");
    node.append(append(el("div", "status-line"), badge(report.review.status, "review"), el("span", "muted", report.review.execution_status === "COMPLETED" ? "검토 실행 완료" : "검토 미실행")));
    if (report.review.reviewer_agent) node.append(el("p", "agent-id", `실제 검토 에이전트: ${report.review.reviewer_agent}`));
    if (report.review.status === "INSUFFICIENT_EVIDENCE") node.append(el("p", "sub-section", "독립 검토가 실행되었더라도 원문 근거가 부족하면 분석은 검증된 것으로 간주하지 않습니다."));
    if (!report.review.findings.length) node.append(el("p", "muted sub-section", "기록된 검토 지적 사항이 없습니다. 이 사실만으로 검토 통과를 의미하지 않습니다."));
    report.review.findings.forEach(finding => {
      if (!finding || typeof finding !== "object") throw new Error("REPORT");
      const item = append(el("div", "review-finding"), el("span", `badge ${finding.severity === "ERROR" ? "danger" : "warning"}`, text(finding.severity)), el("p", "", text(finding.message)), sourceRefs(finding.source_ids, report));
      if (finding.event_id) item.append(link("관련 사건 보기", `#event-${encodeURIComponent(finding.event_id)}`));
      node.append(item);
    });
    node.append(append(el("div", "sub-section"), el("h4", "", "검토자가 확인한 출처"), report.review.checked_source_ids.length ? sourceRefs(report.review.checked_source_ids, report) : el("p", "muted", "직접 확인한 원문 출처가 없습니다.")));
    node.append(append(el("div", "sub-section"), el("h4", "", "검토 한계"), bullets(report.review.limitations)));
    return node;
  }
  function sourcesSection(report) {
    const node = identifiedSection("sources", "원문 출처");
    node.append(el("p", "muted", "출처의 게시일은 사건 발생일과 다를 수 있습니다. 링크가 있다는 사실과 원문 검증에 성공했다는 사실을 구분합니다."));
    if (!report.sources.length) return append(node, el("div", "empty-state", "확인된 원문 출처가 없습니다. 접속을 시도한 주소와 실패 원인은 아래 실행 실패 기록에 따로 남깁니다."));
    const list = el("ol", "source-list");
    report.sources.forEach(source => {
      const item = el("li", "source-item");
      item.id = `source-${encodeURIComponent(source.id)}`;
      if (report.report_kind === "BASELINE") item.append(el("p", "notice warning", source.access_scope === "METADATA_ONLY" ? "공식 접수정보·목차만 확인 · 재무 본문 미확인" : source.source_type === "REPOST" ? "외부 재게시본 · 원본 대조 미완료" : "공식 본문 확인"), el("p", "muted", `자료의 보고기간: ${text(source.reporting_period)}`));
      item.append(el("span", "small-label", `SOURCE ${text(source.id)}`), el("h3", "", text(source.title)), external(text(source.url), source.url, "source-url source-link"), el("p", "", text(source.evidence)), metadata([`게시일 ${source.published_at ? formatted(source.published_at, false) : "미확인"}`, `조회 ${formatted(source.accessed_at)} KST`, source.access_scope === "METADATA_ONLY" ? "접수정보·목차 확인" : source.source_type === "REPOST" ? "재게시 일부 본문 확인 · 원본 대조 미완료" : source.access_status === "VERIFIED" ? "원문 확인" : "확인 상태 미상"]));
      list.append(item);
    });
    return append(node, list);
  }
  function agentsSection(report) {
    const node = identifiedSection("agents", "실제 에이전트 실행 이력");
    node.append(el("p", "muted", "아래는 이 실행에서 기록된 실제 작업입니다. 역할 이름만으로 독립 검증 여부를 추정하지 마세요."));
    if (!report.agents.length) return append(node, el("div", "empty-state", "실제 에이전트 이력이 기록되지 않았습니다."));
    const timeline = el("ol", "timeline");
    report.agents.forEach(agent => {
      const item = append(el("li"), el("h3", "", roleLabels[agent.role] || text(agent.role)), el("span", "agent-id", text(agent.agent_id)), el("p", "", `요청 업무: ${text(agent.task)}`), el("p", "", `수행 결과: ${text(agent.output_summary)}`));
      const labels = {COMPLETED: "작업 완료", PARTIAL: "부분 수행", BLOCKED: "진행 차단"};
      item.append(append(el("div", "status-line"), el("span", `badge ${agent.status === "COMPLETED" ? "good" : "warning"}`, labels[agent.status] || "상태 미확인")));
      item.append(metadata([`시작 ${formatted(agent.started_at)} KST`, `종료 ${formatted(agent.completed_at)} KST`]));
      timeline.append(item);
    });
    return append(node, timeline);
  }
  function failuresSection(report) {
    const node = identifiedSection("failures", "실행 실패 · 미완료 항목");
    if (!report.failures.length) return append(node, el("p", "muted", "이 실행에 기록된 실패 항목이 없습니다. 기록 범위를 넘어선 검증 성공을 뜻하지는 않습니다."));
    report.failures.forEach(failure => {
      const card = append(el("article", "failure-item"), el("h3", "", text(failure.stage)), el("p", "", text(failure.reason)));
      if (failure.url) card.append(external(failure.url, failure.url));
      card.append(el("p", "", `다음 조치: ${text(failure.resolution)}`));
      node.append(card);
    });
    return node;
  }
  function notesSection(report) {
    const node = identifiedSection("notes", "나의 공부 메모");
    const panel = el("div", "notes-panel");
    const label = el("label", "", "이 리포트를 읽고 배운 점");
    label.htmlFor = "study-note";
    const input = el("textarea");
    input.id = "study-note";
    input.placeholder = "새로 알게 된 용어, 의문점, 다음에 확인할 내용을 적어 보세요.";
    input.setAttribute("aria-describedby", "note-help note-status");
    const help = el("p", "note-help", "메모는 이 브라우저에만 저장되며 공개 저장소나 서버로 전송되지 않습니다. 다른 기기·브라우저와 동기화되지 않고 브라우저 데이터 삭제 시 사라질 수 있습니다. 공용 기기에서는 저장을 피하세요.");
    help.id = "note-help";
    const status = el("span", "note-status");
    status.id = "note-status";
    status.setAttribute("role", "status");
    const key = `financial-research-desk:note:${report.run_id}`;
    try { input.value = localStorage.getItem(key) || ""; } catch { status.textContent = "이 브라우저에서는 메모 저장소를 읽을 수 없습니다. 메모를 별도로 복사해 보관하세요."; }
    input.addEventListener("input", () => { status.textContent = "저장하지 않은 변경사항이 있습니다."; });
    const save = el("button", "button", "이 브라우저에 저장");
    save.id = "save-note";
    save.type = "button";
    save.addEventListener("click", () => {
      try { localStorage.setItem(key, input.value); status.textContent = "이 브라우저에 저장했습니다. 공개 게시되지 않습니다."; }
      catch { status.textContent = "저장하지 못했습니다. 브라우저 저장 공간·설정을 확인하거나 메모를 별도로 복사해 보관하세요."; }
    });
    panel.append(label, input, help, append(el("div", "note-actions"), save, status));
    node.append(panel);
    return node;
  }
  function renderReport(report, entry) {
    const header = el("header", "report-heading");
    header.append(el("p", "eyebrow", "SK HYNIX · RESEARCH RECORD"), append(el("div", "status-line"), badge(report.research_status), badge(report.review.status, "review")), el("h1", "", report.topic), el("p", "page-intro", report.summary));
    header.append(metadata([`${report.company.name} · ${text(report.company.ticker)}`, `실행 ${formatted(report.executed_at)} KST`, `기준 시간대 ${report.timezone}`, `조사 기간 ${formatted(report.period.start)} ~ ${formatted(report.period.end)} KST`]));
    header.append(el("p", "record-state", recordLabel(report)));
    if (report.report_kind === "BASELINE") header.append(el("p", "notice warning", "기업 기본 자료 · 최근7일 뉴스와 별도입니다. 위 기간은 자료의 보고기간입니다. 최신성·정정 확인: " + (report.baseline_coverage.freshness_verified ? "확인" : "미완료")));
    header.append(el("p", "report-id", `실행 ID: ${report.run_id}`));
    const download = link("구조화된 JSON 보기 ↗", entry.path);
    download.target = "_blank";
    download.rel = "noopener";
    header.append(append(el("div", "download-links"), download, link("과거 리포트 목록", "company.html#history"), link("기업 기본 자료 확인", "company.html#baseline-overview")));
    const body = el("div", "report-body");
    body.id = "report-content";
    if (report.research_status === "BLOCKED") body.append(append(el("div", "notice warning"), el("h2", "", "자료 접근 차단으로 실제 조사가 미완료되었습니다"), el("p", "", "이 기록은 분석 성공 보고서가 아닙니다. 공개 원문을 읽지 못했으므로 중요한 사건의 유무나 재무 영향을 판단할 수 없습니다. 접속 실패와 실제 검토 결과를 아래에서 확인하세요.")));
    else if (report.research_status === "PARTIAL") body.append(append(el("div", "notice warning"), el("h2", "", "조사 초안이며 최종 확정을 보류합니다"), el("p", "", "분석의 한계와 검토 지적 사항을 확인하고 부족한 근거를 검증된 사실로 받아들이지 마세요.")));
    if (report.research_status === "COMPLETED" && !isFinal(report)) body.append(el("p", "notice warning", "Reviewer 통과 전 조사 초안입니다. 최종 분석 확정을 보류합니다."));
    const limitations = identifiedSection("limitations", "판단의 한계와 다음 확인 항목");
    limitations.append(el("h3", "", "반대 근거 · 조사 한계"), bullets(report.limitations), el("h3", "sub-section", "추후 확인할 항목"), bullets(report.follow_up));
    body.append(eventsSection(report), reviewSection(report), sourcesSection(report), limitations, agentsSection(report), failuresSection(report), notesSection(report));
    const aside = el("aside", "report-aside");
    const toc = el("nav");
    toc.setAttribute("aria-label", "리포트 목차");
    [["events", "주요 사건과 영향"], ["review", "Reviewer 검토"], ["sources", "원문 출처"], ["limitations", "한계와 후속 확인"], ["agents", "실제 실행 이력"], ["failures", "실패 · 미완료"], ["notes", "나의 공부 메모"]].forEach(([id, title]) => toc.append(link(title, `#${id}`)));
    aside.append(append(el("div", "card"), el("span", "small-label", "IN THIS REPORT"), toc), el("p", "aside-note", "사실 · 해석 · 검토 상태를 함께 읽어 주세요. 학습용 자료이며 투자 권유가 아닙니다."));
    content.replaceChildren(header, append(el("div", "report-layout"), body, aside));
    document.title = `${report.company.name} 리포트 · Financial Research Desk`;
  }
  async function load() {
    const loading = el("p", "loading", "리서치 기록을 불러오고 있습니다…");
    loading.id = "page-status";
    loading.setAttribute("role", "status");
    content.replaceChildren(loading);
    try {
      const collection = page === "baseline" ? "baselines" : "reports";
      entries = validateIndex(await fetchJson(`data/${collection}.json`), collection);
      if (page === "home") return home();
      if (page === "company") {
        company();
        baselineOverview();
        if (location.hash === "#history") document.getElementById("history")?.scrollIntoView();
        return;
      }
      const id = new URLSearchParams(location.search).get("id");
      if (!id || !slugPattern.test(id)) return errorState("리포트 식별자가 없거나 올바르지 않습니다. 목록에서 리포트를 선택해 주세요.");
      const entry = entries.find(item => item.run_id === id);
      if (!entry) return errorState("요청한 리포트가 현재 목록에 없습니다. 주소를 확인하거나 다른 실행 기록을 선택해 주세요.");
      const report = validateReport(await fetchJson(entry.path), id);
      renderReport(report, entry);
    } catch {
      errorState("데이터 파일에 접근할 수 없거나 기록 형식이 올바르지 않습니다. 연구 결과를 확인한 것으로 처리하지 않습니다.");
    }
  }
  load();
})();
