"""Synthetic examples live only in tests; they are never public research."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.build import build
from scripts.reports import load_report, render_markdown, save_report, validate_report


def fixture_report():
    return {
        "schema_version": 1,
        "run_id": "synthetic-unit-test-only",
        "company": {"name": "SK하이닉스", "ticker": "000660"},
        "executed_at": "2026-10-20T16:16:03+09:00",
        "timezone": "Asia/Seoul",
        "period": {"start": "2026-10-13T16:16:03+09:00", "end": "2026-10-20T16:16:03+09:00"},
        "topic": "SYNTHETIC TEST ONLY",
        "summary": "SYNTHETIC TEST ONLY: not an actual financial claim",
        "research_status": "COMPLETED",
        "events": [{
            "id": "test-event", "title": "SYNTHETIC EVENT", "event_date": "2026-10-19", "scope": "DIRECT",
            "facts": [{"text": "synthetic assertion", "source_ids": ["test-source"]}],
            "interpretations": [{"text": "synthetic interpretation", "source_ids": ["test-source"]}],
            "impact_channels": [{"area": "매출", "mechanism": "synthetic pathway", "conditions": ["synthetic condition"]}],
            "counter_evidence": ["synthetic limitation"], "watch_items": ["synthetic next check"],
        }],
        "sources": [{"id": "test-source", "title": "SYNTHETIC SOURCE", "published_at": "2026-10-19",
                     "url": "https://example.com/test-only", "accessed_at": "2026-10-20T16:17:00+09:00",
                     "evidence": "synthetic evidence, never publish", "access_status": "VERIFIED"}],
        "limitations": ["test data only"], "follow_up": ["do not publish test fixtures"],
        "review": {"execution_status": "COMPLETED", "status": "PASS", "reviewer_agent": "test-reviewer",
                   "findings": [], "checked_source_ids": ["test-source"], "limitations": ["synthetic review"]},
        "agents": [{"role": "Reviewer", "agent_id": "test-reviewer", "task": "synthetic test",
                    "status": "COMPLETED", "started_at": "2026-10-20T16:17:00+09:00",
                    "completed_at": "2026-10-20T16:18:00+09:00", "output_summary": "synthetic output"}],
        "failures": [],
    }


class ContractTests(unittest.TestCase):
    def test_valid_synthetic_complete_report(self):
        self.assertEqual(validate_report(fixture_report()), [])

    def test_blocked_run_is_valid_but_not_passed_research(self):
        r = fixture_report()
        r.update(research_status="BLOCKED", events=[], sources=[])
        r["review"].update(status="INSUFFICIENT_EVIDENCE", checked_source_ids=[])
        self.assertEqual(validate_report(r), [])
        r["review"]["status"] = "PASS"
        self.assertTrue(any("PASS requires" in e for e in validate_report(r)))

    def test_completed_sourced_research_with_no_new_events_can_pass(self):
        r = fixture_report()
        r["events"] = []
        self.assertEqual(validate_report(r), [])
        self.assertIn("선정 기준을 충족한 검증 사건이 없습니다", render_markdown(r))

    def test_completed_research_cannot_claim_success_without_sources(self):
        r = fixture_report()
        r.update(events=[], sources=[])
        r["review"].update(execution_status="NOT_RUN", status=None, reviewer_agent=None, checked_source_ids=[])
        self.assertTrue(any("COMPLETED research requires" in e for e in validate_report(r)))

    def test_missing_field_and_malformed_types_are_rejected(self):
        r = fixture_report()
        del r["summary"]
        r["events"] = {"not": "array"}
        r["review"]["reviewer_agent"] = []
        errors = validate_report(r)
        self.assertTrue(any("summary" in e for e in errors))
        self.assertTrue(any("events" in e for e in errors))
        self.assertTrue(any("reviewer_agent" in e for e in errors))

    def test_malformed_json_values_never_crash_validator(self):
        for value in [None, [], 3, True, "bad", {}]:
            with self.subTest(value=value):
                self.assertTrue(validate_report(value))
        for key in fixture_report():
            for value in [None, [], {}, 3, True]:
                with self.subTest(key=key, value=value):
                    r = fixture_report()
                    r[key] = value
                    self.assertIsInstance(validate_report(r), list)
        for section, example in [("events", fixture_report()["events"][0]),
                                 ("sources", fixture_report()["sources"][0]),
                                 ("agents", fixture_report()["agents"][0])]:
            for key in example:
                for value in [None, [], {}, 3, True]:
                    with self.subTest(section=section, key=key, value=value):
                        r = fixture_report()
                        r[section][0][key] = value
                        self.assertIsInstance(validate_report(r), list)
        for key in fixture_report()["review"]:
            for value in [None, [], {}, 3, True]:
                with self.subTest(section="review", key=key, value=value):
                    r = fixture_report()
                    r["review"][key] = value
                    self.assertIsInstance(validate_report(r), list)

    def test_period_is_exactly_168_hours_and_ends_at_execution(self):
        r = fixture_report()
        r["period"]["start"] = "2026-10-14T16:16:03+09:00"
        self.assertTrue(any("168 hours" in e for e in validate_report(r)))
        r = fixture_report()
        r["period"]["end"] = "2026-10-20T16:16:04+09:00"
        self.assertTrue(any("must equal" in e for e in validate_report(r)))
        r = fixture_report()
        r["executed_at"] = "2026-10-20T07:16:03+00:00"
        self.assertTrue(any("+09:00" in e for e in validate_report(r)))

    def test_unsafe_slug_and_source_urls_are_rejected(self):
        for slug in ["../escape", "/tmp/escape", "UPPER", "", "a" * 101]:
            r = fixture_report()
            r["run_id"] = slug
            self.assertTrue(any("run_id" in e for e in validate_report(r)))
        for value in ["javascript:alert(1)", "http://example.com", "https://user:secret@example.com",
                      "https://example.com/ bad", "https://example.com/<script>", "https://example.com:bad/"]:
            r = fixture_report()
            r["sources"][0]["url"] = value
            self.assertTrue(any("HTTPS URL" in e for e in validate_report(r)))

    def test_duplicate_ids_unknown_references_and_missing_evidence(self):
        r = fixture_report()
        r["sources"].append(copy.deepcopy(r["sources"][0]))
        r["events"][0]["facts"][0]["source_ids"] = ["missing-source"]
        r["sources"][0]["evidence"] = ""
        errors = validate_report(r)
        self.assertTrue(any("duplicate source" in e for e in errors))
        self.assertTrue(any("unknown source" in e for e in errors))
        self.assertTrue(any("evidence" in e for e in errors))

    def test_max_three_events_and_blocked_events(self):
        r = fixture_report()
        r["events"] *= 4
        self.assertTrue(any("at most 3" in e for e in validate_report(r)))
        r = fixture_report()
        r["research_status"] = "BLOCKED"
        self.assertTrue(any("cannot publish events" in e for e in validate_report(r)))

    def test_review_cannot_claim_unrun_or_unverified_pass(self):
        r = fixture_report()
        r["review"]["execution_status"] = "NOT_RUN"
        self.assertTrue(any("NOT_RUN cannot claim" in e for e in validate_report(r)))
        r = fixture_report()
        r["review"]["checked_source_ids"] = []
        self.assertTrue(any("PASS requires" in e for e in validate_report(r)))
        r = fixture_report()
        r["review"]["reviewer_agent"] = "made-up-agent"
        self.assertTrue(any("actually recorded" in e for e in validate_report(r)))
        r = fixture_report()
        r["review"]["findings"] = [{"severity": "ERROR", "message": "unresolved",
                                    "event_id": None, "source_ids": []}]
        self.assertTrue(any("unresolved ERROR" in e for e in validate_report(r)))

    def test_markdown_covers_results_limits_sources_agents_and_failures(self):
        r = fixture_report()
        r["summary"] = "<script>alert('bad')</script>"
        r["failures"] = [{"stage": "test", "url": None, "reason": "synthetic failure", "resolution": "synthetic fix"}]
        md = render_markdown(r)
        for expected in ["SYNTHETIC EVENT", "synthetic assertion", "synthetic interpretation", "synthetic pathway",
                         "synthetic limitation", "synthetic next check", "test data only", "test-reviewer",
                         "PASS", "synthetic failure", "https://example.com/test-only"]:
            self.assertIn(expected, md)
        self.assertNotIn("<script>", md)
        self.assertIn("&lt;script&gt;", md)

    def test_save_never_overwrites_prior_report_and_rejects_invalid_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            r = fixture_report()
            saved = save_report(r, root)
            before = (saved / "report.json").read_bytes()
            self.assertEqual(load_report(saved / "report.json"), r)
            with self.assertRaises(FileExistsError):
                save_report(r, root)
            self.assertEqual((saved / "report.json").read_bytes(), before)
            r["run_id"] = "../escape"
            with self.assertRaises(ValueError):
                save_report(r, root)

    def test_directory_identity_must_match_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            path.write_text(json.dumps(fixture_report()), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "parent directory"):
                load_report(path)


class BuildTests(unittest.TestCase):
    def make_root(self, root):
        (root / "site").mkdir()
        (root / "site" / "index.html").write_text("<title>Synthetic fixture</title>", encoding="utf-8")
        save_report(fixture_report(), root / "research" / "reports")

    def test_build_lists_reports_in_order_under_project_subpath(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root)
            newer = fixture_report()
            newer["run_id"] = "synthetic-newer"
            newer["executed_at"] = newer["period"]["end"] = "2026-10-21T16:16:03+09:00"
            newer["period"]["start"] = "2026-10-14T16:16:03+09:00"
            save_report(newer, root / "research" / "reports")
            output = build(root)
            listing = json.loads((output / "data" / "reports.json").read_text())["reports"]
            self.assertEqual(listing[0]["run_id"], "synthetic-newer")
            for item in listing:
                self.assertFalse(item["path"].startswith("/"))
                self.assertTrue((output / item["path"]).is_file())
            self.assertTrue((output / ".nojekyll").is_file())
            self.assertTrue((output / "index.html").is_file())
            first = (output / "data" / "reports.json").read_bytes()
            build(root)
            self.assertEqual((output / "data" / "reports.json").read_bytes(), first)

    def test_bad_json_and_markdown_drift_preserve_existing_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root)
            output = build(root)
            before = (output / "data" / "reports.json").read_bytes()
            folder = root / "research" / "reports" / fixture_report()["run_id"]
            (folder / "report.md").write_text("changed history", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Markdown"):
                build(root)
            self.assertEqual((output / "data" / "reports.json").read_bytes(), before)
            (folder / "report.json").write_text("{broken", encoding="utf-8")
            with self.assertRaises(ValueError):
                build(root)

    def test_no_reports_is_failure_not_false_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "site").mkdir()
            (root / "site" / "index.html").write_text("ok")
            with self.assertRaisesRegex(ValueError, "No reports"):
                build(root)


if __name__ == "__main__":
    unittest.main()
