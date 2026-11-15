#!/usr/bin/env python3
"""Build the Sharma News static site (GitHub Pages, /docs) from the daily
finance briefing reports in ~/workspace/research_notes/. Legal briefings live
on the separate sharma-legal-briefing site; this hub links to them."""
import re, glob, markdown, pathlib

ROOT = pathlib.Path(__file__).parent
DOCS = ROOT / "docs"
NOTES = pathlib.Path.home() / "workspace" / "research_notes"
LEGAL_BASE = "https://sharmaelechvac.github.io/sharma-legal-briefing"

CSS = """
:root{--bg:#050a18;--bg2:#0a1230;--card:rgba(255,255,255,.055);--line:rgba(148,184,255,.18);
--txt:#e8eefc;--mut:#9fb0d8;--blue:#38bdf8;--vio:#a78bfa;--grad:linear-gradient(92deg,#38bdf8,#818cf8,#c084fc)}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;font-family:'Segoe UI',system-ui,-apple-system,Roboto,Helvetica,Arial,sans-serif;
background:radial-gradient(1100px 520px at 85% -10%,rgba(129,140,248,.22),transparent 60%),
radial-gradient(900px 480px at -10% 0%,rgba(56,189,248,.16),transparent 55%),var(--bg);color:var(--txt);line-height:1.62}
a{color:var(--blue);text-decoration:none}a:hover{text-decoration:underline}
header.top{position:sticky;top:0;z-index:20;backdrop-filter:blur(14px);background:rgba(5,10,24,.82);
border-bottom:1px solid var(--line)}
.topin{max-width:1080px;margin:0 auto;padding:10px 18px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.topin img.logo{height:54px;width:auto;background:#fff;border-radius:10px;padding:5px 8px;box-shadow:0 0 22px rgba(56,189,248,.35)}
.brand{font-size:24px;font-weight:800;letter-spacing:.4px;background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
nav.main{margin-left:auto;display:flex;gap:8px;flex-wrap:wrap}
nav.main a{color:var(--txt);font-size:14px;font-weight:600;padding:7px 13px;border:1px solid var(--line);border-radius:999px;background:var(--card)}
nav.main a:hover{border-color:var(--blue);text-decoration:none;box-shadow:0 0 14px rgba(56,189,248,.35)}
.wrap{max-width:1080px;margin:0 auto;padding:26px 18px 60px}
.hero{text-align:center;padding:30px 10px 8px}
.hero h1{font-size:42px;margin:0 0 6px;font-weight:900}
.hero h1 .g{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero .date{color:var(--mut);font-size:17px}
.hero .note{display:inline-block;margin-top:14px;padding:8px 18px;border-radius:999px;border:1px solid var(--line);
background:var(--card);font-weight:700;color:#cfe0ff;box-shadow:0 0 18px rgba(129,140,248,.25)}
.chip{display:inline-block;font-size:12.5px;font-weight:800;letter-spacing:.6px;text-transform:uppercase;
padding:4px 12px;border-radius:999px;border:1px solid var(--line);background:rgba(56,189,248,.12);color:#bfe3ff}
.chip.fin{background:rgba(167,139,250,.14);color:#e2d6ff}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:26px}
@media(max-width:760px){.grid{grid-template-columns:1fr}.hero h1{font-size:32px}}
.card{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:24px;
box-shadow:0 10px 34px rgba(0,0,0,.35),inset 0 1px 0 rgba(255,255,255,.06)}
.card h2{margin:10px 0 8px;font-size:24px}
.card p{color:#d5def5}
.btn{display:inline-block;margin-top:12px;padding:11px 22px;border-radius:12px;font-weight:800;color:#04122b;
background:var(--grad);box-shadow:0 0 20px rgba(56,189,248,.45)}
.btn:hover{text-decoration:none;filter:brightness(1.1)}
h2.sec{margin:38px 0 6px;font-size:21px}
.arch{list-style:none;margin:10px 0 0;padding:0}
.arch li{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:13px 17px;margin:0 0 10px}
.arch li a{font-weight:700}
.arch .d{color:var(--mut);font-size:13.5px;font-weight:700;text-transform:uppercase;letter-spacing:.5px}
.arch p{margin:4px 0 0;color:#d5def5;font-size:15px}
article{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:28px 30px;
box-shadow:0 10px 34px rgba(0,0,0,.35);overflow-wrap:break-word}
article h1{font-size:29px;line-height:1.25}article h2{font-size:23px;margin-top:30px;border-bottom:1px solid var(--line);padding-bottom:6px}
article h3{font-size:19px;margin-top:24px}article a{word-break:break-word}
article table{border-collapse:collapse;width:100%;display:block;overflow-x:auto}
article th,article td{border:1px solid var(--line);padding:7px 10px;font-size:14.5px;text-align:left}
article code{background:rgba(56,189,248,.13);padding:1px 6px;border-radius:6px}
article blockquote{border-left:3px solid var(--vio);margin:14px 0;padding:4px 16px;color:#d5def5}
.crumb{color:var(--mut);font-size:14px;margin-bottom:14px}
footer{border-top:1px solid var(--line);color:var(--mut);text-align:center;padding:22px 16px 30px;font-size:14px}
"""

