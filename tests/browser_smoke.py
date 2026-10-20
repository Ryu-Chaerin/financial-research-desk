"""Real Chromium checks. Synthetic responses are confined to test interception.

Run from the repository root after scripts/build.py. Never deploys or sends notes.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import sys
import tempfile
from threading import Thread
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))
from test_data import fixture_report

try:
    from playwright.sync_api import sync_playwright, expect
except ImportError:
    raise SystemExit("Browser tests NOT RUN: Python Playwright is required in the cloud environment")


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class BrowserSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / "dist/data/reports.json").is_file():
            raise RuntimeError("Run python3 scripts/build.py before browser tests")
        executable = shutil.which("chromium") or shutil.which("chromium-browser")
        if not executable:
            raise RuntimeError("Browser tests NOT RUN: system Chromium is missing")
        cls.tmp = tempfile.TemporaryDirectory()
        webroot = Path(cls.tmp.name)
        shutil.copytree(ROOT / "dist", webroot / "financial-research-desk")
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(webroot)))
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}/financial-research-desk/"
        cls.listing = json.loads((ROOT / "dist/data/reports.json").read_text(encoding="utf-8"))["reports"]
        cls.real_id = cls.listing[0]["run_id"]
        cls.real_report = json.loads((ROOT / "dist" / cls.listing[0]["path"]).read_text(encoding="utf-8"))
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(executable_path=executable, headless=True, args=["--no-sandbox"])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.tmp.cleanup()

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1440, "height": 1000})
        self.page = self.context.new_page()
        self.errors = []
        self.external = []
        self.writes = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))

        def network(route):
            request = route.request
            if not request.url.startswith(self.base):
                self.external.append(request.url)
                route.abort()
            else:
                if request.method != "GET":
                    self.writes.append(request.method)
                route.continue_()

        self.context.route("**/*", network)

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [], "Uncaught browser errors")
        self.assertEqual(self.external, [], "Unexpected external requests")
        self.assertEqual(self.writes, [], "Unexpected network writes, including notes")

    def go_report(self, run_id=None):
        self.page.goto(self.base + "report.html?id=" + (run_id or self.real_id))
        expect(self.page.locator("#study-note")).to_be_visible()

    def synthetic(self, report=None, older=False):
        report = report or fixture_report()
        reports = [report]
        if older:
            old = fixture_report()
            old["run_id"] = "synthetic-browser-older"
            old["executed_at"] = old["period"]["end"] = "2026-10-19T16:16:03+09:00"
            old["period"]["start"] = "2026-10-12T16:16:03+09:00"
            reports.append(old)
        listing = {"reports": [{"run_id": r["run_id"], "company_name": r["company"]["name"],
                    "executed_at": r["executed_at"], "summary": r["summary"],
                    "research_status": r["research_status"], "review_status": r["review"]["status"],
                    "path": f"data/reports/{r['run_id']}.json"} for r in reports]}
        self.context.route("**/data/reports.json", lambda route: route.fulfill(json=listing))
        for item in reports:
            self.context.route("**/data/reports/" + item["run_id"] + ".json",
                               lambda route, request, data=item: route.fulfill(json=data))
        return reports

    def assert_friendly_error(self):
        expect(self.page.locator("#page-status")).to_contain_text("다시")
        expect(self.page.locator("nav")).to_be_visible()

    def test_real_home_company_and_report_state(self):
        self.page.goto(self.base + "index.html")
        expect(self.page.locator("a[href^='report.html?id=']").first).to_be_visible()
        self.page.goto(self.base + "company.html")
        expect(self.page.locator("#report-list")).to_contain_text("SK하이닉스")
        links = self.page.locator("#report-list a")
        expect(links).to_have_count(len(self.listing))
        links.last.click()
        expect(self.page.locator(".report-id")).to_contain_text(self.listing[-1]["run_id"])
        self.go_report()
        body = self.page.locator("main")
        if self.real_report["research_status"] == "BLOCKED":
            expect(body).to_contain_text("조사 미완료")
            self.assertEqual(self.real_report["events"], [])
        if self.real_report["review"]["status"]:
            expect(body).to_contain_text(self.real_report["review"]["status"])
        for agent in self.real_report["agents"]:
            expect(body).to_contain_text(agent["agent_id"])
        expect(self.page.locator(".source-link")).to_have_count(len(self.real_report["sources"]))
        self.assertNotIn("synthetic", body.inner_text().lower())

    def test_synthetic_source_links_facts_interpretations_and_archive(self):
        reports = self.synthetic(older=True)
        self.page.goto(self.base + "company.html")
        links = self.page.locator("#report-list a[href^='report.html?id=']")
        expect(links).to_have_count(2)
        links.nth(1).click()
        expect(self.page.locator("main")).to_contain_text(reports[1]["run_id"])
        expect(self.page.locator("main")).to_contain_text("synthetic assertion")
        expect(self.page.locator("main")).to_contain_text("synthetic interpretation")
        source = self.page.locator(".source-link")
        expect(source).to_have_attribute("href", "https://example.com/test-only")
        self.assertIn("noopener", source.get_attribute("rel"))

    def test_newer_draft_does_not_replace_latest_final(self):
        reports = self.synthetic(older=True)
        reports[0]["research_status"] = "PARTIAL"
        reports[0]["review"]["status"] = "INSUFFICIENT_EVIDENCE"
        # Re-register interception with a newer draft and an older confirmed report.
        listing = {"reports": [{"run_id": r["run_id"], "company_name": r["company"]["name"],
                    "executed_at": r["executed_at"], "summary": r["summary"],
                    "research_status": r["research_status"], "review_status": r["review"]["status"],
                    "path": f"data/reports/{r['run_id']}.json"} for r in reports]}
        self.context.route("**/data/reports.json", lambda route: route.fulfill(json=listing))
        for path in ["index.html", "company.html"]:
            self.page.goto(self.base + path)
            final = self.page.locator("#latest-final")
            expect(final.locator("a")).to_have_attribute("href", "report.html?id=" + reports[1]["run_id"])
            expect(self.page.locator("main")).to_contain_text("조사 초안")
        self.go_report(reports[0]["run_id"])
        expect(self.page.locator(".record-state")).to_contain_text("최종 확정 보류")

    def test_no_final_when_all_runs_are_drafts(self):
        for research, review in [("PARTIAL", "INSUFFICIENT_EVIDENCE"), ("COMPLETED", "REVISE"),
                                 ("COMPLETED", None), ("BLOCKED", "INSUFFICIENT_EVIDENCE")]:
            report = fixture_report()
            report["research_status"] = research
            report["review"]["status"] = review
            if review is None:
                report["review"]["execution_status"] = "NOT_RUN"
            self.synthetic(report)
            for path in ["index.html", "company.html"]:
                self.page.goto(self.base + path)
                expect(self.page.locator("#latest-final")).to_contain_text("아직 확정된 보고서가 없습니다")
                expect(self.page.locator("#latest-final a")).to_have_count(0)

    def test_notes_persist_only_in_browser(self):
        self.go_report()
        note = "PRIVATE BROWSER TEST NOTE <b>literal</b>"
        self.page.locator("#study-note").fill(note)
        self.page.locator("#save-note").click()
        expect(self.page.locator("#note-status")).to_contain_text("저장")
        self.page.reload()
        expect(self.page.locator("#study-note")).to_have_value(note)
        other = self.browser.new_context()
        try:
            page = other.new_page()
            page.goto(self.base + "report.html?id=" + self.real_id)
            expect(page.locator("#study-note")).to_have_value("")
        finally:
            other.close()

    def test_notes_are_isolated_between_reports(self):
        reports = self.synthetic(older=True)
        self.go_report(reports[0]["run_id"])
        self.page.locator("#study-note").fill("only first report")
        self.page.locator("#save-note").click()
        self.go_report(reports[1]["run_id"])
        expect(self.page.locator("#study-note")).to_have_value("")

    def test_storage_failure_does_not_break_report(self):
        self.page.add_init_script("Storage.prototype.setItem = function(){throw new Error('test denied')}")
        self.go_report()
        self.page.locator("#study-note").fill("unsaved")
        self.page.locator("#save-note").click()
        expect(self.page.locator("#note-status")).not_to_be_empty()
        expect(self.page.locator("#note-status")).to_contain_text("저장하지 못")
        expect(self.page.locator("main")).to_contain_text(self.real_report["topic"])

    def test_text_is_not_executed_as_html(self):
        report = fixture_report()
        payload = '<img src=x onerror="window.__injected=true">'
        report["summary"] = payload
        report["events"][0]["facts"][0]["text"] = payload
        self.synthetic(report)
        self.go_report(report["run_id"])
        expect(self.page.locator("main")).to_contain_text(payload)
        self.assertIsNone(self.page.evaluate("window.__injected"))
        expect(self.page.locator("main img")).to_have_count(0)

    def test_empty_history(self):
        self.context.route("**/data/reports.json", lambda route: route.fulfill(json={"reports": []}))
        self.page.goto(self.base)
        expect(self.page.locator("main")).to_contain_text("없")

    def test_broken_listing_json(self):
        self.context.route("**/data/reports.json", lambda route: route.fulfill(body="{broken", content_type="application/json"))
        self.page.goto(self.base)
        self.assert_friendly_error()

    def test_missing_listing(self):
        self.context.route("**/data/reports.json", lambda route: route.fulfill(status=404, body="missing"))
        self.page.goto(self.base)
        self.assert_friendly_error()

    def test_broken_and_incomplete_report_json(self):
        for body in ["{broken", json.dumps({"run_id": self.real_id})]:
            with self.subTest(body=body):
                self.context.route("**/data/reports/" + self.real_id + ".json",
                                   lambda route, request, data=body: route.fulfill(body=data, content_type="application/json"))
                self.page.goto(self.base + "report.html?id=" + self.real_id)
                self.assert_friendly_error()

    def test_unknown_report_id(self):
        self.page.goto(self.base + "report.html?id=../../unknown")
        expect(self.page.locator("#page-status")).not_to_be_empty()
        expect(self.page.locator("nav")).to_be_visible()
        expect(self.page.locator("#study-note")).to_have_count(0)

    def test_real_baseline_sources_and_company_link(self):
        listing = json.loads((ROOT / "dist/data/baselines.json").read_text())["reports"]
        self.assertTrue(listing, "Expected a real baseline record")
        baseline = json.loads((ROOT / "dist" / listing[0]["path"]).read_text())
        self.page.goto(self.base + "company.html")
        self.page.locator("#baseline-overview a[href^='baseline.html']").first.click()
        expect(self.page.locator("#study-note")).to_be_visible()
        expect(self.page.locator(".report-id")).to_contain_text(baseline["run_id"])
        expect(self.page.locator(".source-link")).to_have_count(len(baseline["sources"]))
        expect(self.page.locator("main")).to_contain_text("원본 대조 미완료")
        expect(self.page.locator("main")).to_contain_text("접수정보·목차만 확인")
        expect(self.page.locator("main")).to_contain_text("최신성·정정 확인: 미완료")
        expect(self.page.locator("main")).to_contain_text("INSUFFICIENT_EVIDENCE")
        for width in [320, 390]:
            self.page.set_viewport_size({"width": width, "height": 844})
            self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"))

    def test_baseline_fetch_error_does_not_hide_weekly_history(self):
        self.context.route("**/data/baselines.json", lambda route: route.fulfill(status=404, body="missing"))
        self.page.goto(self.base + "company.html")
        expect(self.page.locator("#baseline-overview")).to_contain_text("불러오지 못")
        expect(self.page.locator("#report-list a")).to_have_count(len(self.listing))

    def test_broken_baseline_report_is_friendly_error(self):
        listing = json.loads((ROOT / "dist/data/baselines.json").read_text())["reports"]
        item = listing[0]
        self.context.route("**/" + item["path"], lambda route: route.fulfill(json={"run_id": item["run_id"]}))
        self.page.goto(self.base + "baseline.html?id=" + item["run_id"])
        self.assert_friendly_error()

    def test_mobile_layouts(self):
        for width in [320, 390]:
            self.page.set_viewport_size({"width": width, "height": 844})
            for path in ["index.html", "company.html", "report.html?id=" + self.real_id]:
                with self.subTest(width=width, path=path):
                    self.page.goto(self.base + path)
                    if path.startswith("report"):
                        expect(self.page.locator("#study-note")).to_be_visible()
                    else:
                        expect(self.page.locator("a[href^='report.html?id=']").first).to_be_visible()
                    self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
