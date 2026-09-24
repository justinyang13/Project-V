"""Build self-contained HTML docs (docs/*.html) from the markdown sources. Run after any doc change:
python scripts/build_docs.py
Sources: SPEC.md, wiki/*.md, wiki/runs/001-snow-tea.md (+ qc report), docs-src/{style.css,index.body.html}.
Each page is a single file (CSS inlined, no network needed). Links to repo files that aren't pages point to GitHub."""
import os, re, html
import markdown

REPO = "https://github.com/justinyang13/Video-Zen1/blob/main/"
PAGES = [  # (output file, title, source md files joined in order)
    ("spec.html", "Spec", ["SPEC.md"]),
    ("runbook.html", "Runbook", ["wiki/runbook.md"]),
    ("lessons.html", "Lessons", ["wiki/lessons.md"]),
    ("music.html", "Music", ["wiki/music.md"]),
    ("models.html", "Models", ["wiki/models.md"]),
    ("posting-plan.html", "Posting plan", ["wiki/posting-plan.md"]),
    ("job-001.html", "Job 001 log", ["wiki/runs/001-snow-tea.md", "wiki/runs/001-snow-tea-qc-report.md"]),
]
MD2HTML = {"SPEC.md": "spec.html", "runbook.md": "runbook.html", "lessons.md": "lessons.html", "music.md": "music.html",
           "models.md": "models.html", "posting-plan.md": "posting-plan.html", "001-snow-tea.md": "job-001.html", "README.md": "index.html"}
CSS = open("docs-src/style.css").read()
NAV = [("index.html", "Home")] + [(p[0], p[1]) for p in PAGES]

def shell(title, body, current):
    nav = "".join(f'<a href="{h}"{" class=on" if h == current else ""}>{t}</a>' for h, t in NAV)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — Video-Zen1</title><style>{CSS}</style></head><body>
<header class="top"><nav><span class="brand">Video-Zen1</span>{nav}</nav></header><main>{body}</main>
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
        if path.startswith("../"): path = path[3:]
        return f'<a href="{REPO}{path}"{rest}'
    h = re.sub(r'<a href="([^"]+)"([^>]*>)', rep, h)
    h = h.replace("[UNVERIFIED]", '<span class="badge unv">UNVERIFIED</span>').replace("**[UNVERIFIED]**", '<span class="badge unv">UNVERIFIED</span>')
    h = h.replace("[verified]", '<span class="badge ver">verified</span>')
    return h

md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists", "toc", "codehilite"], extension_configs={"codehilite": {"guess_lang": False, "noclasses": True, "pygments_style": "default"}})
os.makedirs("docs", exist_ok=True)
for out, title, srcs in PAGES:
    text = "\n\n---\n\n".join(open(s).read() for s in srcs)
    md.reset(); body = fix_links(md.convert(text))
    body = re.sub(r'<div class="codehilite"[^>]*>(<pre[^>]*>)', r'\1', body)  # plain <pre>, theme handled by CSS
    body = re.sub(r'</pre></div>', '</pre>', body)
    body = re.sub(r'<span style="[^"]*">', '<span>', body)
    open(f"docs/{out}", "w").write(shell(title, body, out))
    print("wrote docs/" + out)
open("docs/index.html", "w").write(shell("Image to 1-hour loop video", open("docs-src/index.body.html").read(), "index.html"))
print("wrote docs/index.html")