def shell(prefix, title, body, chip=""):
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{title} — Sharma News</title><style>{CSS}</style></head>
<body>
<header class="top"><div class="topin">
<img class="logo" src="{prefix}logo.png" alt="Sharma Electric &amp; HVAC">
<span class="brand">SHARMA NEWS</span>
<nav class="main">
<a href="{prefix}index.html">Home</a>
<a href="{LEGAL_BASE}/">⚖️ Legal Briefing</a>
<a href="{prefix}finance/index.html">📈 Finance Briefing</a>
<a href="{prefix}finance/archive/index.html">Finance Archive</a>
</nav></div></header>
<div class="wrap">{body}</div>
<footer>Sharma Electric &amp; HVAC — Sharma News · Updated daily at 5:00 AM ET · General news summaries for the Sharma team — not legal or financial advice.</footer>
</body></html>"""

def md_to_html(md_text):
    html = markdown.markdown(md_text, extensions=["extra", "sane_lists"])
    # linkify bare URLs not already inside href/anchor text
    def repl(m):
        url = m.group(1)
        return f'<a href="{url}" target="_blank" rel="noopener">{url}</a>'
    html = re.sub(r'(?<![=">])(https?://[^\s<\)\]]*[^\s<\)\]\.,;:])', repl, html)
    return html

FIN = {  # date -> (report glob, weekday label, archive one-liner)
 "2026-11-11": ("sharma-daily-finance-news-2026-11-11-*", "Wednesday, November 11, 2026",
   "Hot October CPI (+0.4% headline, +0.3% core) killed the four-week mortgage-rate slide, put a December Fed hike — possibly 50 bp — on the table, and pushed the 10-year Treasury to ~5%. Copper stayed historically high and physically tight."),
 "2026-11-12": ("sharma-daily-finance-news-2026-11-12-*", "Thursday, November 12, 2026",
   "The hot CPI drove an in-window repricing: a December Fed hike became fully priced, the daily 30-year mortgage rate jumped 12 bp to 7.30%, and homebuilder shares fell. Copper settled modestly higher after a sharp fortnight's fall."),
 "2026-11-13": ("sharma-daily-finance-news-2026-11-13-*", "Friday, November 13, 2026",
   "A December Fed hike became a near-certainty and the daily 30-year rate rose to 7.42% while Freddie Mac's weekly average fell to 7.11%; NAR October existing-home sales hit a 16-year low at 3.75M SAAR; every major builder Sharma works with fell."),
 "2026-11-14": ("sharma-daily-finance-news-2026-11-14-*", "Saturday, November 14, 2026",
   "A rates-and-inflation day: the 30-year fixed jumped to 7.50%, October PPI rose 6.5% year-over-year, three Fed presidents spoke hawkishly, and copper fell to $6.0795/lb — a fifth straight down week."),
 "2026-11-15": ("sharma-daily-finance-news-2026-11-15-*", "Sunday, November 15, 2026",
   "A genuinely quiet weekend: copper at $6.08/lb with LME copper breaking toward $13,430/t, its lowest since July; US–China talks on a “$30 billion-for-$30 billion” tariff-cut arrangement — no agreement announced; Boston Fed President Collins backed a “steady, gradual path” of rate hikes, with a December 8–9 quarter-point hike widely expected."),
}
LEGAL = {  # date -> (weekday label, biggest-story one-liner for hub cards/lists)
 "2026-11-12": ("Thursday, November 12, 2026",
   "Biggest: the Bankruptcy Threshold Adjustment Act (signed Tue Nov 10) permanently raises the Subchapter V debt limit to $7.5M — plus a time-sensitive OSHA HazCom deadline Fri Nov 20, 2026."),
 "2026-11-13": ("Friday, November 13, 2026",
   "Biggest: SCOTUS grants review in Mullin v. RAICES on the asylum-shutdown proclamation; also the $183.5M Acima settlement (Florida a party) and the FTC suit to block the $3.5B Covetrus–MWI merger."),
 "2026-11-14": ("Saturday, November 14, 2026",
   "Biggest: the FAA nationwide ground stop (Fri Nov 13); the 11th Circuit upholds the CFPB PACE-loan rule; Johnson Controls pays $5M in an FCA cyber-compliance settlement."),
 "2026-11-15": ("Sunday, November 15, 2026",
   "Biggest story: Judge Ana Reyes's Saturday, Nov 14 TRO halting the East Potomac Park / golf-course closure and redevelopment in Washington, D.C. — the only major ruling actually issued in the core weekend window, with a same-weekend presidential promise to appeal."),
}

def fin_report(date):
    pat = FIN[date][0]
    p = sorted(NOTES.glob(pat + "/report.md"))[0]
    return p.read_text(encoding="utf-8", errors="replace")

# ---- finance archive pages + latest ----
for date,(pat,label,one) in FIN.items():
    body = f'<p class="crumb"><a href="../index.html">📈 Finance Briefing</a> · <a href="index.html">Archive</a></p><article>{md_to_html(fin_report(date))}</article>'
    (DOCS/"finance"/"archive"/f"{date}.html").write_text(
        shell("../../", f"Finance Briefing — {label}", body), encoding="utf-8")

latest = "2026-11-15"
body = f'<p class="crumb"><span class="chip fin">📈 Finance · Latest edition</span></p><article>{md_to_html(fin_report(latest))}</article>'
(DOCS/"finance"/"index.html").write_text(
    shell("../", f"Finance Briefing — {FIN[latest][1]}", body), encoding="utf-8")

items = "\n".join(
    f'<li><span class="d">{FIN[d][1]}</span><br><a href="{d}.html">Finance Briefing — {d}</a><p>{FIN[d][2]}</p></li>'
    for d in sorted(FIN, reverse=True))
body = f'<span class="chip fin">📈 Finance</span><h2 class="sec" style="margin-top:14px">Finance Briefing Archive</h2><ul class="arch">{items}</ul>'
(DOCS/"finance"/"archive"/"index.html").write_text(
    shell("../../", "Finance Briefing Archive", body), encoding="utf-8")

# ---- home ----
legal_arch = "\n".join(
    f'<li><span class="d">{LEGAL[d][0]}</span><br><a href="{LEGAL_BASE}/archive/{d}.html">Legal Briefing — {d}</a><p>{LEGAL[d][1]}</p></li>'
    for d in sorted(LEGAL, reverse=True))
fin_arch = "\n".join(
    f'<li><span class="d">{FIN[d][1]}</span><br><a href="finance/archive/{d}.html">Finance Briefing — {d}</a><p>{FIN[d][2]}</p></li>'
    for d in sorted(FIN, reverse=True))
body = f"""
<div class="hero"><h1>Sharma <span class="g">News</span></h1>
<div class="date">Sunday, November 15, 2026 · The daily news hub for Sharma Electric &amp; HVAC</div><br>
<span class="note">Updated daily at 5:00 AM ET.</span></div>
<div class="grid">
<div class="card"><span class="chip">⚖️ Legal</span>
<h2>Legal Briefing — Nov 15, 2026</h2><p>{LEGAL['2026-11-15'][1]}</p>
<a class="btn" href="{LEGAL_BASE}/">Read today's legal briefing →</a></div>
<div class="card"><span class="chip fin">📈 Finance</span>
<h2>Finance Briefing — Nov 15, 2026</h2><p>{FIN['2026-11-15'][2]}</p>
<a class="btn" href="finance/index.html">Read today's finance briefing →</a></div>
</div>
<h2 class="sec">⚖️ Legal archive</h2><ul class="arch">{legal_arch}</ul>
<h2 class="sec">📈 Finance archive</h2><ul class="arch">{fin_arch}</ul>
"""
(DOCS/"index.html").write_text(shell("", "Home — Sunday, November 15, 2026", body), encoding="utf-8")
print("built:", [str(p.relative_to(DOCS)) for p in sorted(DOCS.rglob('*.html'))])
