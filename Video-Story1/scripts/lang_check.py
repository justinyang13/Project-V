#!/Users/justin/Code/Project-V/.venv/bin/python
"""Blocking language check: none of the four banned words may appear in anything viewers see or read (narration, cards, captions, title, description, file names in output/)."""
import pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent; BAD = re.compile(r"chinese|taiwanese|japanese|korean", re.I)
files = [ROOT / "jobs/narration.json", ROOT / "scripts/cards.py", ROOT / "jobs/timeline.json"] + list((ROOT / "output").glob("*.srt")) + list((ROOT / "output").glob("*.txt")) + list((ROOT / "output").glob("*.md"))
bad = [(f.name, m.group(0)) for f in files if f.exists() for m in BAD.finditer(f.read_text())] + [(p.name, "filename") for p in (ROOT / "output").glob("*") if BAD.search(p.name)]
print("LANGUAGE CHECK:", "FAIL " + str(bad) if bad else "PASS (%d files)" % len(files)); sys.exit(1 if bad else 0)
