"""Stage only YOUR hunks of a file that also holds someone else's uncommitted edits (see Runbook §G).
python3 scripts/stage_hunks.py wiki/SPEC.md wiki/lessons.md --skip 'justin|Volumes/SSD-4T|SSD'
--skip REGEX   a hunk whose REMOVED lines match REGEX is the other person's edit and is NOT staged (e.g. their path rewrites).
--only REGEX   alternatively: stage only hunks whose ADDED lines match REGEX (e.g. 'Tram|flicker|Snow').
--dry-run      print what would be staged. Mode-only changes (644 -> 755) are ignored. Afterwards check: git diff --cached | grep -ci '<their words>' = 0."""
import argparse, re, subprocess, sys
ap = argparse.ArgumentParser(); ap.add_argument("files", nargs="+"); ap.add_argument("--skip"); ap.add_argument("--only"); ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()
for f in a.files:
    d = subprocess.run(["git", "diff", "-U0", "--", f], capture_output=True, text=True, check=True).stdout.split("\n")
    head, hunks, cur = [], [], None
    for l in d:
        if l.startswith("@@"): cur = [l]; hunks.append(cur)
        elif cur is None: head.append(l)
        else: cur.append(l)
    def mine(h):
        rem = [x[1:] for x in h[1:] if x.startswith("-")]; add = [x[1:] for x in h[1:] if x.startswith("+")]
        if a.skip and any(re.search(a.skip, x) for x in rem): return False
        if a.only and not any(re.search(a.only, x) for x in add): return False
        return True
    keep = [h for h in hunks if mine(h)]
    print(f"{f}: {len(hunks)} hunks, {len(keep)} staged")
    if not keep or a.dry_run: continue
    patch = "\n".join([x for x in head if not x.startswith(("old mode", "new mode"))] + [x for h in keep for x in h]).rstrip("\n") + "\n"
    r = subprocess.run(["git", "apply", "--cached", "--unidiff-zero", "-"], input=patch, text=True, capture_output=True)
    if r.returncode: sys.exit(r.stderr)
