"""Create Markdown alongside a JSON report without overwriting prior history."""
from pathlib import Path
import sys

try:
    from .reports import load_report, render_markdown
except ImportError:
    from reports import load_report, render_markdown


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/render_report.py path/to/report.json", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    try:
        markdown = render_markdown(load_report(path))
        output = path.with_suffix(".md")
        if output.exists():
            if output.read_text(encoding="utf-8") != markdown:
                raise ValueError(f"Refusing to overwrite existing history: {output}")
        else:
            with output.open("x", encoding="utf-8") as stream:
                stream.write(markdown)
        print(f"Markdown verified: {output}")
        return 0
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
