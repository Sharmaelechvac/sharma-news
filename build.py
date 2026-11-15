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
:root{--paper:#f7f4ec;--paper2:#faf8f2;--ink:#111;--mut:#555;--accent:#1b365d;--hair:#c9c2b2}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);
font-family:Georgia,'Times New Roman',Times,serif;line-height:1.55}
a{color:var(--accent);text-decoration:underline;text-underline-offset:2px}
a:hover{color:#000}
/* ---------- masthead ---------- */
.masthead{max-width:1020px;margin:0 auto;padding:16px 18px 0;text-align:center}
.masthead img.logo{height:58px;width:auto}
.dbl{border-top:4px solid var(--ink);margin-top:10px}
.dbl::after{content:"";display:block;border-top:1px solid var(--ink);margin-top:2px}
.nameplate{font-family:'Playfair Display',Georgia,'Times New Roman',serif;font-weight:900;
font-size:58px;line-height:1.05;letter-spacing:.5px;margin:10px 0 2px}
.tagline{font-style:italic;color:#333;font-size:15.5px;margin:0 0 10px}
.dateline{display:flex;justify-content:space-between;gap:8px 18px;flex-wrap:wrap;
border-top:1px solid var(--ink);padding:6px 2px 7px;font-size:12.5px;
text-transform:uppercase;letter-spacing:1.4px}
nav.main{display:flex;justify-content:center;flex-wrap:wrap;border-top:1px solid var(--ink);
border-bottom:6px double var(--ink);padding:7px 0}
nav.main a{color:var(--ink);text-decoration:none;font-size:13px;font-weight:700;
letter-spacing:1.6px;text-transform:uppercase;padding:0 15px}
nav.main a + a{border-left:1px solid var(--hair)}
nav.main a:hover{text-decoration:underline}
.wrap{max-width:1020px;margin:0 auto;padding:6px 18px 54px}
/* ---------- front page ---------- */
.front{display:grid;grid-template-columns:1fr 1fr;margin-top:24px;
border-bottom:2px solid var(--ink);padding-bottom:24px}
.story{padding:0 24px}
.story:first-child{padding-left:0}
.story + .story{border-left:1px solid var(--hair);padding-right:0}
.kicker{font-size:12px;font-weight:700;letter-spacing:2.2px;text-transform:uppercase;color:var(--accent)}
.story .headline{font-family:'Playfair Display',Georgia,'Times New Roman',serif;font-weight:700;
font-size:26px;line-height:1.22;margin:8px 0 10px}
.byline{font-size:12.5px;text-transform:uppercase;letter-spacing:1px;color:#444;
border-top:1px solid var(--hair);border-bottom:1px solid var(--hair);padding:5px 0;margin:0 0 12px}
.cont{font-variant:small-caps;font-size:17px;font-weight:700;color:var(--ink)}
/* ---------- index / archive ---------- */
h2.sec{font-size:19px;font-weight:700;text-transform:uppercase;letter-spacing:1.6px;
border-bottom:2px solid var(--ink);padding-bottom:5px;margin:32px 0 2px}
.arch{list-style:none;margin:0;padding:0}
.arch li{border-bottom:1px solid var(--hair);padding:11px 0}
.arch li a{font-size:18px;font-weight:700;color:var(--ink);text-decoration:none}
.arch li a:hover{text-decoration:underline}
.arch .d{color:var(--mut);font-size:12.5px;font-weight:700;text-transform:uppercase;letter-spacing:1px}
.arch p{margin:3px 0 0;color:#333;font-size:15px}
/* ---------- article pages ---------- */
article{overflow-wrap:break-word;padding-top:6px}
article h1{font-family:'Playfair Display',Georgia,'Times New Roman',serif;font-size:30px;line-height:1.2;margin:10px 0 12px}
article h2{font-size:22px;margin-top:30px;border-bottom:1px solid var(--ink);padding-bottom:5px}
article h3{font-size:18.5px;margin-top:24px}
article a{word-break:break-word}
article table{border-collapse:collapse;width:100%;display:block;overflow-x:auto}
article th,article td{border:1px solid #999;padding:6px 9px;font-size:14px;text-align:left}
article th{background:#ece7da}
article code{background:#ece7da;padding:1px 5px;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.88em}
article blockquote{border-left:2px solid var(--ink);margin:14px 0;padding:2px 16px;color:#333;font-style:italic}
.crumb{color:var(--mut);font-size:12.5px;text-transform:uppercase;letter-spacing:1.2px;margin:16px 0 8px}
.crumb a{color:var(--ink)}
footer{max-width:1020px;margin:0 auto;padding:0 18px 30px;text-align:center}
footer .fin{border-top:6px double var(--ink);padding-top:12px;font-size:13px;color:#444}
@media(max-width:760px){
.nameplate{font-size:38px}
.front{grid-template-columns:1fr}
.story{padding:0}
.story + .story{border-left:none;border-top:1px solid var(--hair);margin-top:22px;padding-top:20px}
.story .headline{font-size:23px}
article h1{font-size:25px}
.dateline{justify-content:center;text-align:center}
}
"""

def shell(prefix, title, body, chip=""):
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{title} — The Sharma News</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&amp;display=swap" rel="stylesheet">
<style>{CSS}</style></head>
<body>
<header class="masthead">
<img class="logo" src="{prefix}logo.png" alt="Sharma Electric &amp; HVAC">
<div class="dbl"></div>
<div class="nameplate">The Sharma News</div>
<p class="tagline">The daily news hub for Sharma Electric &amp; HVAC</p>
<div class="dateline"><span>Orlando, Florida</span><span>Sunday, November 15, 2026</span><span>Updated daily at 5:00 AM ET</span></div>
<nav class="main">
<a href="{prefix}index.html">Front Page</a>
<a href="{LEGAL_BASE}/">Legal Briefing</a>
<a href="{prefix}finance/index.html">Finance Briefing</a>
<a href="{prefix}finance/archive/index.html">Finance Archive</a>
</nav></header>
<div class="wrap">{body}</div>
<footer><div class="fin">Sharma Electric &amp; HVAC — The Sharma News · Updated daily at 5:00 AM ET · General news summaries for the Sharma team — not legal or financial advice.</div></footer>
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
    body = f'<p class="crumb"><a href="../index.html">Finance Briefing</a> · <a href="index.html">Archive</a></p><article>{md_to_html(fin_report(date))}</article>'
    (DOCS/"finance"/"archive"/f"{date}.html").write_text(
        shell("../../", f"Finance Briefing — {label}", body), encoding="utf-8")

latest = "2026-11-15"
body = f'<p class="crumb"><span class="kicker">Finance Briefing · Latest Edition</span></p><article>{md_to_html(fin_report(latest))}</article>'
(DOCS/"finance"/"index.html").write_text(
    shell("../", f"Finance Briefing — {FIN[latest][1]}", body), encoding="utf-8")

items = "\n".join(
    f'<li><span class="d">{FIN[d][1]}</span><br><a href="{d}.html">Finance Briefing — {d}</a><p>{FIN[d][2]}</p></li>'
    for d in sorted(FIN, reverse=True))
body = f'<span class="kicker">Finance</span><h2 class="sec" style="margin-top:8px">Finance Briefing — Back Issues</h2><ul class="arch">{items}</ul>'
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
<div class="front">
<div class="story"><span class="kicker">Legal Briefing</span>
<h2 class="headline">{LEGAL['2026-11-15'][1]}</h2>
<p class="byline">Legal Briefing — Harvey, Legal Advisor · Edition of Nov 15, 2026</p>
<a class="cont" href="{LEGAL_BASE}/">Read today's legal briefing →</a></div>
<div class="story"><span class="kicker">Finance Briefing</span>
<h2 class="headline">{FIN['2026-11-15'][2]}</h2>
<p class="byline">Finance Briefing — Warren Buffett, CFO · Edition of Nov 15, 2026</p>
<a class="cont" href="finance/index.html">Read today's finance briefing →</a></div>
</div>
<h2 class="sec">Legal — Back Issues</h2><ul class="arch">{legal_arch}</ul>
<h2 class="sec">Finance — Back Issues</h2><ul class="arch">{fin_arch}</ul>
"""
(DOCS/"index.html").write_text(shell("", "Home — Sunday, November 15, 2026", body), encoding="utf-8")
print("built:", [str(p.relative_to(DOCS)) for p in sorted(DOCS.rglob('*.html'))])
