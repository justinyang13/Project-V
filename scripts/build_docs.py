"""Build self-contained HTML docs from the markdown sources. Run from Project-V after any doc change:
.venv/bin/python scripts/build_docs.py
Master docs -> wiki/html/*.html (published as the Pages site): wiki/SPEC.md, wiki/*.md, wiki/html-src/{style.css,index.body.html}.
Per-video page -> Video-<Name>/RUNLOG.html (stays with its video folder, NOT in the master site): built from that folder's RUNLOG.md (+ qc-report.md).
Each page is a single file (CSS inlined, no network needed). Links to repo files that aren't pages point to GitHub."""
import glob, os, re, html
import markdown

REPO = "https://github.com/justinyang13/Project-V/blob/main/"
VIDEO_DIRS = sorted(d for d in glob.glob("Video-*") if os.path.isfile(f"{d}/RUNLOG.md"))
PAGES = [  # (output file, title, source md files joined in order)
    ("spec.html", "Spec", ["wiki/SPEC.md"]),
    ("runbook.html", "Runbook", ["wiki/runbook.md"]),
    ("lessons.html", "Lessons", ["wiki/lessons.md"]),
    ("music.html", "Music", ["wiki/music.md"]),
    ("models.html", "Models", ["wiki/models.md"]),
    ("posting-plan.html", "Posting plan", ["wiki/posting-plan.md"]),
]
VIDEO_PAGES = [(f"{d}/RUNLOG.html", d, [f"{d}/RUNLOG.md"] + ([f"{d}/qc-report.md"] if os.path.isfile(f"{d}/qc-report.md") else [])) for d in VIDEO_DIRS]
SITE = "https://justinyang13.github.io/Project-V/"
MD2HTML = {"SPEC.md": "spec.html", "runbook.md": "runbook.html", "lessons.md": "lessons.html", "music.md": "music.html",
           "models.md": "models.html", "posting-plan.md": "posting-plan.html", "README.md": "index.html"}
CSS = open("wiki/html-src/style.css").read()
NAV = [("index.html", "Home")] + [(p[0], p[1]) for p in PAGES]

VIDEO_NAV = [(SITE, "Master docs")] + [(SITE + p[0], p[1]) for p in PAGES]

def shell(title, body, current, nav_items=None):
    nav = "".join(f'<a href="{h}"{" class=on" if h == current else ""}>{t}</a>' for h, t in (nav_items or NAV))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — Project-V</title><style>{CSS}</style></head><body>
<header class="top"><nav><span class="brand">Project-V</span>{nav}</nav></header><main>{body}</main>
<script>document.querySelectorAll('pre').forEach(function(p){{var b=document.createElement('button');b.className='copy';b.textContent='Copy';
b.onclick=function(){{navigator.clipboard&&navigator.clipboard.writeText(p.innerText.replace(/Copy$/,'').trim());b.textContent='Copied';setTimeout(function(){{b.textContent='Copy'}},1200)}};p.appendChild(b)}});</script>
</body></html>"""

def fix_links(h):
    def rep(m):
        href, rest = m.group(1), m.group(2)
        if href.startswith(("http://", "https://", "#", "mailto:")): return m.group(0)
        path, _, frag = href.partition("#")
        base = os.path.basename(path)
        if base in MD2HTML and path.endswith(".md"): return f'<a href="{MD2HTML[base]}{"#" + frag if frag else ""}"{rest}'
        while path.startswith("../"): path = path[3:]
        return f'<a href="{REPO}{path}"{rest}'
    h = re.sub(r'<a href="([^"]+)"([^>]*>)', rep, h)
    h = h.replace("[UNVERIFIED]", '<span class="badge unv">UNVERIFIED</span>').replace("**[UNVERIFIED]**", '<span class="badge unv">UNVERIFIED</span>')
    h = h.replace("[verified]", '<span class="badge ver">verified</span>')
    return h

md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists", "toc", "codehilite"], extension_configs={"codehilite": {"guess_lang": False, "noclasses": True, "pygments_style": "default"}})
os.makedirs("wiki/html", exist_ok=True)
def render(out, title, srcs, dest, nav_items=None):
    text = "\n\n---\n\n".join(open(s).read() for s in srcs)
    md.reset(); body = fix_links(md.convert(text))
    body = re.sub(r'<div class="codehilite"[^>]*>(<pre[^>]*>)', r'\1', body)  # plain <pre>, theme handled by CSS
    body = re.sub(r'</pre></div>', '</pre>', body)
    body = re.sub(r'<span style="[^"]*">', '<span>', body)
    open(dest, "w").write(shell(title, body, out, nav_items))
    print("wrote " + dest)
for out, title, srcs in PAGES: render(out, title, srcs, f"wiki/html/{out}")
for out, title, srcs in VIDEO_PAGES: render(out, title, srcs, out, VIDEO_NAV)
idx = open("wiki/html-src/index.body.html").read().replace("<!--VIDEOS-->", "")
open("wiki/html/index.html", "w").write(shell("Scene idea to 1-hour loop video", idx, "index.html"))
print("wrote wiki/html/index.html")
