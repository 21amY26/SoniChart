"""Map headings, tables and figures to the page labels printed in the footer of a Word-rendered PDF.

Usage: python report/paginate.py report/_render/report.pdf report/_render/pages.json
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
pdf, out = sys.argv[1], Path(sys.argv[2])
text = subprocess.run(["swift", str(HERE / "pdftext.swift"), pdf], capture_output=True, text=True, check=True).stdout
pages = text.split("\f")[:-1]


def label(t):
    lines = [l.strip() for l in t.splitlines() if l.strip()]
    for l in reversed(lines[-3:]):
        if re.fullmatch(r"[ivxlc]+|\d+", l):
            return l
    return "?"


labels = [label(t) for t in pages]
body_start = next(i for i, l in enumerate(labels) if l == "1")
res = {}


def find(key, pattern, start, end=None):
    for i in range(start, end or len(pages)):
        if re.search(pattern, pages[i], re.M):
            res[key] = labels[i]; return


find("Acknowledgement", r"^ACKNOWLEDGEMENT", 1, body_start)
find("Abstract", r"^ABSTRACT", 1, body_start)
find("List of Tables", r"^LIST OF TABLES", 1, body_start)
find("List of Figures", r"^LIST OF FIGURES", 1, body_start)
for n in range(1, 7):
    find(f"Chapter {n}", rf"^CHAPTER {n}\s*$", body_start)
for m in re.finditer(r"^(\d\.\d) ([A-Z][^\n]{3,})$", "\n".join(pages[body_start:]), re.M):
    pass
for i in range(body_start, len(pages)):
    for m in re.finditer(r"^(\d\.\d) [A-Z]", pages[i], re.M):
        res.setdefault(m.group(1), labels[i])
    for m in re.finditer(r"^(Table \d\.\d|Fig\. \d\.\d):", pages[i], re.M):
        res.setdefault(m.group(1), labels[i])
find("REFERENCES", r"^REFERENCES\s*$", body_start)
find("ANNEXURES", r"^ANNEXURES\s*$", body_start)
out.write_text(json.dumps(res, indent=1))
print(f"{len(pages)} pages; labels: {' '.join(labels)}")
print(json.dumps(res))
