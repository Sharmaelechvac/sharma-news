"""Re-wrap every existing docs/*.html page with build.py's current CSS + shell(),
keeping each page's body (content, links, images) byte-for-byte except emoji."""
import re, pathlib, sys, html as ihtml
root = pathlib.Path(sys.argv[1]); src = (root/"build.py").read_text()
a = src.index('CSS = """'); b = src.index('def md_to_html')
ns = {"re": re, "LEGAL_BASE": "https://sharmaelechvac.github.io/sharma-legal-briefing"}
exec(src[a:b], ns)
n = 0
for p in sorted((root/"docs").rglob("*.html")):
    t = p.read_text(encoding="utf-8")
    title = re.search(r"<title>(.*?) — (?:The )?Sharma News</title>", t, re.S).group(1)
    prefix = re.search(r'<img class="logo" src="([^"]*)logo\.png"', t).group(1)
    i = t.index('<div class="wrap">') + len('<div class="wrap">')
    j = t.rindex('</div>\n<footer>')
    body = t[i:j]
    p.write_text(ns["shell"](prefix, title, body), encoding="utf-8"); n += 1
print("rewrapped", n)
