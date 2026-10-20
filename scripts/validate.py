"""Validate reports. Run from any directory with Python 3.12+."""
from pathlib import Path
import sys

try:
    from .reports import load_report
except ImportError:
    from reports import load_report

ROOT = Path(__file__).resolve().parents[1]


def main(paths: list[str] | None = None) -> int:
    paths = sys.argv[1:] if paths is None else paths
    selected = [Path(p) for p in paths] if paths else sorted((ROOT / "research" / "reports").glob("*/report.json")) + sorted((ROOT / "research" / "baselines").glob("*/report.json"))
    if not selected:
        print("FAIL: No report.json files found", file=sys.stderr)
        return 1
    failures = 0
    for path in selected:
        try:
            report = load_report(path)
            print(f"VALID {path.name} ({report['run_id']}, research={report['research_status']}, review={report['review']['status'] or 'NOT_RUN'})")
        except (OSError, ValueError) as exc:
            failures += 1
            print(f"FAIL {path}: {exc}", file=sys.stderr)
    print(f"Validated {len(selected)} report(s); failed {failures}. Structural validity is not source verification.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
