#!/usr/bin/env python3
"""
Build the approval-preview HTML artifact from a consolidated tracker CSV.

Usage:
    python3 build_preview.py <consolidated.csv> <approval-preview-template.html> <output.html>

Expects the CSV to have exactly these headers (see references/consolidation-prompt.md):
    Company, Position, Applied Date, Current Status, Point of Contact,
    Stage History, Last Updated, Processed Message IDs

Reads the template HTML, which must contain the literal placeholder
"__TRACKER_DATA__" in its <script> block, and writes a new HTML file
with that placeholder replaced by the row data as a JSON array.

Doing this via a script (rather than hand-copying rows into the page,
or having an agent read the whole CSV into its own context) keeps large
datasets out of the conversation that's driving the rest of the skill.
"""
import csv
import json
import os
import sys


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)

    csv_path, template_path, output_path = sys.argv[1:4]

    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "company": r.get("Company", "").strip(),
                "position": r.get("Position", "").strip(),
                "applied": r.get("Applied Date", "").strip(),
                "status": r.get("Current Status", "").strip(),
                "contact": r.get("Point of Contact", "").strip(),
                "history": r.get("Stage History", "").strip(),
                "updated": r.get("Last Updated", "").strip(),
                "msgIds": [m.strip() for m in r.get("Processed Message IDs", "").split(";") if m.strip()],
            })

    print(f"Parsed {len(rows)} rows from {csv_path}")
    companies = sorted(set(r["company"] for r in rows))
    print(f"{len(companies)} unique companies")

    data_json = json.dumps(rows, ensure_ascii=False)
    # Prevent a literal </script> inside any field value from closing the
    # script tag early and breaking the page.
    data_json_safe = data_json.replace("</script", "<\\/script")

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    if "__TRACKER_DATA__" not in template:
        print("ERROR: template does not contain the __TRACKER_DATA__ placeholder", file=sys.stderr)
        sys.exit(1)

    out = template.replace("__TRACKER_DATA__", data_json_safe)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(out)

    print(f"Wrote {output_path} ({os.path.getsize(output_path)} bytes)")


if __name__ == "__main__":
    main()
