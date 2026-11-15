#!/usr/bin/env python3
"""Build the Sharma News static site (GitHub Pages, /docs) from the daily
finance briefing reports in ~/workspace/research_notes/. Legal briefings live
on the separate sharma-legal-briefing site; this hub links to them.

Photos: each edition's pictures come FROM the cited source articles
themselves (the article's lead / og:image, downloaded into docs/img/) —
see IMAGES below, keyed by date + slot ("lead" / "inline"). Editions or
slots with no IMAGES entry render with no <img> at all. Captions credit
the source publication, as Sanjay directed ("pull photos from the
articles you are citing").

Layout: newspaper style. Every finance edition page opens with an
"At a Glance" box + "Key Numbers" strip (both taken only from that
report's own summary), then each story shows headline + deck + Sharma
impact line with the FULL original text folded inside a native
<details> ("Read the full story") — nothing is deleted."""
import re, glob, html as ihtml, markdown, pathlib

ROOT = pathlib.Path(__file__).parent
DOCS = ROOT / "docs"
IMG = DOCS / "img"
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
letter-spacing:1.6px;text-transform:uppercase;padding:10px 15px}
nav.main a + a{border-left:1px solid var(--hair)}
nav.main a:hover{text-decoration:underline}
.wrap{max-width:1020px;margin:0 auto;padding:6px 18px 54px}
/* ---------- photos (newspaper style) ---------- */
.photo{margin:12px 0 16px}
.photo img{width:100%;height:auto;display:block;background:#fff;border:1px solid var(--ink);
padding:3px;filter:grayscale(92%) contrast(1.06)}
.photo figcaption{font-style:italic;font-size:13.5px;color:#222;margin-top:6px;line-height:1.45}
.photo .credit{display:block;font-style:normal;font-variant:small-caps;font-size:11.5px;
letter-spacing:.8px;color:var(--mut);margin-top:2px}
.photo.small{max-width:430px}
.story .photo img{max-height:290px;object-fit:cover;object-position:top}
/* ---------- at a glance / key numbers ---------- */
.glance{background:var(--paper2);border:1px solid var(--ink);border-top:4px solid var(--ink);
padding:14px 18px 8px;margin:20px 0 18px}
.glance h2{font-size:15px;text-transform:uppercase;letter-spacing:2px;margin:0 0 8px;
border:none;padding:0}
.glance ul{margin:0 0 8px;padding-left:20px}
.glance li{margin:5px 0;font-size:15.5px}
.keynums{display:flex;flex-wrap:wrap;border:1px solid var(--ink);background:var(--paper2);margin:0 0 20px}
.kn{flex:1 1 138px;padding:9px 12px;border-right:1px solid var(--hair)}
.kn:last-child{border-right:none}
.kn b{display:block;font-size:19px;line-height:1.2}
.kn span{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--mut)}
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
.cont{font-variant:small-caps;font-size:17px;font-weight:700;color:var(--ink);
display:inline-block;padding:10px 6px 10px 0}
/* ---------- index / archive ---------- */
h2.sec{font-size:19px;font-weight:700;text-transform:uppercase;letter-spacing:1.6px;
border-bottom:2px solid var(--ink);padding-bottom:5px;margin:32px 0 2px}
.arch{list-style:none;margin:0;padding:0}
.arch li{border-bottom:1px solid var(--hair);padding:11px 0;overflow:hidden}
.arch li a{font-size:18px;font-weight:700;color:var(--ink);text-decoration:none}
.arch li a:hover{text-decoration:underline}
.arch .d{color:var(--mut);font-size:12.5px;font-weight:700;text-transform:uppercase;letter-spacing:1px}
.arch p{margin:3px 0 0;color:#333;font-size:15px}
.arch img.thumb{width:112px;height:76px;object-fit:cover;float:left;margin:3px 14px 6px 0;
background:#fff;border:1px solid var(--ink);padding:2px;filter:grayscale(92%) contrast(1.06)}
/* ---------- article pages ---------- */
article{overflow-wrap:break-word;padding-top:6px;max-width:68ch;margin:0 auto}
article h1{font-family:'Playfair Display',Georgia,'Times New Roman',serif;font-size:30px;line-height:1.2;margin:10px 0 12px}
article h2{font-size:22px;margin-top:30px;border-bottom:1px solid var(--ink);padding-bottom:5px}
article h3{font-size:18.5px;margin-top:24px}
article a{word-break:break-word}
article table{border-collapse:collapse;width:100%;display:block;overflow-x:auto}
article th,article td{border:1px solid #999;padding:6px 9px;font-size:14px;text-align:left}
article th{background:#ece7da}
article code{background:#ece7da;padding:1px 5px;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.88em}
article blockquote{border-left:2px solid var(--ink);margin:14px 0;padding:2px 16px;color:#333;font-style:italic}
.windowline{font-variant:small-caps;font-size:16px;color:#333;border-bottom:1px solid var(--hair);padding-bottom:8px}
.jump{position:sticky;top:0;z-index:6;background:var(--paper);border-bottom:2px solid var(--ink);
display:flex;flex-wrap:wrap;gap:2px 16px;padding:8px 0;margin:0 0 6px}
.jump a{color:var(--ink);text-decoration:none;font-size:12.5px;font-weight:700;
text-transform:uppercase;letter-spacing:1.1px;padding:9px 2px}
.jump a:hover{text-decoration:underline}
.item{border-bottom:1px solid var(--hair);padding:12px 0 14px}
.item .item-head{font-family:'Playfair Display',Georgia,'Times New Roman',serif;
font-size:20px;line-height:1.3;margin:2px 0 6px}
.item .deck{margin:0 0 6px;color:#222;font-size:15.5px}
.item .impact{margin:0 0 4px;font-size:15.5px}
.item .impact b{font-variant:small-caps;letter-spacing:.4px}
details.full{margin-top:6px}
details.full summary{cursor:pointer;font-variant:small-caps;font-size:16.5px;font-weight:700;
color:var(--accent);padding:11px 0;min-height:24px}
details.full summary:hover{color:#000}
details.full .fullbody{border-top:1px dotted var(--hair);padding-top:4px}
.sec-intro{color:#222}
.totop{text-align:right;margin-top:26px}
.totop a{font-variant:small-caps;font-weight:700;color:var(--ink);padding:10px 0;display:inline-block}
.secname{font-size:14px;font-weight:700;letter-spacing:2.4px;text-transform:uppercase;color:var(--accent);
border-top:2px solid var(--ink);border-bottom:1px solid var(--ink);padding:8px 0;text-align:center;margin:14px 0 4px}
.spotlight{border:2px solid var(--ink);background:var(--paper2);padding:16px 20px 10px;margin:0 0 22px}
.spotlight .item-head{font-family:'Playfair Display',Georgia,'Times New Roman',serif;font-size:23px;line-height:1.3;margin:2px 0 6px}
.spotlight .makerline{font-variant:small-caps;font-size:15.5px;color:#333;border-bottom:1px solid var(--hair);padding-bottom:7px;margin:0 0 10px}
.spotlight .photo{max-width:520px}
.spotlight .deck{font-size:16px;color:#222;margin:0 0 6px}
.techfeature{border-bottom:2px solid var(--ink);padding:22px 0 24px}
.techfeature .photo{max-width:640px}
.techfeature .headline{font-family:'Playfair Display',Georgia,'Times New Roman',serif;font-weight:700;
font-size:26px;line-height:1.22;margin:8px 0 10px}
.spotline{font-size:16.5px;margin:0 0 10px}
.crumb{color:var(--mut);font-size:12.5px;text-transform:uppercase;letter-spacing:1.2px;margin:16px 0 8px}
.crumb a{color:var(--ink);padding:6px 0;display:inline-block}
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
.kn{flex:1 1 45%}
.photo.small{max-width:none}
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
<body id="top">
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
<a href="{prefix}tech/index.html">Tech Briefing</a>
<a href="{prefix}tech/archive/index.html">Tech Archive</a>
</nav></header>
<div class="wrap">{body}</div>
<footer><div class="fin">Sharma Electric &amp; HVAC — The Sharma News · Updated daily at 5:00 AM ET · General news summaries for the Sharma team — not legal or financial advice.</div></footer>
</body></html>"""

def md_to_html(md_text):
    html = markdown.markdown(md_text, extensions=["extra", "sane_lists"])
    def repl(m):
        url = m.group(1)
        return f'<a href="{url}" target="_blank" rel="noopener">{url}</a>'
    html = re.sub(r'(?<![=">])(https?://[^\s<\)\]]*[^\s<\)\]\.,;:])', repl, html)
    return html

# ---------- photos: pulled from the cited articles themselves ----------
# slot -> (file in docs/img/, alt, caption, credit). File must exist on
# disk or the slot renders empty — never a broken <img>.
IMAGES = {
 "home": {
  "legal": ("home-legal.jpg", "Fencing at East Potomac Park, Washington, D.C.",
    "Fencing at East Potomac Park in Washington, D.C. — the public golf course whose closure for redevelopment a federal judge halted on Saturday.",
    "Photo: Reuters"),
  "finance": ("2026-11-15-lead.jpg", "Copper market update graphic, November 14, 2026",
    "Copper eased to $6.05–6.08/lb at Friday's close, in the copper-market update the finance briefing cites.",
    "Photo: So OK Trading"),
 },
 "2026-11-11": {
  "lead": ("2026-11-11-lead.jpg", "Federal Reserve Governor Christopher Waller",
    "Fed Governor Christopher Waller, whose October-CPI trigger for a bigger December hike was met by the print.",
    "Photo: Reuters"),
  "inline": ("2026-11-11-inline.jpg", "Copper market",
    "Copper stayed near record levels, with China's import premium at record highs and nearby supply tight.",
    "Photo: Devdiscourse"),
 },
 "2026-11-12": {
  "lead": ("2026-11-12-lead.png", "Commodities wrap graphic, November 11, 2026",
    "The Nov 11 commodities wrap: copper settled higher on the day after a sharp fortnight's fall.",
    "Photo: The Edge"),
  "inline": ("2026-11-12-inline.jpg", "Local housing markets chart, November 2026",
    "A second look at local housing markets in November, from the housing coverage the briefing cites.",
    "Photo: Calculated Risk"),
 },
 "2026-11-13": {
  "lead": ("2026-11-13-lead.jpg", "A home for sale",
    "Existing-home sales fell 5.5% in October to 3.75 million a year — a 16-year low.",
    "Photo: Real Estate News"),
  "inline": ("2026-11-13-inline.jpg", "Copper",
    "Copper hit a four-month low on Nov 12, settling at $6.1825/lb on COMEX.",
    "Photo: Mining.com"),
 },
 "2026-11-14": {
  "lead": ("2026-11-14-lead.jpg", "Mortgage rates chart, November 13, 2026",
    "Mortgage rates jumped to 7.50% on Nov 13 — up 0.32 in three days.",
    "Photo: Mortgage News Daily"),
  "inline": ("2026-11-14-inline.jpg", "Construction materials",
    "Producer prices: construction materials and components are up 6.2% year-over-year.",
    "Photo: United States Real Estate Investor"),
 },
 "2026-11-15": {
  "lead": ("2026-11-15-lead.jpg", "Copper market update graphic, November 14, 2026",
    "Copper market update, Nov 14: COMEX at $6.05–6.08/lb and LME copper at its lowest since July.",
    "Photo: So OK Trading"),
  "inline": ("2026-11-15-inline.jpg", "U.S.–China trade",
    "The U.S. and China held their first trade-council meeting ahead of the Trump–Xi talks, discussing a “$30 billion-for-$30 billion” tariff-cut arrangement.",
    "Photo: Reuters"),
 },
}

def photo_html(entry, prefix, cls=""):
    if not entry:
        return ""
    fname, alt, caption, credit = entry
    if not (IMG / fname).exists():
        return ""
    return (f'<figure class="photo {cls}"><img src="{prefix}img/{fname}" alt="{alt}" loading="lazy">'
            f'<figcaption>{caption}<span class="credit">{credit}</span></figcaption></figure>')

# ---------- at-a-glance + key numbers (from each report's own summary) ----------
FIN_GLANCE = {
 "2026-11-11": [
   "October CPI came in hot: +0.4% headline, +0.3% core — a third straight +0.3% core print.",
   "A December Fed hike — possibly 50 bp — is on the table; the 10-year Treasury pushed to ~5%.",
   "Mortgage rates jumped 12 bp in one day to 7.30%, ending four weeks of easing.",
   "Copper stayed historically high and physically tight; Comex settled +0.88% at $6.2745/lb.",
   "No material news on HVAC / R-454B / tariffs, CES or World Electric, or builder slowdowns, layoffs or defaults."],
 "2026-11-12": [
   "A December Fed hike became fully priced after the hot October CPI.",
   "The daily 30-year mortgage rate jumped 12 bp to 7.30%, and homebuilder shares fell.",
   "COMEX copper settled +0.88% at $6.2745/lb after a sharp fortnight's fall.",
   "NAR October existing-home sales were not yet out — due 10:00 AM ET Nov 12, consensus 3.8–3.87M SAAR.",
   "No material news for CES / World Electric, R-454B, housing starts, or builder layoffs/defaults."],
 "2026-11-13": [
   "A December Fed hike became a near-certainty (CME FedWatch 100%); the daily 30-year rate rose to 7.42% while Freddie Mac's weekly average fell to 7.11%.",
   "NAR October existing-home sales hit a 16-year low: 3.75M SAAR, −5.5% month-over-month.",
   "Every major builder Sharma works with fell on Nov 12, led by Dream Finders (−8.17%).",
   "Copper settled −1.47% at $6.1825/lb — lowest since July 8, still +21.5% vs a year ago.",
   "No HVAC / R-454B, small-business credit, insurance or tax news inside the window."],
 "2026-11-14": [
   "The 30-year fixed mortgage rate jumped to 7.50% (+0.32 in 3 days).",
   "October PPI rose 6.5% year-over-year; construction materials are up 6.2% year-over-year.",
   "Three Fed presidents spoke hawkishly on Nov 13; markets priced a December hike as a certainty.",
   "Treasury yields closed the week at 2-year 4.88% / 10-year 5.15%.",
   "Copper settled $6.0795/lb — a fifth straight down week, still +20.40% year-over-year."],
 "2026-11-15": [
   "Copper fell 1.67% to $6.08/lb; LME copper broke toward $13,430/t, its lowest since July.",
   "US–China talks on a “$30 billion-for-$30 billion” tariff-cut arrangement — no agreement announced.",
   "Boston Fed President Collins backed a “steady, gradual path” of rate hikes; a Dec 8–9 quarter-point hike is widely expected.",
   "No new housing-starts/permits/sales data, no builder operating announcements, and no HVAC or R-454B news in the window."],
}
FIN_NUMBERS = {
 "2026-11-11": [("CPI (Oct, m/m)", "+0.4%"), ("Core CPI (m/m)", "+0.3%"),
   ("Policy rate", "3.75%–4.00%"), ("30-yr fixed", "7.30%"),
   ("10-yr Treasury", "4.99%"), ("COMEX copper", "$6.2745/lb")],
 "2026-11-12": [("COMEX copper", "$6.2745/lb"), ("Dec copper", "$6.2900/lb"),
   ("LME copper", "$13,992/t"), ("LME stocks", "316,625 t"), ("30-yr fixed", "7.30%")],
 "2026-11-13": [("Daily 30-yr fixed", "7.42%"), ("Freddie Mac weekly", "7.11%"),
   ("Existing-home sales", "3.75M SAAR"), ("Median price", "$416,700"),
   ("COMEX copper", "$6.1825/lb"), ("Dec hike odds", "100%")],
 "2026-11-14": [("30-yr fixed", "7.50%"), ("PPI (y/y)", "+6.5%"),
   ("Constr. materials (y/y)", "+6.2%"), ("10-yr Treasury", "5.15%"),
   ("2-yr Treasury", "4.88%"), ("COMEX copper", "$6.0795/lb")],
 "2026-11-15": [("Copper", "$6.08/lb"), ("LME copper", "~$13,430/t"),
   ("Tariff talks", "$30B-for-$30B"), ("Next Fed meeting", "Dec 8–9")],
}
HOME_GLANCE = [
 "Legal — biggest story: Judge Ana Reyes's Saturday, Nov 14 TRO halting the East Potomac Park / golf-course closure and redevelopment in Washington, D.C.",
 "Legal — most useful Florida item: Koppert v. Homeowners Choice (2d DCA, Nov 13) — an arbitration decision emailed as a QuickBooks invoice attachment was not “served,” so the 20-day trial clock never ran.",
 "Finance — copper at $6.08/lb, with LME copper breaking toward $13,430/t, its lowest since July.",
 "Finance — US–China talks on a “$30 billion-for-$30 billion” tariff-cut arrangement; no agreement announced.",
 "Finance — Boston Fed President Collins backed a “steady, gradual path” of rate hikes, with a December 8–9 quarter-point hike widely expected."]

def glance_html(bullets):
    lis = "\n".join(f"<li>{b}</li>" for b in bullets)
    return f'<div class="glance" id="glance"><h2>At a Glance</h2><ul>{lis}</ul></div>'

def keynums_html(pairs):
    cells = "".join(f'<div class="kn"><b>{v}</b><span>{k}</span></div>' for k, v in pairs)
    return f'<div class="keynums">{cells}</div>'

# ---------- article renderer: headline + deck + impact, full text folded ----------
def strip_tags(s):
    return re.sub(r"\s+", " ", ihtml.unescape(re.sub(r"<[^>]+>", " ", s))).strip()

def excerpt(text, n):
    t = re.sub(r"\s+", " ", text).strip()
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"

def item_deck(block, headline):
    text = strip_tags(block)
    if headline and text.startswith(headline):
        text = text[len(headline):].lstrip(" —–-:")
    m = re.search(r"Key (?:numbers|figures):\s*(.*?)(?=\s*(?:Publication date|Published|Source|Why it matters)\b|$)", text, re.S)
    if m:
        return excerpt(m.group(1), 230)
    return excerpt(text, 230)

def item_impact(block):
    m = re.search(r"(?:Why it matters to Sharma|Sharma impact):\s*(.*)", strip_tags(block), re.S)
    return excerpt(m.group(1), 260) if m else ""

ITEM_SPLIT = r'(<h3>.*?</h3>|<p><strong>Item\s+\d+[A-Z]?\s*—.*?</strong></p>)'

def render_section_body(body):
    parts = re.split(ITEM_SPLIT, body, flags=re.S)
    intro, items = parts[0], []
    for i in range(1, len(parts), 2):
        marker = parts[i]
        rest = parts[i + 1] if i + 1 < len(parts) else ""
        items.append((marker, marker + rest))
    if not items:
        if len(strip_tags(body)) > 700:
            deck = excerpt(strip_tags(body), 230)
            return (f'<div class="item"><p class="deck">{deck}</p>'
                    f'<details class="full"><summary>Read this section in full</summary>'
                    f'<div class="fullbody">{body}</div></details></div>')
        return body
    out = []
    if strip_tags(intro):
        out.append(f'<div class="sec-intro">{intro}</div>')
    for marker, block in items:
        headline = strip_tags(marker)
        deck = item_deck(block, headline)
        impact = item_impact(block)
        imp = f'<p class="impact"><b>Why it matters to Sharma:</b> {impact}</p>' if impact else ""
        out.append(
            f'<div class="item"><h3 class="item-head">{headline}</h3>'
            f'<p class="deck">{deck}</p>{imp}'
            f'<details class="full"><summary>Read the full story</summary>'
            f'<div class="fullbody">{block}</div></details></div>')
    return "\n".join(out)

def render_article(md_text, date, prefix):
    raw = md_to_html(md_text)
    chunks = re.split(r'(<h2>.*?</h2>)', raw, flags=re.S)
    preamble = chunks[0]
    sections = []
    for i in range(1, len(chunks), 2):
        sections.append((chunks[i], chunks[i + 1] if i + 1 < len(chunks) else ""))
    imgs = IMAGES.get(date, {})
    nav_items, rendered = [], []
    sec_no = 0
    inline_placed = False
    for idx, (heading, body) in enumerate(sections):
        title = strip_tags(heading)
        if not strip_tags(body):
            rendered.append(f'<p class="windowline">{title}</p>')
            continue
        sec_no += 1
        sid = f"sec-{sec_no}"
        nav_items.append(f'<a href="#{sid}">{title}</a>')
        rendered.append(f'<h2 id="{sid}">{title}</h2>' + render_section_body(body))
        if not inline_placed and imgs.get("inline"):
            rendered.append(photo_html(imgs["inline"], prefix, "small"))
            inline_placed = True
    nav = ""
    if nav_items:
        nav = '<nav class="jump"><a href="#glance">At a Glance</a>' + "".join(nav_items) + "</nav>"
    top = ""
    if FIN_GLANCE.get(date):
        top += glance_html(FIN_GLANCE[date])
    if FIN_NUMBERS.get(date):
        top += keynums_html(FIN_NUMBERS[date])
    if imgs.get("lead"):
        top += photo_html(imgs["lead"], prefix)
    return (preamble + nav + top + "\n".join(rendered) +
            '<p class="totop"><a href="#top">Back to top ↑</a></p>')

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
for date, (pat, label, one) in FIN.items():
    body = (f'<p class="crumb"><a href="../index.html">Finance Briefing</a> · '
            f'<a href="index.html">Archive</a></p><article>{render_article(fin_report(date), date, "../../")}</article>')
    (DOCS / "finance" / "archive" / f"{date}.html").write_text(
        shell("../../", f"Finance Briefing — {label}", body), encoding="utf-8")

latest = "2026-11-15"
body = (f'<p class="crumb"><span class="kicker">Finance Briefing · Latest Edition</span></p>'
        f'<article>{render_article(fin_report(latest), latest, "../")}</article>')
(DOCS / "finance" / "index.html").write_text(
    shell("../", f"Finance Briefing — {FIN[latest][1]}", body), encoding="utf-8")

def thumb_html(date, prefix):
    entry = IMAGES.get(date, {}).get("lead")
    if not entry or not (IMG / entry[0]).exists():
        return ""
    return f'<img class="thumb" src="{prefix}img/{entry[0]}" alt="" loading="lazy">'

items = "\n".join(
    f'<li>{thumb_html(d, "../../")}<span class="d">{FIN[d][1]}</span><br>'
    f'<a href="{d}.html">Finance Briefing — {d}</a><p>{FIN[d][2]}</p></li>'
    for d in sorted(FIN, reverse=True))
body = f'<span class="kicker">Finance</span><h2 class="sec" style="margin-top:8px">Finance Briefing — Back Issues</h2><ul class="arch">{items}</ul>'
(DOCS / "finance" / "archive" / "index.html").write_text(
    shell("../../", "Finance Briefing Archive", body), encoding="utf-8")

# ---------- TECH: construction / engineering / tech news ----------
# Parallel structure to FIN. The Product Spotlight refreshes every
# WEEKDAY (per Sanjay): fresh picks Mon–Fri, weekends carry Friday's.
# Display labels therefore say "Spotlight" even where a report draft
# said "product of the day".
TECH = {  # date -> (report glob, weekday label, archive one-liner)
 "2026-11-15": ("sharma-tech-news-2026-11-15-*", "Sunday, November 15, 2026",
   "Construction input costs jumped 13.3% year-over-year — copper wire & cable up 25.5% — while contractors' selling prices rose only 5.5%. Inaugural Product Spotlight: Leviton Lever Edge USB outlets ⚡ and Bosch YORK YD heat pumps ❄️."),
}
TECH_IMAGES = {  # photos pulled from the articles the report cites
 "2026-11-15": {
  "lead": ("tech-lead.webp", "Bundle of steel sections in a warehouse",
    "A bundle of steel sections — steel mill products are up 32.9% year-over-year in an input-cost surge led by copper wire & cable, up 25.5%.",
    "Photo: Image/Adobe via ENR"),
  "inline": ("tech-collapse.jpg", "FDNY at the Brooklyn collapse site, November 12, 2026",
    "FDNY crews at the Flatbush Avenue collapse site in Brooklyn, Nov 12, 2026 — eight people were killed when a building fell into an adjacent excavation.",
    "Photo: Yuki Iwamura / AP Photo via FireRescue1"),
 },
}
TECH_SPOT = {  # date -> report item no. -> photo entry (from the cited article/product page)
 "2026-11-15": {
  "2.1": ("tech-leviton.webp", "Leviton Lever Edge USB outlet (ECC15-W)",
    "Leviton's Lever Edge duplex receptacle with built-in USB charging — lever termination rated up to 3.5× faster than screw terminals.",
    "Photo: Leviton"),
  "2.2": ("tech-york.jpg", "YORK YD heat pump outdoor unit",
    "A YORK YD-series heat pump — Bosch Home Comfort's new portfolio puts a fully modulating inverter compressor at every efficiency tier.",
    "Photo: YORK / Bosch Home Comfort"),
 },
}

def tech_report(date):
    pat = TECH[date][0]
    p = sorted(NOTES.glob(pat + "/report.md"))[0]
    return p.read_text(encoding="utf-8", errors="replace")

def render_spotlight(body, date, prefix):
    parts = re.split(ITEM_SPLIT, body, flags=re.S)
    items = []
    for i in range(1, len(parts), 2):
        items.append((parts[i], parts[i] + (parts[i + 1] if i + 1 < len(parts) else "")))
    out = []
    for marker, block in items:
        headline = strip_tags(marker)
        num = re.match(r"\s*(\d+\.\d+)", headline)
        entry = TECH_SPOT.get(date, {}).get(num.group(1)) if num else None
        text = strip_tags(block)
        maker = re.search(r"Maker:\s*(.*?)(?=\s*Release date:)", text)
        rel = re.search(r"Release date:\s*(.*?)(?=\s*What it is:)", text)
        cool = re.search(r"Why it's cool for Sharma:\s*(.*?)(?=\s*Price:|\s*Source:|$)", text, re.S)
        kick = ("⚡ Electrical Spotlight" if "⚡" in headline
                else "❄️ HVAC Spotlight" if "❄" in headline
                else "Product Spotlight")
        ml = ""
        if maker or rel:
            bits = []
            if maker: bits.append(f"Maker: {excerpt(maker.group(1), 90)}")
            if rel: bits.append(f"Released: {excerpt(rel.group(1), 150)}")
            ml = f'<p class="makerline">{" · ".join(bits)}</p>'
        deck = (f'<p class="deck"><b>Why it\'s cool:</b> {excerpt(cool.group(1), 340)}</p>'
                if cool else "")
        full = block.replace("PRODUCT OF THE DAY", "SPOTLIGHT")
        out.append(
            f'<div class="spotlight"><span class="kicker">{kick}</span>'
            f'<h3 class="item-head">{headline.replace("PRODUCT OF THE DAY", "SPOTLIGHT")}</h3>'
            f'{photo_html(entry, prefix)}{ml}{deck}'
            f'<details class="full"><summary>Read the full story</summary>'
            f'<div class="fullbody">{full}</div></details></div>')
    return "\n".join(out)

def render_tech_article(md_text, date, prefix):
    md_text = re.sub(r"^-?\s*PHOTO:.*$", "", md_text, flags=re.M)
    raw = md_to_html(md_text)
    chunks = re.split(r'(<h2>.*?</h2>)', raw, flags=re.S)
    preamble = chunks[0]
    sections = []
    for i in range(1, len(chunks), 2):
        sections.append((chunks[i], chunks[i + 1] if i + 1 < len(chunks) else ""))
    imgs = TECH_IMAGES.get(date, {})
    intro_bits, glance, spotlight, generic = [], "", "", []
    for heading, body in sections:
        title = strip_tags(heading)
        if title.startswith("Edition No."):
            intro_bits.append(f'<p class="windowline">{title}</p>')
            if strip_tags(body):
                intro_bits.append(f'<div class="sec-intro">{body}</div>')
        elif title.startswith("Summary"):
            lis = re.findall(r"<li>(.*?)</li>", body, flags=re.S)
            lis = [re.sub(r"product of the day", "spotlight product", li, flags=re.I)
                   for li in lis]
            if lis:
                glance = glance_html(lis)
        elif "PRODUCT SPOTLIGHT" in title:
            spotlight = render_spotlight(body, date, prefix)
        elif strip_tags(body):
            generic.append((title, body))
    nav_items, rendered = [], []
    if glance:
        nav_items.append('<a href="#glance">At a Glance</a>')
    if spotlight:
        nav_items.append('<a href="#spotlight">⭐ Product Spotlight</a>')
    sec_no = 0
    for title, body in generic:
        sec_no += 1
        sid = f"sec-{sec_no}"
        nav_items.append(f'<a href="#{sid}">{title}</a>')
        block = f'<h2 id="{sid}">{title}</h2>'
        if sec_no == 1 and imgs.get("lead"):
            block += photo_html(imgs["lead"], prefix)
        block += render_section_body(body)
        if sec_no == 1 and imgs.get("inline"):
            block += photo_html(imgs["inline"], prefix, "small")
        rendered.append(block)
    nav = f'<nav class="jump">{"".join(nav_items)}</nav>' if nav_items else ""
    spot = ""
    if spotlight:
        spot = ('<h2 id="spotlight">⭐ Product Spotlight</h2>'
                '<p class="sec-intro">A cool new electrical product and a cool new '
                'HVAC product every weekday — fresh picks Monday–Friday; weekends '
                'carry Friday\'s picks.</p>' + spotlight)
    return ('<div class="secname">Construction · Engineering · Tech</div>' +
            preamble + "\n".join(intro_bits) + nav + glance + spot +
            "\n".join(rendered) +
            '<p class="totop"><a href="#top">Back to top ↑</a></p>')

# ---- tech archive pages + latest ----
(DOCS / "tech" / "archive").mkdir(parents=True, exist_ok=True)
for date, (pat, label, one) in TECH.items():
    body = (f'<p class="crumb"><a href="../index.html">Tech Briefing</a> · '
            f'<a href="index.html">Archive</a></p><article>{render_tech_article(tech_report(date), date, "../../")}</article>')
    (DOCS / "tech" / "archive" / f"{date}.html").write_text(
        shell("../../", f"Sharma Tech — {label}", body), encoding="utf-8")

tlatest = sorted(TECH)[-1]
body = (f'<p class="crumb"><span class="kicker">Construction · Engineering · Tech · Latest Edition</span></p>'
        f'<article>{render_tech_article(tech_report(tlatest), tlatest, "../")}</article>')
(DOCS / "tech" / "index.html").write_text(
    shell("../", f"Sharma Tech — {TECH[tlatest][1]}", body), encoding="utf-8")

def tech_thumb_html(date, prefix):
    entry = TECH_IMAGES.get(date, {}).get("lead")
    if not entry or not (IMG / entry[0]).exists():
        return ""
    return f'<img class="thumb" src="{prefix}img/{entry[0]}" alt="" loading="lazy">'

titems = "\n".join(
    f'<li>{tech_thumb_html(d, "../../")}<span class="d">{TECH[d][1]}</span><br>'
    f'<a href="{d}.html">Sharma Tech — {d}</a><p>{TECH[d][2]}</p></li>'
    for d in sorted(TECH, reverse=True))
body = f'<span class="kicker">Construction · Engineering · Tech</span><h2 class="sec" style="margin-top:8px">Sharma Tech — Back Issues</h2><ul class="arch">{titems}</ul>'
(DOCS / "tech" / "archive" / "index.html").write_text(
    shell("../../", "Sharma Tech Archive", body), encoding="utf-8")

# ---- home ----
legal_arch = "\n".join(
    f'<li><span class="d">{LEGAL[d][0]}</span><br><a href="{LEGAL_BASE}/archive/{d}.html">Legal Briefing — {d}</a><p>{LEGAL[d][1]}</p></li>'
    for d in sorted(LEGAL, reverse=True))
fin_arch = "\n".join(
    f'<li>{thumb_html(d, "")}<span class="d">{FIN[d][1]}</span><br><a href="finance/archive/{d}.html">Finance Briefing — {d}</a><p>{FIN[d][2]}</p></li>'
    for d in sorted(FIN, reverse=True))
tech_arch = "\n".join(
    f'<li>{tech_thumb_html(d, "")}<span class="d">{TECH[d][1]}</span><br><a href="tech/archive/{d}.html">Sharma Tech — {d}</a><p>{TECH[d][2]}</p></li>'
    for d in sorted(TECH, reverse=True))
tech_lead = TECH_IMAGES.get(tlatest, {}).get("lead")
home_imgs = IMAGES.get("home", {})
body = f"""
{glance_html(HOME_GLANCE)}
<div class="front">
<div class="story"><span class="kicker">Legal Briefing</span>
{photo_html(home_imgs.get("legal"), "")}
<h2 class="headline">{LEGAL['2026-11-15'][1]}</h2>
<p class="byline">Legal Briefing — Harvey, Legal Advisor · Edition of Nov 15, 2026</p>
<a class="cont" href="{LEGAL_BASE}/">Read today's legal briefing →</a></div>
<div class="story"><span class="kicker">Finance Briefing</span>
{photo_html(home_imgs.get("finance"), "")}
<h2 class="headline">{FIN['2026-11-15'][2]}</h2>
<p class="byline">Finance Briefing — Warren Buffett, CFO · Edition of Nov 15, 2026</p>
<a class="cont" href="finance/index.html">Read today's finance briefing →</a></div>
</div>
<div class="techfeature"><span class="kicker">Construction · Engineering · Tech</span>
{photo_html(tech_lead, "")}
<h2 class="headline">Construction input costs jump 13.3% in a year; copper wire &amp; cable up 25.5%</h2>
<p class="spotline">⭐ Product Spotlight — ⚡ <b>Leviton Lever Edge™ USB Outlets</b> · ❄️ <b>Bosch Home Comfort YORK® YD heat pumps</b></p>
<p class="byline">Sharma Tech · Edition of Nov 15, 2026</p>
<a class="cont" href="tech/index.html">Read today's tech briefing →</a></div>
<h2 class="sec">Legal — Back Issues</h2><ul class="arch">{legal_arch}</ul>
<h2 class="sec">Finance — Back Issues</h2><ul class="arch">{fin_arch}</ul>
<h2 class="sec">Tech — Back Issues</h2><ul class="arch">{tech_arch}</ul>
"""
(DOCS / "index.html").write_text(shell("", "Home — Sunday, November 15, 2026", body), encoding="utf-8")
print("built:", [str(p.relative_to(DOCS)) for p in sorted(DOCS.rglob('*.html'))])
