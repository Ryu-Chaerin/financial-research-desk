"""Build an offline-compatible static artifact; does not deploy anything."""
from pathlib import Path
import json
import shutil
import sys

try:
    from .reports import load_report, render_markdown
except ImportError:
    from reports import load_report, render_markdown

ROOT = Path(__file__).resolve().parents[1]


def build(root: Path = ROOT) -> Path:
    root = Path(root).resolve()
    source = root / "site"
    if not (source / "index.html").is_file():
        raise ValueError("site/index.html is required")
    paths = sorted((root / "research" / "reports").glob("*/report.json")) + sorted((root / "research" / "baselines").glob("*/report.json"))
    if not paths:
        raise ValueError("No reports found; cannot silently publish an empty artifact")
    reports = []
    for path in paths:
        report = load_report(path)
        expected_kind = "BASELINE" if path.parent.parent.name == "baselines" else "WEEKLY"
        if report.get("report_kind", "WEEKLY") != expected_kind:
            raise ValueError(f"Report kind does not match collection: {path}")
        expected = render_markdown(report)
        if not path.with_suffix(".md").is_file() or path.with_suffix(".md").read_text(encoding="utf-8") != expected:
            raise ValueError(f"Markdown missing or inconsistent with JSON: {path}")
        reports.append(report)
    reports.sort(key=lambda r: r["executed_at"], reverse=True)
    if len({r["run_id"] for r in reports}) != len(reports):
        raise ValueError("Duplicate run_id")
    # Validate completely before replacing an earlier build. Never delete source.
    output = root / "dist"
    if output.is_symlink():
        raise ValueError("Refusing to replace a symlinked dist directory")
    staging = root / ".cache" / "build-staging"
    if staging.is_symlink() or staging.parent.is_symlink():
        raise ValueError("Refusing symlinked staging directory")
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(source, staging)
    data_dir = staging / "data" / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    listing = []
    baselines = []
    for r in reports:
        run_id = r["run_id"]
        collection = "baselines" if r.get("report_kind") == "BASELINE" else "reports"
        target_dir = staging / "data" / collection
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / f"{run_id}.json").write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (target_dir / f"{run_id}.md").write_text(render_markdown(r), encoding="utf-8")
        target_list = baselines if collection == "baselines" else listing
        target_list.append({"run_id": run_id, "company_name": r["company"]["name"], "executed_at": r["executed_at"],
                        "summary": r["summary"], "research_status": r["research_status"],
                        "review_status": r["review"]["status"], "report_kind": r.get("report_kind", "WEEKLY"), "path": f"data/{collection}/{run_id}.json"})
    (staging / "data" / "reports.json").write_text(json.dumps({"reports": listing}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (staging / "data" / "baselines.json").write_text(json.dumps({"reports": baselines}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (staging / ".nojekyll").touch()
    if output.exists():
        shutil.rmtree(output)
    staging.rename(output)
    print(f"Built {len(reports)} report(s) into {output}; no deployment performed")
    return output


if __name__ == "__main__":
    try:
        build()
    except (OSError, ValueError) as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
