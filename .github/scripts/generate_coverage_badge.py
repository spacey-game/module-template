import json
import sys
from pathlib import Path


def extract_line_coverage_percent(summary: dict[str, object]) -> float:
    if "line_percent" in summary:
        return float(summary["line_percent"])

    lines = summary.get("lines")
    if isinstance(lines, dict) and "percent" in lines:
        return float(lines["percent"])

    raise KeyError("Could not find line coverage percent in summary JSON")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: generate_coverage_badge.py SUMMARY_JSON OUTPUT_SVG")

    summary = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    percent = extract_line_coverage_percent(summary)
    label = "coverage"
    value = f"{percent:.1f}%"
    label_width = 62
    value_width = max(42, len(value) * 7 + 12)
    width = label_width + value_width

    if percent >= 80:
        color = "#4c1"
    elif percent >= 60:
        color = "#dfb317"
    else:
        color = "#e05d44"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" role="img" aria-label="{label}: {value}">
  <title>{label}: {value}</title>
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r"><rect width="{width}" height="20" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <path fill="#555" d="M0 0h{label_width}v20H0z"/>
    <path fill="{color}" d="M{label_width} 0h{value_width}v20H{label_width}z"/>
    <path fill="url(#b)" d="M0 0h{width}v20H0z"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="{label_width / 2}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_width / 2}" y="14">{label}</text>
    <text x="{label_width + value_width / 2}" y="15" fill="#010101" fill-opacity=".3">{value}</text>
    <text x="{label_width + value_width / 2}" y="14">{value}</text>
  </g>
</svg>
'''
    Path(sys.argv[2]).write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()