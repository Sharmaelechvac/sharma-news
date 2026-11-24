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

Layout: the standing Sharma design system (~/workspace/DESIGN-RULES.md) —
navy/gold, kit display headings, Inter body at 18px, IBM Plex
Mono for numbers, flat white panels on #f4f6fb, full-color photos, no
emoji, no newspaper costume. Every finance edition page opens with an
"At a Glance" box + "Key Numbers" strip (both taken only from that
report's own summary), then each story shows headline + deck + Sharma
impact line, and the FULL original text on the story's OWN page —
clicking a headline or a photo opens that page (per Sanjay
2026-11-15: a click must go to a new page to read more). The Permit
News page is compiled from permits-source.json (see below)."""
import re, glob, html as ihtml, markdown, pathlib

ROOT = pathlib.Path(__file__).parent
DOCS = ROOT / "docs"
IMG = DOCS / "img"
NOTES = pathlib.Path.home() / "workspace" / "research_notes"
LEGAL_BASE = "https://sharmaelechvac.github.io/sharma-legal-briefing"

CSS = """
:root{--navy:#264387;--navy-d:#1a2f61;--gold:#F0A846;--ink:#1d2433;--mute:#5b6478;
--line:#dfe4ee;--tint:#f4f6fb;--paper:#ffffff}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--tint);color:var(--ink);
font-family:-apple-system,"SF Pro Text",Inter,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
font-size:18px;line-height:1.65}
h1,h2,h3,.headline,.item-head,.kicker,.secname,h2.sec,.glance h2,nav.main a,.top .ttl b,
.spotline,.cont{font-family:-apple-system,"SF Pro Display",Inter,"Segoe UI",Arial,sans-serif;font-weight:700}
a{color:var(--navy);text-decoration:underline;text-decoration-color:#b9c4dc;text-underline-offset:2px}
a:hover{color:var(--navy-d);text-decoration-color:var(--navy-d)}
.num,.kn b,.dateline{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-variant-numeric:tabular-nums}
/* ---------- header ---------- */
.top{background:#fff;border-bottom:3px solid var(--gold)}
.top .bar{max-width:1040px;margin:0 auto;padding:12px 16px;display:flex;align-items:center;
justify-content:space-between;gap:12px}
.top .brand{display:block;line-height:0}
.top img.logo{height:54px;width:auto}
.top .ttl{text-align:right;line-height:1.25}
.top .ttl b{display:block;font-size:19px;color:var(--navy-d);font-weight:700}
.top .ttl span{display:block;font-size:14px;color:var(--mute)}
nav.main{background:#fff;border-bottom:1px solid var(--line)}
nav.main .in{max-width:1040px;margin:0 auto;padding:0 8px;display:flex;overflow-x:auto;
-webkit-overflow-scrolling:touch;scrollbar-width:none}
nav.main .in::-webkit-scrollbar{display:none}
nav.main a{color:var(--navy);text-decoration:none;font-size:17px;font-weight:700;white-space:nowrap;
padding:13px 12px;display:flex;align-items:center;min-height:48px}
nav.main a:hover{color:var(--navy-d)}
nav.main a.on{color:var(--navy-d);border-bottom:3px solid var(--gold);padding-bottom:10px}
.wrap{max-width:1040px;margin:0 auto;padding:8px 16px 48px;background:#fff}
/* ---------- photos ---------- */
.photo{margin:10px 0 12px}
.photo img{width:100%;height:auto;display:block;background:var(--tint);border:1px solid var(--line)}
.photo figcaption{font-size:14px;color:var(--mute);margin-top:5px;line-height:1.45}
.photo .credit{display:block;font-size:13px;color:var(--mute);margin-top:1px}
.photo.small{max-width:430px}
.story .photo img{max-height:260px;object-fit:cover;object-position:top}
/* ---------- at a glance / key numbers ---------- */
.glance{background:var(--tint);border-left:3px solid var(--gold);padding:12px 16px 6px;margin:16px 0 14px}
.glance h2{font-size:14px;text-transform:uppercase;letter-spacing:.12em;color:var(--navy);
margin:0 0 6px;border:none;padding:0;font-weight:700}
.glance ul{margin:0 0 8px;padding-left:18px}
.glance li{margin:4px 0;font-size:17px}
.keynums{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));border:1px solid var(--line);
margin:0 0 18px}
.kn{padding:9px 12px;border-right:1px solid var(--line);border-bottom:1px solid var(--line);margin:0 -1px -1px 0}
.kn b{display:block;font-size:28px;line-height:1.15;color:var(--navy-d)}
.kn span{font-size:14px;color:var(--mute)}
/* ---------- front page ---------- */
.front{display:grid;grid-template-columns:1fr 1fr;gap:0;margin-top:18px;
border-bottom:1px solid var(--line);padding-bottom:18px}
.story{padding:0 20px}
.story:first-child{padding-left:0}
.story + .story{border-left:1px solid var(--line);padding-right:0}
.kicker{display:inline-block;font-size:14px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
color:var(--navy);border-bottom:2px solid var(--gold);padding-bottom:2px}
.story .headline,.techfeature .headline{font-weight:700;color:var(--navy-d);
font-size:44px;line-height:1.12;margin:8px 0 10px}
.byline{font-size:14px;color:var(--mute);margin:0 0 6px}
.cont{font-size:17px;font-weight:700;color:var(--navy);display:inline-block;padding:10px 0}
/* ---------- index / archive ---------- */
h2.sec{font-size:30px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--navy);
border-bottom:2px solid var(--navy);padding-bottom:6px;margin:34px 0 0}
.arch{list-style:none;margin:0;padding:0}
.arch li{border-bottom:1px solid var(--line);padding:12px 0;overflow:hidden}
.arch li a{font-size:19px;font-weight:700;color:var(--navy-d);text-decoration:none}
.arch li a:hover{text-decoration:underline}
.arch .d{color:var(--mute);font-size:14px;letter-spacing:0;text-transform:none}
.arch p{margin:2px 0 0;color:#3a4255;font-size:17px}
.arch img.thumb{width:96px;height:64px;object-fit:cover;float:left;margin:3px 12px 4px 0;
background:var(--tint);border:1px solid var(--line)}
/* ---------- article pages ---------- */
article{overflow-wrap:break-word;padding-top:4px;max-width:72ch}
article h1{font-size:28px;line-height:1.2;color:var(--navy-d);margin:8px 0 10px}
article h2{font-size:30px;line-height:1.2;color:var(--navy-d);margin-top:32px;border-bottom:2px solid var(--gold);padding-bottom:6px}
article h3{font-size:22px;color:var(--ink);margin-top:24px}
article a{word-break:break-word}
article table{border-collapse:collapse;width:100%;display:block;overflow-x:auto;font-size:16px}
article th,article td{border:1px solid var(--line);padding:8px 11px;text-align:left;vertical-align:top}
article th{background:var(--tint);color:var(--navy-d)}
article code{background:var(--tint);padding:1px 5px;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.88em}
article blockquote{border-left:3px solid var(--gold);margin:14px 0;padding:2px 14px;color:#3a4255}
.windowline{font-size:16px;color:var(--mute);border-bottom:1px solid var(--line);padding-bottom:8px}
.jump{position:sticky;top:0;z-index:6;background:#fff;border-bottom:1px solid var(--line);
display:flex;gap:0 16px;overflow-x:auto;white-space:nowrap;padding:0;margin:0 0 6px;scrollbar-width:none}
.jump::-webkit-scrollbar{display:none}
.jump a{color:var(--navy);text-decoration:none;font-size:15px;font-weight:600;padding:14px 0}
.jump a:hover{color:var(--navy-d);text-decoration:underline}
.item{border-bottom:1px solid var(--line);padding:12px 0 12px}
.item .item-head{font-size:26px;line-height:1.25;color:var(--navy-d);margin:2px 0 6px}
.item .deck{margin:0 0 6px;color:#3a4255;font-size:20px;line-height:1.5}
.item .impact{margin:0 0 4px;font-size:17px;background:#fff8ec;border-left:3px solid var(--gold);padding:6px 12px}
.item .impact b{color:var(--navy-d)}
.item-head a,.spotlight .item-head a,.headline a{color:inherit;text-decoration:none}
.item-head a:hover,.spotlight .item-head a:hover,.headline a:hover{text-decoration:underline}
a.photolink{display:block;text-decoration:none}
.storyhead{font-size:28px;line-height:1.2;color:var(--navy-d);margin:6px 0 10px}
details.full{margin-top:6px}
details.full summary{cursor:pointer;font-size:16px;font-weight:600;color:var(--navy);padding:12px 0}
details.full .fullbody{border-top:1px solid var(--line);padding-top:4px}
.sec-intro{color:#3a4255}
.totop{text-align:right;margin-top:22px}
.totop a{font-size:15px;font-weight:600;padding:10px 0;display:inline-block}
.secname{font-size:14px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--navy);
border-bottom:2px solid var(--navy);padding:6px 0;margin:12px 0 4px}
.spotlight{border:1px solid var(--line);border-top:3px solid var(--gold);padding:14px 18px 10px;margin:0 0 22px;background:#fff}
.spotlight .item-head{font-size:28px;line-height:1.25;color:var(--navy-d);margin:2px 0 6px}
.spotlight .makerline{font-size:16px;color:var(--mute);border-bottom:1px solid var(--line);padding-bottom:7px;margin:0 0 10px}
.spotlight .photo{max-width:560px}
.spotlight .deck{font-size:20px;line-height:1.5;color:#3a4255;margin:0 0 6px}
.techfeature{border-bottom:1px solid var(--line);padding:18px 0 18px;display:grid;
grid-template-columns:300px 1fr;column-gap:20px;align-items:start}
.techfeature .kicker{grid-column:1/-1;justify-self:start;margin-bottom:6px}
.techfeature .photolink{grid-row:2/6}
.techfeature.nophoto{grid-template-columns:1fr}
.techfeature .photo{margin:4px 0 0}
.techfeature .photo img{max-height:200px;object-fit:cover}
.techfeature .photo figcaption{display:none}
.spotline{font-size:17px;margin:0 0 6px}
.crumb{color:var(--mute);font-size:14px;margin:14px 0 6px}
.crumb a{padding:8px 0;display:inline-block}
footer{background:var(--navy-d);color:#cfd8ee;border-top:3px solid var(--gold);font-size:14px}
.pagehead{font-size:38px;line-height:1.15;color:var(--navy-d);margin:8px 0 10px}
table.data{border-collapse:collapse;width:100%;font-size:17px;margin:6px 0 10px}
table.data th,table.data td{border:1px solid var(--line);padding:10px 12px;text-align:left;vertical-align:top}
table.data th{background:var(--tint);color:var(--navy-d);
font-family:"-apple-system","SF Pro Display",Inter,"Segoe UI",sans-serif;font-weight:700;font-size:17px}
table.data td.n,table.data th.n{text-align:right;font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace}
.tblwrap{overflow-x:auto}
footer .fin{max-width:1040px;margin:0 auto;padding:14px 16px 18px}
footer .fin b{color:#fff}
@media(max-width:760px){
body{font-size:17px}
.top img.logo{height:44px}
.top .ttl b{font-size:17px}
.top .ttl span{font-size:14px}
.front{grid-template-columns:1fr}
.story{padding:0}
.story + .story{border-left:none;border-top:1px solid var(--line);margin-top:16px;padding-top:14px}
.techfeature{grid-template-columns:1fr}
.techfeature .photolink{grid-row:auto}
.story .headline,.techfeature .headline{font-size:34px}
article h1,.storyhead{font-size:26px}
article h2{font-size:26px}
.item .item-head{font-size:24px}
.item .deck,.spotlight .deck{font-size:19px}
.spotlight .item-head{font-size:26px}
h2.sec{font-size:26px}
.pagehead{font-size:30px}
.kn b{font-size:24px}
table.data{font-size:16px}
.photo.small{max-width:none}
.story .photo img{max-height:200px}
}

/* ---------- NYT LOOK (Sanjay 2026-11-20: "Still blocky — mimic NYT") —
   Replaces the Home News v3 card look. New York Times style: flat white
   paper, black serif headlines (Georgia), hairline rules instead of
   cards/shadows/rounded corners, small sans kickers and bylines, photos
   square-cornered with small gray captions. Content unchanged. ---------- */
body{background:#fff;color:#121212}
.wrap{background:#fff;padding-top:10px}
nav.main{background:#fff;border-bottom:1px solid #121212}
nav.main a{border-radius:0;color:#121212}
nav.main a.on{background:none;color:#121212;border-bottom:3px solid #121212;box-shadow:none;padding-bottom:10px}
h1,h2,h3,.headline,.item-head,.storyhead,.pagehead,.glance h2,.kn b{
font-family:Georgia,"Times New Roman",Times,serif;color:#121212}
.kicker{display:inline-block;background:none;color:#121212;box-shadow:none;border-radius:0;
padding:0;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}
.glance{background:#fff;border:none;border-top:2px solid #121212;border-bottom:1px solid #DFDFDD;
border-radius:0;box-shadow:none;padding:14px 0 8px;margin:14px 0 16px}
.glance h2{font-family:-apple-system,"SF Pro Text",Inter,Arial,sans-serif;font-size:14px;
font-weight:700;text-transform:uppercase;letter-spacing:.08em}
.glance h2::after{display:none}
.keynums{gap:0;border:none;border-bottom:1px solid #DFDFDD}
.kn{background:#fff;border:none;border-right:1px solid #DFDFDD;border-radius:0;box-shadow:none;padding:10px 14px}
.kn:last-child{border-right:none}
.kn b{font-size:26px}
.kn span{color:#727272}
.front{grid-template-columns:1.55fr 1fr;gap:0;border-bottom:1px solid #DFDFDD;padding-bottom:20px;margin-top:16px}
@media(max-width:760px){.front{grid-template-columns:1fr}}
.story,.story:first-child,.story + .story,.techfeature{background:#fff;border:none;border-left:none;
border-radius:0;box-shadow:none;padding:0 20px;overflow:visible;display:block;margin:0}
.story:first-child{padding-left:0}
.story + .story{border-left:1px solid #DFDFDD;padding-right:0}
@media(max-width:760px){.story,.story:first-child,.story + .story{padding:0}
.story + .story{border-left:none;border-top:1px solid #DFDFDD;margin-top:16px;padding-top:14px}}
.story .kicker,.techfeature .kicker{margin:0}
.story .photolink,.techfeature .photolink{display:block}
.photo{margin:10px 0 12px}
.photo img,.story .photo img,.techfeature .photo img,.front .story:first-child .photo img{
border:none;border-radius:0;box-shadow:none;width:100%;height:auto;aspect-ratio:auto;
max-height:none;object-fit:initial;background:none}
.photo figcaption{padding:6px 0 0;font-size:12px;color:#727272;line-height:1.45}
.photo .credit{font-size:11px;color:#727272;text-transform:none}
.story .headline,.techfeature .headline{font-size:25px;line-height:1.2;letter-spacing:0;
margin:8px 0 8px;padding:0;display:block;-webkit-line-clamp:none;overflow:visible}
.front .story:first-child .headline{font-size:38px;line-height:1.12}
.headline a,.item-head a{color:#121212}
.byline,.spotline{padding:0;font-size:13px;color:#727272}
.byline{font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.cont{display:inline-block;background:none;color:#121212;box-shadow:none;border-radius:0;
margin:8px 0 0;padding:8px 0;font-size:14px;font-weight:700;text-decoration:underline;
text-underline-offset:3px}
.cont:hover{color:#121212}
.techfeature{display:grid;grid-template-columns:300px 1fr;column-gap:20px;align-items:start;
padding:18px 0;margin-top:0;border-bottom:1px solid #DFDFDD}
@media(max-width:760px){.techfeature{grid-template-columns:1fr}}
.techfeature .photo{margin:4px 0 0}
.techfeature.nophoto{background:#fff;color:#121212;display:block}
.techfeature.nophoto .headline,.techfeature.nophoto .headline a{color:#121212}
.techfeature.nophoto .byline,.techfeature.nophoto .spotline{color:#727272}
.techfeature.nophoto .cont{background:none;color:#121212}
h2.sec,.pagehead{font-family:-apple-system,"SF Pro Text",Inter,Arial,sans-serif;font-size:15px;
font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#121212;
border-bottom:1px solid #121212;padding-bottom:6px}
h2.sec::after,.pagehead::after{display:none}
.arch li{background:#fff;border-bottom:1px solid #DFDFDD;border-radius:0;box-shadow:none;
padding:14px 0;margin-bottom:0}
.arch img.thumb{width:96px;height:72px;border:none;border-radius:0;margin:3px 12px 4px 0}
.arch li a{color:#121212;font-family:Georgia,"Times New Roman",Times,serif}
article{background:#fff;border-radius:0;box-shadow:none;padding:4px 0 28px;margin-top:6px}
article .photo img{border-radius:0}
.item{background:#fff;border-bottom:1px solid #DFDFDD;border-radius:0;box-shadow:none;
padding:18px 0;margin-top:0}
.item .item-head{font-size:26px;line-height:1.22}
.item .deck{color:#333}
.item .impact{background:#F7F7F5;border-left:2px solid #121212;border-radius:0;padding:8px 12px}
.item .impact b{color:#121212}
.spotlight{background:#fff;border:none;border-top:2px solid #121212;border-radius:0;
box-shadow:none;padding:14px 0 10px}
.jump{background:#fff;border-bottom:1px solid #DFDFDD}
.jump a{background:none;border:none;border-radius:0;box-shadow:none;padding:12px 0;margin:0 16px 0 0;
font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#121212}
.tblwrap{background:#fff;border-radius:0;box-shadow:none;padding:0}
table.data th{background:#F7F7F5;color:#121212}
.storyhead{font-size:32px;line-height:1.15}
a{color:#121212}
html[data-scheme="dark"] .story,html[data-scheme="dark"] .techfeature,
html[data-scheme="dark"] .item,html[data-scheme="dark"] .spotlight,
html[data-scheme="dark"] article,html[data-scheme="dark"] .glance,
html[data-scheme="dark"] .arch li,html[data-scheme="dark"] .kn{background:#fff}
html[data-scheme="dark"] .story .headline,html[data-scheme="dark"] .techfeature .headline,
html[data-scheme="dark"] .item .item-head,html[data-scheme="dark"] .storyhead{color:#121212}
/* ---------- NYT FRONT PAGE STRUCTURE (Sanjay 2026-11-20: "Copy the real
   NYT front page layout exactly") — blackletter masthead with double rule,
   lead story centered in a wide middle column, secondary stories in ruled
   side rails, glance and archives flowing in newspaper columns. Hub-only
   grid uses :has(> .front) so edition/story pages keep the article layout. */
.masthead{text-align:center;padding:20px 0 12px;border-bottom:4px double #121212;margin-bottom:6px}
.mast-name{font-family:"UnifrakturMaguntia",Georgia,"Times New Roman",serif;
font-size:68px;line-height:1;color:#121212}
.mast-tag{font-size:12px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#555;margin-top:8px}
@media(max-width:760px){.mast-name{font-size:44px}}
nav.main{border-top:1px solid #DFDFDD}
nav.main .in{justify-content:center}
.wrap:has(> .front){display:grid;grid-template-columns:1fr 2.1fr 1.15fr;
grid-template-areas:"head head head" "left center right" "left center right2"
"glance glance glance";column-gap:0}
.wrap:has(> .front) > .masthead{grid-area:head}
.wrap:has(> .front) > .front{display:contents}
.wrap:has(> .front) > .glance{grid-area:glance}
.wrap:has(> .front) > h2.sec,.wrap:has(> .front) > .arch{grid-column:1 / -1}
.nyt-lead{grid-area:center;padding:2px 22px 0 !important;border:none !important;
display:flex !important;flex-direction:column;text-align:center}
.nyt-lead .kicker{align-self:center}
.nyt-lead .headline{order:1;font-size:44px !important;line-height:1.08 !important;margin:12px 0 10px}
.nyt-lead .byline{order:2}
.nyt-lead .photolink{order:3;margin-top:12px}
.nyt-lead .photo figcaption{text-align:left}
.nyt-lead .cont{order:4;align-self:center}
.wrap:has(> .front) > .front .story:not(.nyt-lead){grid-area:left;
padding-right:18px !important;border-right:1px solid #DFDFDD}
.wrap:has(> .front) > .front .story:not(.nyt-lead) .headline{font-size:23px;line-height:1.22}
.wrap:has(> .front) > .techfeature{grid-area:right;display:block;
padding-left:18px;border-left:1px solid #DFDFDD;border-bottom:none}
.wrap:has(> .front) > .techfeature .headline{font-size:20px;line-height:1.25}
.wrap:has(> .front) > .techfeature.nophoto{grid-area:right2}
@media(max-width:860px){
.wrap:has(> .front){grid-template-columns:1fr;
grid-template-areas:"head" "center" "left" "right" "right2" "glance"}
.nyt-lead{padding:0 !important}
.nyt-lead .headline{font-size:33px !important}
.wrap:has(> .front) > .front .story:not(.nyt-lead){padding-right:0 !important;
border-right:none;border-top:1px solid #DFDFDD;padding-top:14px;margin-top:6px}
.wrap:has(> .front) > .techfeature{padding-left:0;border-left:none;
border-top:1px solid #DFDFDD;padding-top:14px}}
.glance ul{columns:2;column-gap:36px}
@media(max-width:760px){.glance ul{columns:1}}
.arch{columns:3;column-gap:30px}
.arch li{break-inside:avoid}
@media(max-width:860px){.arch{columns:1}}
article{max-width:840px;margin-left:auto;margin-right:auto}
article h1{text-align:center;font-size:40px;line-height:1.12}
.crumb{text-align:center}
.jump{justify-content:center}
.jump a{margin:0 8px}
.sitehead .brand{justify-content:center;text-align:center;flex-direction:column;gap:8px}
.sitetitle{font-size:44px}
.pagenav{justify-content:center}
.frontmatter{text-align:center}
.frontmatter h1.headline{font-size:48px}
.frontmatter .coverage{margin:0 auto}
/* ---------- CONSISTENT THROUGHOUT (Sanjay 2026-11-20) — every page type
   carries the same NYT system: mini nameplate on section/story/archive
   pages, paper-white footer with double rule, black rules under section
   heads, centered serif page/story heads. ---------- */
.masthead--mini{padding:12px 0 8px;margin-bottom:4px}
.masthead--mini .mast-name{font-size:36px}
.masthead--mini .mast-tag{display:none}
footer{background:#fff;color:#555;border-top:4px double #121212}
footer .fin b{color:#121212}
article h2{border-bottom:1px solid #121212}
.storyhead{text-align:center;font-size:36px;line-height:1.12;color:#121212}
.pagehead{font-family:Georgia,"Times New Roman",Times,serif;text-align:center;
font-size:40px;text-transform:none;letter-spacing:0;color:#121212}
.secname{font-family:-apple-system,"SF Pro Text",Inter,Arial,sans-serif;font-size:15px;
font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#121212;
border-bottom:1px solid #121212;padding:6px 0;text-align:center}
.windowline{text-align:center;border-bottom:none;color:#727272}
.totop{text-align:center}
.totop a{color:#555;font-size:13px;text-transform:uppercase;letter-spacing:.06em}
details.full summary{color:#121212}
/* ---------- REFINEMENT — THE CLICK (Sanjay 2026-11-20: "more refined,
   especially when clicking") — story/edition pages read like an NYT
   article: narrow serif reading column, proper byline/caption small
   print, ruled full-text section, quiet link behaviour. ---------- */
article{max-width:720px}
article p,.item .deck,.deck,details.full .fullbody{font-family:Georgia,"Times New Roman",Times,serif;
font-size:18px;line-height:1.62;color:#333}
.storyhead{font-size:38px;letter-spacing:-.01em;margin-top:10px}
article h1{letter-spacing:-.01em}
.crumb{font-family:-apple-system,"SF Pro Text",Inter,Arial,sans-serif;font-size:12px;
text-transform:uppercase;letter-spacing:.06em;color:#727272}
.photo figcaption{font-size:12px;color:#727272;line-height:1.5}
.photo .credit{font-size:11px;color:#909090;display:block;margin-top:2px}
.item{padding:22px 0}
.item .impact{font-family:-apple-system,"SF Pro Text",Inter,Arial,sans-serif;font-size:16px;line-height:1.55}
.item-head a:hover,.headline a:hover,.arch li a:hover{text-decoration:underline;text-underline-offset:3px}
a{-webkit-tap-highlight-color:transparent}
details.full{margin-top:10px}
details.full summary{font-family:-apple-system,"SF Pro Text",Inter,Arial,sans-serif;
font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#121212;
padding:14px 0;border-top:1px solid #DFDFDD;list-style:none}
details.full .fullbody{border-top:1px solid #DFDFDD;padding-top:10px}
::selection{background:#E8EEF7}
html{scroll-behavior:smooth}
.glance li{margin:0;padding:7px 0;border-bottom:1px solid #EDEDEB;font-size:16.5px;line-height:1.5}
.glance li:last-child{border-bottom:none}
.kn span{font-size:11px;text-transform:uppercase;letter-spacing:.06em}
"""

_EMOJI = re.compile("[\u2600-\u27BF\u2B50\u2B55\U0001F000-\U0001FAFF]\uFE0F?[ \u00a0]?")
def plain(s):
    """No emoji anywhere in the output (Sharma brand rule, 2026-11-15)."""
    return _EMOJI.sub("", s)

def plain_heading(title):
    """Plain labels only on news pages (DESIGN-RULES): no 'quarantined' or
    'honesty note' style section headings. The items under the heading and
    their in-text flags stay exactly as written in the report."""
    low = title.lower()
    if "quarantin" in low or "unverified" in low:
        return "Not confirmed — excluded from the confirmed items above"
    if "honesty note" in low:
        return "About the reporting window"
    return title

def shell(prefix, title, body, chip="", active=""):
    title, body = plain(title), plain(body)
    def on(key):
        return ' class="on"' if active == key else ""
    mast = "" if active == "home" else '<div class="masthead masthead--mini"><div class="mast-name">Sharma News</div></div>'
    return f"""<!DOCTYPE html>
<html lang="en" class="sk"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex">
<meta name="theme-color" content="#264387">\n<meta name="color-scheme" content="light">\n<script>(function(){{try{{if(localStorage.getItem("sk-scheme")==="dark"){{var d=document.documentElement;d.setAttribute("data-scheme","dark");var m=document.querySelector('meta[name="theme-color"]');if(m)m.content=d.getAttribute("data-theme")==="track"?"#1C1C1E":"#1a2f61"}}}}catch(e){{}}}})()</script>
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="News">
<title>{title} — Sharma News</title>
<link rel="manifest" href="{prefix}manifest.webmanifest">
<link rel="apple-touch-icon" href="https://sharma-kit.sharma-crew.workers.dev/assets/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="32x32" href="https://sharma-kit.sharma-crew.workers.dev/assets/favicon-32.png">
<link rel="stylesheet" href="https://sharma-kit.sharma-crew.workers.dev/sharma-kit.css">
<link href="https://fonts.googleapis.com/css2?family=UnifrakturMaguntia&display=swap" rel="stylesheet">
<script src="https://sharma-kit.sharma-crew.workers.dev/sharma-kit.js" defer></script>
<style>{CSS}</style></head>
<body id="top" class="sk">
<header class="sk-header"><div class="sk-header__bar">
<div class="sk-header__lead"><a class="sk-header__logo" href="{prefix}index.html"><img src="https://sharma-kit.sharma-crew.workers.dev/assets/logo-white-header.png" alt="Sharma Electric &amp; HVAC" width="103" height="20"></a></div>
<div class="sk-header__title">Sharma News</div>
<div class="sk-header__trail"><a class="sk-header__btn" href="{prefix}more/" aria-label="More"><svg class="sk-icon"><use href="#i-more"/></svg></a></div>
</div></header>
<div class="sk-offline"></div>
<nav class="main"><div class="in">
<a href="{prefix}index.html"{on("home")}>Home</a>
<a href="{LEGAL_BASE}/">Legal</a>
<a href="{prefix}finance/index.html"{on("finance")}>Finance</a>
<a href="{prefix}finance/archive/index.html">Finance archive</a>
<a href="{prefix}tech/index.html"{on("tech")}>Tech</a>
<a href="{prefix}tech/archive/index.html">Tech archive</a>
<a href="{prefix}permits/index.html"{on("permits")}>Permit News</a>
</div></nav>
<div class="wrap">{mast}{body}</div>
<footer><div class="fin"><b>Sharma Electric &amp; HVAC</b> · Sharma News, updated daily at 5:00 AM ET. News summaries for the Sharma team. Not legal or financial advice.</div></footer>
<script>if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost")) {{ addEventListener("load", function(){{ navigator.serviceWorker.register("{prefix}sw.js?kit=https://sharma-kit.sharma-crew.workers.dev", {{ scope: "/sharma-news/" }}).catch(function(){{}}); }}); }}</script>
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
  "legal": ("home-legal.jpg", "The U.S. Capitol dome at dusk with lit windows",
    "The U.S. Capitol at dusk — the Senate on Wednesday, Nov 18 cleared the BAAJA permitting bill's last 60-vote hurdle (final cloture 65–31), leaving only a simple-majority passage vote.",
    "Photo: Heatmap News"),
  "finance": ("2026-11-24-lead.jpg", "Nvidia CEO Jensen Huang",
    "Nvidia reinstated Jensen Huang as CEO on Monday, November 23 and the stock closed +31.48% at $165.05 — its best day since 2003 — snapping a seven-session losing streak as the S&P 500 rose 4.73% to 7,237.17.",
    "Photo: Reuters via CNN"),
 },
 "2026-11-24": {
  "lead": ("2026-11-24-lead.jpg", "Nvidia CEO Jensen Huang",
    "Nvidia reinstated Jensen Huang as CEO on Monday, November 23 and the stock closed +31.48% at $165.05 — its best day since 2003 — snapping a seven-session losing streak as the S&P 500 rose 4.73% to 7,237.17.",
    "Photo: Reuters via CNN"),
 },
 "2026-11-23": {
  "lead": ("2026-11-23-lead.webp", "Mortgage rates chart, November 22, 2026",
    "Zillow's Sunday 30-year purchase average held at 7.18%, unchanged from Saturday — quoted money goes into Monday where Friday's panic bid left it, with Wednesday's PCE print the next test.",
    "Photo: Norada Real Estate (Zillow via Yahoo Finance)"),
 },
 "2026-11-21": {
  "lead": ("2026-11-20-lead.jpg", "Anthropic CEO Dario Amodei and President Daniela Amodei celebrate the company's IPO at Nasdaq",
    "Anthropic fell 8.5% to $88.91 on its second trading day, Friday, Nov 20 — touching $83.05, five cents above its $83 IPO price — as the S&P 500 fell 3.70% into correction.",
    "Photo: Reuters via New York Post"),
 },
 "2026-11-20": {
  "lead": ("2026-11-20-lead.jpg", "Anthropic CEO Dario Amodei and President Daniela Amodei celebrate the company's IPO at Nasdaq",
    "Anthropic's record $81.3 billion IPO — priced at $83, opened at $111.50, closed at $97.17 (+17.07%) — could not stem Thursday's rout: the S&P 500 fell 2.02% for a sixth straight day.",
    "Photo: Reuters via New York Post"),
  "inline": ("2026-11-20-inline.jpg", "A home for sale with a mortgage-rate backdrop",
    "Freddie Mac's weekly 30-year rate jumped 17 bp to 7.28% for the week ending November 19, ending four straight weekly declines.",
    "Photo: Realtor.com"),
 },
 "2026-11-19": {
  "lead": ("2026-11-19-lead.jpg", "New home construction",
    "October housing starts rose 9.9% to a 1.309 million pace, but single-family permits fell 8.7% to 772,000 — the lowest since January 2023.",
    "Photo: NAHB"),
  "inline": ("2026-11-19-inline.jpg", "A homeowner posting a for-sale sign in a front yard",
    "Pending home sales fell 4.7% in October to a record-low index of 63.0; the South fell 6.3% on the month.",
    "Photo: Getty Images via National Association of Realtors"),
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
 "2026-11-24": [
   "Nvidia reinstated Jensen Huang as CEO, president and director — unanimously, effective immediately, 12 days after his November 11 resignation — and Nvidia closed at $165.05 (+31.48%, best day since 2003, about +$952B of market value). The indexes snapped a seven-session losing streak and exited correction: S&P 500 7,237.17 (+4.73%), Nasdaq 24,089.56 (+6.51%), Dow 49,595.31 (+3.01%); VIX 26.62 (−25.8%). Both indexes remain below their October 6 peaks (S&P −7.4%, Nasdaq −12.7%).",
   "Bonds did not confirm it: Treasury par yields for November 23 were 2-year 4.63% and 10-year 4.92%, both unchanged vs November 20 (30-year 5.29%). NY Fed President Williams said inflation is 'simply too high,' 2% is '100 percent essential,' and the Fed must act 'over time' — PCE inflation about 3.5% at end-2026 on his path, target not reached until 2028. December +25 bp pricing firmed to 91.2%–95.1% across Monday's snapshots, with 50 bp back at 4.9%. Blackout begins midnight Saturday, November 28; FOMC December 8–9.",
   "Mortgage money stayed put: MND daily 30-year 7.34% (+1 bp), Zillow purchase 7.18% for a third straight day (refinance 7.46%), Bankrate 7.40%; Freddie Mac's weekly stands at 7.28%. Builders rose only about 1.3% in a +4.73% market (DHI $147.24, LEN $81.90, PHM $126.35) — the rate trade did not recover with the AI trade.",
   "Copper split: COMEX front month settled +2.74% at $5.6270/lb with the risk rally while LME three-month copper fell 2.33% to $12,162.50/t. CME lumber (January 2027) settled at $541.00 per 1,000 bd ft (+$4.00). No new steel, PVC or R-454B print.",
   "Oil fell to three-month lows despite Hormuz — Brent (January) $89.37 (−3.46%), WTI (January) $80.17 (−3.88%) — as Libya's Sharara pipeline restarted and Gulf barrels kept flowing. AAA fell an eighth straight day: regular $3.6366/gal, diesel $5.8182/gal (eighth day under $6); Florida regular $3.4604, diesel $5.5687. The IRGC's claim that three tankers hit naval mines in Hormuz on Monday is UNVERIFIED — CENTCOM had not responded and no UKMTO confirmation was located.",
   "Bankruptcy: Florida's Otero Repair, LLC filed Chapter 11 Subchapter V on Monday (S.D. Fla., case 26-25587; auto repair, not construction), and Monday coverage detailed lighting agency R.L. Mlazgar's November 19 Chapter 11 — a disputed $9,246,030 HLI Solutions claim dominates about $10.44M of unsecured claims. No electrical or HVAC contractor filing dated Monday was found. Ahead today after the cutoff: Case-Shiller and FHFA at 9:00 AM ET, consumer confidence at 10:00 AM; Wednesday brings PCE, GDP, new-home sales and the Beige Book."],
 "2026-11-23": [
   "Equity futures bounced on the Sunday reopen after the worst week since 2020: S&P 500 futures +1.3% just after 6:00 PM ET and about +2% later in the evening, Nasdaq-100 futures nearly +3% — against Friday's closes of S&P 500 6,910.39 (−3.70%, week −8.6%), Dow 48,147.33, Nasdaq 22,617.73. Oracle's secured OpenAI funding and Asian stabilization measures were credited; futures are not Monday's open.",
   "Oil fell on the reopen — no Hormuz premium: Sunday-evening WTI about $82.84/bbl (−0.7%) and Brent about $91.85 (−0.8%) against Friday settlements of $83.98 / $92.57, even as Hormuz transits ran 42% below prewar levels (Kpler) and 14+ tankers staged at Kharg Island with no departure confirmed.",
   "Bessent told CBS's Face the Nation the Fed 'may be making a policy mistake if they over-tighten,' and Ackman called a December hike 'another mistake' and proposed a 3% target. Sunday-evening pricing trimmed to 88.6% for a 25 bp hike, 11.4% for no change, 50 bp no longer priced. Wednesday's PCE print is the week's test; the FOMC meets Dec 8–9.",
   "AAA pump prices fell a seventh straight day: regular $3.645/gal, diesel $5.845/gal (seventh day under $6); Florida regular about $3.47, diesel about $5.59. Zillow's Sunday 30-year purchase average was unchanged from Saturday at 7.18% — the source itself notes a weekend table is not a new daily change; the refinance average was 7.44%.",
   "Bahrain said Sunday two people were injured in Saturday's facility attack (one critical) and called for UN Security Council action; the IRGC claimed Patriot targets at Al-Riffa and Awali. Central Florida price cuts eased to 1,148 in the week ending Nov 21 (average cut 3.34%, 56.79% at 60+ days), with Lake County the exception at 308, up 62.",
   "Trump said Saturday he would work with the incoming Democratic Congress on a 10% credit-card rate cap (median card rate about 22.2%; balances a record $1.29T) — a January 2027 story at the earliest, with no bill yet. Two real-estate LLCs filed Chapter 11 on Sunday; no construction-trade filing dated Sunday was found, and there was no new copper, lumber, steel, PVC or R-454B print."],
 "2026-11-22": [
   "Two more tankers were hit near Khasab in the Strait of Hormuz on Saturday (UKMTO via Reuters) — a second straight day of strikes, no casualties; Iran said a tanker hit a naval mine, which Reuters could not verify. Oil futures reopen Sunday 6:00 PM ET, so the strikes are unpriced gap risk over Friday's Brent $92.57 / WTI $83.98 settlements.",
   "AAA pump prices fell again Saturday: regular $3.6594/gal, diesel $5.8649/gal (under $6 a sixth straight day); Florida regular $3.4771, diesel $5.6049. GasBuddy projects a $3.62 Thanksgiving Day average, above the 2022 record of $3.56.",
   "Zillow's Saturday 30-year purchase average fell 15 bp to 7.18% (15-year 6.57%, refinance 7.49%) — lender-quote averages on a different basis from MND's Friday 7.33% and Freddie Mac's weekly 7.28%. No Saturday print exists for MND, Treasuries, or stocks; Friday's closes stand.",
   "Treasury Secretary Bessent's Friday pushback against a 50 bp December hike was widely reported Saturday; CME FedWatch (Friday) still prices more than 98% for a standard 25 bp hike and Citi expects 25 bp. No Fed official spoke Saturday; the October PCE index lands Wednesday, November 25.",
   "CFTC positioning (Nov 17, released Friday, analysed Saturday): managed-money copper net longs cut to 28,692 contracts from 80,000+ in late September, with $1.3B sold in the week ending November 10 — a paper washout against a still-record $495/t Yangshan physical premium.",
   "Fannie Mae's November forecast (dated Nov 12, recirculated Saturday) sees the 30-year averaging 7.2% through 2028 but cuts 2027 sales to 3.989M and starts to 1.277M; its rate inputs are as of October 30, so the rate path reads stale-low. Two further Friday construction bankruptcies were indexed Saturday (Ken's Construction Ch. 7; Ryerson Brothers Excavating Ch. 11 Sub V)."],
 "2026-11-21": [
   "Stocks entered correction on Friday: S&P 500 6,910.39 (−3.70%, seventh straight loss), Dow 48,147.33 (−1.93%), Nasdaq 22,617.73 (−5.28%, now negative for 2026); VIX 35.89 (+26.2%), its highest in 19 months. Nvidia fell 14.01% to $125.53 on a reported SEC accounting examination; Anthropic fell 8.5% to $88.91 on day two.",
   "Mortgage News Daily's daily 30-year fell 12 bp to 7.33% on Friday as Treasury par yields dropped (10-year 4.92%, −12 bp; 2-year 4.63%) — a panic bid, not a policy shift. Freddie Mac's weekly average remains 7.28%.",
   "December +25 bp pricing firmed to nearly 98% (Barron's/CME FedWatch); Governor Cook renewed her hike case Friday and Goldman Sachs expects hikes in December and March. Michigan sentiment (final) rose to 51.5 with one-year inflation expectations down to 3.7%.",
   "COMEX copper fell again: front month $5.4770/lb (−2.63%, week −9.91%, lowest settlement since March 30); December $5.496/lb, a bear market −20.2% from the September record. LME official cash copper $12,230.50/t (−2.70%).",
   "Oil rose on the day but fell a third straight week (Brent $92.57, WTI $83.98); AAA diesel held under $6 at $5.898/gal (Florida $5.65). Builder shares rose against the rout (D.R. Horton +1.91%, PulteGroup +1.76%, Lennar +1.02%).",
   "Florida unemployment fell to 4.3% in October (BLS, released Friday). An electrical contractor, All States Electric Services Corp (San Francisco), filed Chapter 7 on Friday. Markets are closed Saturday–Sunday; the October PCE index lands Wednesday, November 25."],
 "2026-11-20": [
   "Freddie Mac's weekly 30-year jumped 17 bp to 7.28% (15-year 6.66%), ending four straight weekly declines; Mortgage News Daily's daily 30-year was 7.45%.",
   "Stocks plunged a sixth straight day: S&P 500 7,175.83 (−2.02%), Dow 49,097.06 (−2.19%, first close below 50,000 since June), Nasdaq 23,879.20 (−2.25%); VIX 28.44 (+15.8%). Anthropic's record $81.3B IPO closed +17.07% at $97.17 and could not stem the rout.",
   "Initial jobless claims edged up to 203,000; continuing claims jumped 70,000 to 1.763M. The Philadelphia Fed index plunged to 6.3 (from 20.9) with prices paid at 58.2, the highest since April.",
   "COMEX copper December settled at $5.6335/lb (−0.62%) after Wednesday's rout; LME official cash copper $12,570/t (−1.41%). UBS support: $5.50/lb / $12,000/t.",
   "Treasury par yields eased on the rout (10-year 5.04%, 2-year 4.76%); December +25 bp stayed near-certain at 95.7% futures-implied, and J.P. Morgan now sees hikes at the next three meetings.",
   "Oil was flat (Brent $91.98, WTI $83.21); AAA diesel held under $6 at $5.9298/gal. Builder shares fell: Lennar −3.57%, PulteGroup −2.0%, D.R. Horton −1.18%. The SBA size-standards comment period closes today, Friday, November 20."],
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
 "2026-11-16": [
   "Kansas City Fed President Schmid said Sunday inflation is “uncomfortably above the 2% target, and moving in the wrong direction”; futures are fully priced for a 25 bp December hike (LSEG: 89% for 25 bp, 11% for 50 bp).",
   "LME copper fell a third straight session, down 1% to $13,264.50/t — its lowest in more than four months; COMEX copper near $6.02/lb.",
   "Oil eased on surplus expectations: Brent −0.49% to $95.37/bbl, WTI −0.26% to $88.33/bbl; the IEA sees a 1.7M bpd Q4 surplus.",
   "Central Florida: 1,238 listings cut prices in the week to Nov 15, averaging −3.30%, with 59.37% on the market 60+ days.",
   "UPDATE: China confirmed the first Xi–Trump–Putin trilateral for Thu Nov 19 in Shenzhen — no new tariff rates announced.",
   "No new housing data, no builder operating announcements, no HVAC / R-454B news, and no Florida OIR final order on the NCCI −7.4% filing in the window."],
 "2026-11-17": [
   "Florida OIR APPROVED the NCCI workers' comp cut on Mon Nov 16: −7.4% average for new and renewal policies effective Jan 1, 2027 — now bookable, not proposed.",
   "Stocks fell a third straight day and the Nasdaq entered correction: S&P 500 7,416.59 (−1.92%), Nasdaq 24,509.76 (−2.49%), Dow 51,608.17 (−1.41%); Nvidia −4.12% to $156.14.",
   "COMEX copper settled below $6 at $5.9975/lb (−1.35%, lowest since June 24); LME official cash copper $13,375/t (−1.73%).",
   "Mortgage News Daily 30-year at 7.51% on Monday; 10-year Treasury eased 3 bp to 5.12%. Warsh said nothing on rates; Hammack backed slow, steady hikes.",
   "Florida Realtors October: single-family sales 19,049 (−10.1% YoY), pending sales −15.7%, median $420,000 (+2.2%); condo median $290,000 (−3.3%).",
   "Oil settled down over 3% (Brent $92.44, WTI $85.72) and U.S. retail diesel fell below $6/gal for the first time since early September."],
 "2026-11-19": [
   "October starts rose 9.9% to 1.309M, but permits fell 7.4% to 1.295M and single-family permits fell 8.7% to 772,000 — the lowest since January 2023.",
   "Pending home sales hit a record low: NAR index 63.0 in October (−4.7%, −16.7% YoY); the South fell 6.3% on the month (−18.7% YoY).",
   "COMEX copper plunged −5.30% to $5.6685/lb (intraday low $5.5835), its lowest since April; LME three-month copper closed −5.7% at $12,471/t.",
   "October FOMC minutes: “almost all” officials see further hikes likely; Waller told CNBC the Fed should “go 50 in December” without a clear January signal. December +25 bp ended the day at 92.7%.",
   "Mortgage News Daily 30-year at 7.46% on Wednesday; 10-year Treasury eased 3 bp to 5.07%. MBA applications fell 2.3% with its 30-year contract rate at 7.35%.",
   "Stocks split: S&P 500 7,323.63 (−0.23%, fifth straight loss), Dow 50,198.17 (−1.11%), Nasdaq 24,429.88 (+0.42%). Oil fell (Brent $91.95, WTI $83.26) on a +3.4M-barrel EIA crude build; AAA diesel $5.96/gal."],
 "2026-11-18": [
   "Builder sentiment crashed to a 14-year low: NAHB HMI fell 4 points to 25 in November (South 27) — 46% of builders are cutting prices and 68% are offering incentives.",
   "COMEX copper slid a fourth straight session to $5.9760/lb (−0.36%, lowest since June 24); LME official cash copper $13,226/t (−1.12%).",
   "Mortgage News Daily 30-year at 7.48% on Tuesday; 10-year Treasury eased 2 bp to 5.10%. Musalem wants several hikes before spring; Williams rules out a 50 bp step — December +25 bp is priced at ~95–97%.",
   "Stocks fell a fourth straight day: S&P 500 7,340.53 (−1.03%), Nasdaq 24,328.38 (−0.74%), Dow 50,759.42 (−1.64%). Nvidia beat after the close — revenue $115.8B (+103%), Q4 guidance $130B.",
   "Retail sales rose 0.2% to $748.2B in October (ex-autos +0.6%); furniture fell 2.3%, building-material dealers rose 0.5%. Home Depot Q3 sales $43.4B (+4.9%), comps +2.2%.",
   "Oil settled slightly higher (Brent $93.14, WTI $86.01); AAA diesel held under $6 at $5.98/gal. Central Florida October closings fell 4.0% YoY with the median at $390,000 (+1.3%)."],
}
FIN_NUMBERS = {
 "2026-11-24": [("S&P 500 (Mon)", "7,237.17"), ("Nasdaq (Mon)", "24,089.56"),
   ("Nvidia (Mon)", "$165.05 +31.48%"), ("MND daily 30-yr (Mon)", "7.34%"),
   ("10-yr Treasury (Mon)", "4.92%"), ("COMEX copper (Mon)", "$5.6270/lb"),
   ("Brent crude (Mon)", "$89.37/bbl"), ("AAA diesel (Mon)", "$5.8182/gal")],
 "2026-11-23": [("S&P 500 futures (Sun eve)", "~+2%"), ("WTI crude (Sun eve)", "~$82.84/bbl"),
   ("AAA diesel (Sun)", "$5.845/gal"), ("AAA FL diesel (Sun)", "~$5.59/gal"),
   ("Zillow 30-yr purch. (Sun)", "7.18%"), ("Dec +25 bp odds (Sun eve)", "88.6%")],
 "2026-11-22": [("Zillow 30-yr purch. (Sat)", "7.18%"), ("AAA diesel (Sat)", "$5.865/gal"),
   ("AAA FL diesel (Sat)", "$5.605/gal"), ("CFTC copper net long", "28,692"),
   ("Brent crude (Fri close)", "$92.57/bbl"), ("Next FOMC", "Dec 8–9")],
 "2026-11-21": [("MND daily 30-yr (Fri)", "7.33%"), ("S&P 500 (Fri)", "6,910.39"),
   ("VIX (Fri)", "35.89"), ("COMEX copper (front)", "$5.4770/lb"),
   ("10-yr Treasury (Fri)", "4.92%"), ("Brent crude (Fri)", "$92.57/bbl")],
 "2026-11-20": [("Freddie Mac 30-yr", "7.28%"), ("MND daily 30-yr", "7.45%"),
   ("S&P 500", "7,175.83"), ("COMEX copper (Dec)", "$5.6335/lb"),
   ("10-yr Treasury", "5.04%"), ("Brent crude", "$91.98/bbl")],
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
 "2026-11-16": [("Policy rate", "3.75%–4.00%"), ("Dec 25 bp odds (LSEG)", "89%"),
   ("LME copper", "$13,264.50/t"), ("Brent crude", "$95.37/bbl"),
   ("WTI crude", "$88.33/bbl"), ("FL price cuts (wk)", "1,238")],
 "2026-11-17": [("COMEX copper", "$5.9975/lb"), ("30-yr fixed (MND)", "7.51%"),
   ("10-yr Treasury", "5.12%"), ("S&P 500", "7,416.59"),
   ("Brent crude", "$92.44/bbl"), ("FL WC cut (2027)", "−7.4%")],
 "2026-11-19": [("Housing starts (Oct)", "1.309M"), ("SF permits (Oct)", "772,000"),
   ("Pending sales idx", "63.0"), ("COMEX copper", "$5.6685/lb"),
   ("30-yr fixed (MND)", "7.46%"), ("Brent crude", "$91.95/bbl")],
 "2026-11-18": [("NAHB HMI (Nov)", "25"), ("COMEX copper", "$5.9760/lb"),
   ("30-yr fixed (MND)", "7.48%"), ("10-yr Treasury", "5.10%"),
   ("S&P 500", "7,340.53"), ("Brent crude", "$93.14/bbl")],
}
HOME_GLANCE = [
 "Legal — biggest story: the Senate clears the BAAJA permitting bill's last 60-vote hurdle (Wed Nov 18) — budget waiver 70–26, substitute adopted 69–27, final cloture 65–31 — with the passage vote still pending at the cutoff.",
 "Legal — Florida: a thin day — the First DCA nominating commission opens applications for the Tanenbaum vacancy (due Dec 2), and the new leaders firm up an affordability agenda with Amendment 3 headed to the March regular session; IRS FIRE retires today and the OSHA HazCom deadline is tomorrow.",
 "Finance — A historic reversal: Nvidia reinstated Jensen Huang as CEO on Monday, November 23 and closed +31.48% at $165.05 (about +$952B in a day), snapping a seven-session losing streak — S&P 500 +4.73% to 7,237.17, Nasdaq +6.51% to 24,089.56, Dow +3.01% to 49,595.31, VIX −25.8% to 26.62 — while Treasury yields did not move (10-year 4.92%) and mortgage money stayed put (MND 30-year 7.34%).",
 "Finance — NY Fed President Williams said inflation is 'simply too high' and 2% is '100 percent essential'; December +25 bp pricing firmed to 91.2%–95.1% with 50 bp back at 4.9%. Wednesday's October PCE print is the week's test before the Dec 8–9 FOMC; the blackout begins midnight Saturday, November 28.",
 "Finance — Oil fell to three-month lows (Brent $89.37, WTI $80.17) as Libya's Sharara pipeline restarted, and AAA diesel fell an eighth straight day to $5.8182/gal (Florida $5.5687). COMEX copper bounced +2.74% to $5.6270/lb while LME three-month fell 2.33% to $12,162.50/t; the IRGC's claim of three tankers hitting mines in Hormuz is UNVERIFIED."]

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

# ---------- story pages (per Sanjay 2026-11-15: clicking a headline or a
# photo must open a new page to read the story) ----------
STORY_PAGES = {}   # docs-relative path -> (title, body)
_STORY_KEYS = {}   # (section, date, headline) -> path
_USED_SLUGS = set()

def slugify(text):
    t = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (t[:64].rstrip("-") or "story")

def story_paths_for(section, date, kind=None):
    out = []
    for (sec, d, h), (p, kd) in _STORY_KEYS.items():
        if sec == section and d == date and (kind is None or kd == kind):
            out.append(p)
    return out

def story_page(ctx, headline, deck, impact, photo_entry, rest_html, deck_html="", kind="item"):
    """Register a standalone story page; return its docs-relative path."""
    k = (ctx["section"], ctx["date"], headline)
    if k in _STORY_KEYS:
        path = _STORY_KEYS[k][0]
    else:
        base = slugify(headline)
        slug, n = base, 2
        while (ctx["section"], ctx["date"], slug) in _USED_SLUGS:
            slug = f"{base}-{n}"; n += 1
        _USED_SLUGS.add((ctx["section"], ctx["date"], slug))
        path = f'{ctx["section"]}/story/{ctx["date"]}-{slug}.html'
        _STORY_KEYS[k] = (path, kind)
    imp = f'<p class="impact"><b>Why it matters to Sharma:</b> {impact}</p>' if impact else ""
    deck_h = deck_html or (f'<p class="deck">{deck}</p>' if deck else "")
    body = (f'<p class="crumb"><a href="../../{ctx["sec_home"]}">&larr; {ctx["sec_label"]}</a> &middot; '
            f'<a href="../../{ctx["section"]}/archive/{ctx["date"]}.html">Edition of {ctx["date"]}</a></p>'
            f'<span class="kicker">{ctx["sec_label"]} &middot; {ctx["date_label"]}</span>'
            f'<h1 class="storyhead">{headline}</h1>'
            f'{photo_html(photo_entry, "../../")}{deck_h}{imp}'
            f'<div class="fullbody">{rest_html}</div>'
            f'<p class="totop"><a href="../../{ctx["sec_home"]}">&larr; Back to the {ctx["sec_label"]}</a></p>')
    STORY_PAGES[path] = (headline, body, ctx["section"])
    return path

ITEM_SPLIT = r'(<h3>.*?</h3>|<p><strong>Item\s+\d+[A-Z]?\s*—.*?</strong></p>)'


def render_section_body(body, ctx=None):
    parts = re.split(ITEM_SPLIT, body, flags=re.S)
    intro, items = parts[0], []
    for i in range(1, len(parts), 2):
        marker = parts[i]
        rest = parts[i + 1] if i + 1 < len(parts) else ""
        items.append((marker, marker + rest))
    if not items:
        if len(strip_tags(body)) > 700:
            deck = excerpt(strip_tags(body), 230)
            if ctx:
                path = story_page(ctx, ctx.get("sec_title") or "Section in full",
                                  deck, "", None, body, kind="section")
                href = f'{ctx["prefix"]}{path}'
                return (f'<div class="item"><p class="deck">{deck}</p>'
                        f'<a class="cont" href="{href}">Read this section in full &rarr;</a></div>')
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
        if ctx:
            rest = block[len(marker):]
            path = story_page(ctx, headline, deck, impact, None, rest)
            href = f'{ctx["prefix"]}{path}'
            out.append(
                f'<div class="item"><h3 class="item-head"><a href="{href}">{headline}</a></h3>'
                f'<p class="deck">{deck}</p>{imp}'
                f'<a class="cont" href="{href}">Read the full story &rarr;</a></div>')
        else:
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
        title = plain_heading(strip_tags(heading))
        if not strip_tags(body):
            rendered.append(f'<p class="windowline">{title}</p>')
            continue
        sec_no += 1
        sid = f"sec-{sec_no}"
        nav_items.append(f'<a href="#{sid}">{title}</a>')
        fctx = {"section": "finance", "date": date, "date_label": FIN[date][1],
                "sec_label": "Finance Briefing", "sec_home": "finance/index.html",
                "prefix": prefix, "sec_title": title}
        rendered.append(f'<h2 id="{sid}">{title}</h2>' + render_section_body(body, fctx))
        if not inline_placed and imgs.get("inline"):
            inl = photo_html(imgs["inline"], prefix, "small")
            paths = story_paths_for("finance", date, "item") or story_paths_for("finance", date)
            if inl and paths:
                inl = f'<a class="photolink" href="{prefix}{paths[0]}">{inl}</a>'
            rendered.append(inl)
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
        lead = photo_html(imgs["lead"], prefix)
        paths = story_paths_for("finance", date, "item") or story_paths_for("finance", date)
        if lead and paths:
            lead = f'<a class="photolink" href="{prefix}{paths[0]}">{lead}</a>'
        top += lead
    return (preamble + nav + top + "\n".join(rendered) +
            '<p class="totop"><a href="#top">Back to top ↑</a></p>')

FIN = {  # date -> (report glob, weekday label, archive one-liner)
 "2026-11-24": ("sharma-daily-finance-news-2026-11-24-*", "Tuesday, November 24, 2026",
   "A historic reversal driven by one company: Nvidia reinstated Jensen Huang as CEO 12 days after his resignation and the stock closed +31.48% at $165.05 (about +$952B in a day), snapping a seven-session losing streak — S&P 500 +4.73% to 7,237.17, Nasdaq +6.51% to 24,089.56, Dow +3.01% to 49,595.31, VIX −25.8% to 26.62 — while Treasury par yields did not move (10-year 4.92%, 2-year 4.63%) and mortgage money stayed put (MND 30-year 7.34%, Zillow purchase 7.18%). Williams (NY Fed) said inflation is 'simply too high' and 2% is '100 percent essential'; December +25 bp pricing firmed to 91.2%–95.1% with 50 bp back at 4.9%. COMEX copper bounced +2.74% to $5.6270/lb while LME three-month fell 2.33% to $12,162.50/t; lumber settled at $541.00. Oil fell to three-month lows (Brent $89.37, WTI $80.17) as Libya's Sharara restarted; AAA diesel fell an eighth day to $5.8182/gal (Florida $5.5687). IRGC's claim of three tankers hitting mines in Hormuz is UNVERIFIED. Builders rose only ~1.3% (DHI $147.24, LEN $81.90, PHM $126.35)."),
 "2026-11-23": ("sharma-daily-finance-news-2026-11-23-*", "Monday, November 23, 2026",
   "A closed-market Sunday with a live futures reopen: S&P 500 futures rose about 2% Sunday evening (Nasdaq-100 nearly +3%) after the worst week since 2020 (S&P 500 −8.6% to 6,910.39), while oil fell on the reopen — WTI about $82.84, Brent about $91.85 — pricing no Hormuz premium despite two days of tanker strikes, Bahrain reporting two injured in Saturday's facility attack, and 14+ tankers staged at Kharg with no departure confirmed. Bessent (CBS) warned the Fed 'may be making a policy mistake if they over-tighten' and Ackman called a December hike 'another mistake'; Sunday-evening pricing trimmed to 88.6% for +25 bp with 50 bp off the board. AAA diesel fell to $5.845/gal (Florida about $5.59), a seventh day under $6; Zillow's Sunday 30-year purchase average was unchanged at 7.18%. Trump revived a 10% credit-card cap with the incoming Democratic Congress; Central Florida price cuts eased to 1,148. Wednesday's PCE print is the week's test."),
 "2026-11-22": ("sharma-daily-finance-news-2026-11-22-*", "Sunday, November 22, 2026",
   "A closed-market Saturday whose one hard news event was geopolitical: two more tankers were hit near Khasab in the Strait of Hormuz (UKMTO via Reuters) — a second straight day of strikes — putting Sunday's 6:00 PM ET futures reopen at gap risk after oil's third straight weekly loss (Brent $92.57 Fri). Zillow's Saturday 30-year purchase average fell 15 bp to 7.18% (a lender-quote average, not MND); AAA diesel fell to $5.865/gal (Florida $5.605). Treasury Secretary Bessent's Friday pushback against a 50 bp December hike was widely reported Saturday, and CFTC data showed managed-money copper net longs cut to 28,692 contracts (Nov 17) from 80,000+ in September. Friday's closes stand: S&P 500 6,910.39, COMEX copper $5.4770/lb."),
 "2026-11-21": ("sharma-daily-finance-news-2026-11-21-*", "Saturday, November 21, 2026",
   "Friday's rout put stocks in correction: S&P 500 −3.70% to 6,910.39 (seventh straight loss, −8.6% on the week), Dow −1.93% to 48,147.33, Nasdaq −5.28% to 22,617.73 and negative for 2026; VIX 35.89 (+26.2%). Nvidia fell 14.01% to $125.53 on a reported SEC accounting examination and Anthropic fell 8.5% to $88.91 on day two. The daily 30-year mortgage rate fell 12 bp to 7.33% as the 10-year Treasury fell 12 bp to 4.92% — a panic bid, while December +25 bp pricing firmed to nearly 98%. COMEX copper fell to $5.4770/lb (week −9.91%), LME cash $12,230.50/t; oil rose on the day but fell a third straight week (Brent $92.57, WTI $83.98); AAA diesel $5.898/gal. Florida unemployment fell to 4.3% in October."),
 "2026-11-20": ("sharma-daily-finance-news-2026-11-20-*", "Friday, November 20, 2026",
   "Freddie Mac's weekly 30-year jumped 17 bp to 7.28%, ending four straight weekly declines, as stocks plunged a sixth straight day — S&P 500 −2.02% to 7,175.83, Dow −2.19% to 49,097.06 (first close below 50,000 since June), Nasdaq −2.25% — and Anthropic's record $81.3B IPO (closed $97.17, +17.07%) failed to stem the rout. Jobless claims edged up to 203,000 with continuing claims +70,000 to 1.763M; the Philadelphia Fed index plunged to 6.3 with prices paid at 58.2. COMEX copper steadied at $5.6335/lb (−0.62%), LME cash $12,570/t; the 10-year Treasury eased to 5.04% and oil was flat (Brent $91.98, WTI $83.21); AAA diesel $5.9298/gal."),
 "2026-11-19": ("sharma-daily-finance-news-2026-11-19-*", "Thursday, November 19, 2026",
   "October starts rose 9.9% to 1.309M but permits fell 7.4% to 1.295M — single-family permits 772,000, the lowest since January 2023 — and pending home sales hit a record-low 63.0 (South −6.3%). COMEX copper plunged 5.30% to $5.6685/lb, its lowest since April, as the October FOMC minutes showed “almost all” officials expecting further hikes and Waller called to “go 50 in December.” The daily 30-year mortgage rate eased to 7.46% and the 10-year Treasury to 5.07%; stocks split (S&P 500 −0.23% to 7,323.63, Dow −1.11%, Nasdaq +0.42%). Oil fell on a +3.4M-barrel EIA build (Brent $91.95, WTI $83.26); AAA diesel $5.96/gal. Lowe's Q3 sales were $22.76B (+9.3%) with $0.34 of its $3.10 adjusted EPS from $250M in tariff refunds."),
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
 "2026-11-16": ("sharma-daily-finance-news-2026-11-16-*", "Monday, November 16, 2026",
   "A Sunday window with three real moves: KC Fed President Schmid called inflation “uncomfortably above the 2% target, and moving in the wrong direction” with a December hike fully priced (89% for 25 bp, 11% for 50 bp); LME copper fell a third straight session to $13,264.50/t, its lowest in over four months; oil eased on a forecast 1.7M bpd Q4 surplus. Plus 1,238 Central Florida price cuts and China's confirmation of the Nov 19 Xi–Trump–Putin trilateral — no new tariff rates."),
 "2026-11-17": ("sharma-daily-finance-news-2026-11-17-*", "Tuesday, November 17, 2026",
   "Florida OIR approved the NCCI workers' comp cut (−7.4% average, effective Jan 1, 2027) on Mon Nov 16. Stocks fell a third straight day — S&P 500 −1.92% to 7,416.59, Nasdaq −2.49% and in correction — and COMEX copper settled below $6 at $5.9975/lb, its lowest since June 24. Florida Realtors October: single-family sales −10.1% YoY to 19,049, pending sales −15.7%, median $420,000 (+2.2%). Oil settled down over 3% (Brent $92.44, WTI $85.72); the daily 30-year mortgage rate was 7.51%."),
 "2026-11-18": ("sharma-daily-finance-news-2026-11-18-*", "Wednesday, November 18, 2026",
   "Builder sentiment crashed to a 14-year low — NAHB HMI 25 in November (South 27), with 46% of builders cutting prices — as stocks fell a fourth straight day (S&P 500 −1.03% to 7,340.53, its lowest close since late July) and COMEX copper slid a fourth session to $5.9760/lb. The daily 30-year mortgage rate eased to 7.48% and the 10-year Treasury to 5.10%; October retail sales rose 0.2% to $748.2B. Nvidia beat after the close (revenue $115.8B, +103%; Q4 guidance $130B) and Home Depot posted Q3 sales of $43.4B (+4.9%). Oil settled slightly higher (Brent $93.14, WTI $86.01); AAA diesel held under $6 at $5.98/gal."),
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
 "2026-11-16": ("Monday, November 16, 2026",
   "Biggest story: the Justice Department's Sunday, Nov 15 letter warning Sen. Elizabeth Warren to preserve records over her planned Trump investigations, citing \"significant legal consequences\" — plus the Florida Overton case reaching SCOTUS and an electrical contractor's Chapter 11 hearing today."),
 "2026-11-17": ("Tuesday, November 17, 2026",
   "Biggest story: California sues OpenAI (Mon Nov 16) over rogue AI-agent cyberattacks — the first state suit over the Hugging Face breach — plus the $38B Visa/Mastercard swipe-fee hearing, the Senate's 70–27 permitting-bill vote, and the DOL PERM overhaul proposal."),
 "2026-11-18": ("Wednesday, November 18, 2026",
   "Biggest story: Oregon sues OpenAI (Tue Nov 17) over ChatGPT child safety — AG Rayfield seeks at least $2.035 billion — plus Florida's new legislative leaders taking power and declining DeSantis's Amendment 3 special-session timeline, the St. John Fifth Circuit confirmation (52–46), and the PERM comment deadline fixed at Jan 19, 2027."),
 "2026-11-19": ("Thursday, November 19, 2026",
   "Biggest story: the Senate clears the BAAJA permitting bill's last 60-vote hurdle on Wed Nov 18 — budget waiver 70–26, Capito substitute adopted 69–27, final cloture 65–31 — with passage still pending at the cutoff; plus the Fourth Circuit's Tax Court deadline ruling, the MIT brothers' MEV acquittal (Mon Nov 16), the Eleventh Circuit's I-220A ruling (Tue Nov 17), and deadline reminders: IRS FIRE retires today, OSHA HazCom tomorrow."),
 "2026-11-20": ("Friday, November 20, 2026",
   "Biggest story: the Senate passes the BAAJA permitting bill 62–33 on Thu Nov 19 and sends it to the House; plus DOL's final independent-contractor rule (control + profit/loss test), the GSA/DHS E-Verify sweep of 1,579 federal contractors (proof due Dec 16), Florida's record 20th execution (Overton, after SCOTUS denied the stay), Judge Merryday letting Trump's $15B defamation case proceed in narrowed form, and the OSHA HazCom substances deadline today."),
 "2026-11-21": ("Saturday, November 21, 2026",
   "Biggest story: the Fifth Circuit rules 9–8 on Fri Nov 20 that the House unconstitutionally passed the 2022 $1.7T spending bill by proxy voting (Quorum Clause), upholding an injunction barring PWFA enforcement against Texas; plus a new executive order flowing congressional-request duties down to federal subcontractors, FTC + 30 states vs. Dollar General (Florida already a plaintiff), MasTec's $1.25B Murphy acquisition, the DOL contractor rule's fixed dates (publishes Nov 23, effective Jan 22, 2027), and the OSHA HazCom substances deadline passing on Nov 20."),
 "2026-11-22": ("Sunday, November 22, 2026",
   "Biggest story: a thin Saturday — a Missouri judge gives final approval on Fri Nov 20 to Bayer's $7.25B Roundup settlement (reported Sat Nov 21); plus Florida AG Uthmeier's FDUTPA suit against The Leapfrog Group over hospital safety grades, the flood emergency (EO 26-232) covering 21 counties including Brevard, Lake and Seminole through Jan 1, 2027, and a Saturday Chapter 11 filing by lender Oxygen Funding."),
 "2026-11-23": ("Monday, November 23, 2026",
   "Biggest story: a thin Sunday — the Army says it will bypass a court order and detonate 68 barrels of toxic lead azide in Iowa by Tuesday, Nov 24, invoking emergency powers after the Eighth Circuit froze its permit; plus confirmation that Friday's federal-contractor order is Executive Order 14438, a federal judge blocking Connecticut's ICE mask ban (Fri Nov 20, late-located), and three watch items landing today: the DOL contractor rule's Federal Register publication, the Supreme Court's Monday orders list, and the Tasty Chick'n lease-rejection hearing."),
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
        shell("../../", f"Finance Briefing — {label}", body, active="finance"), encoding="utf-8")

latest = "2026-11-24"
body = (f'<p class="crumb"><span class="kicker">Finance Briefing · Latest Edition</span></p>'
        f'<article>{render_article(fin_report(latest), latest, "../")}</article>')
(DOCS / "finance" / "index.html").write_text(
    shell("../", f"Finance Briefing — {FIN[latest][1]}", body, active="finance"), encoding="utf-8")

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
    shell("../../", "Finance Briefing Archive", body, active="finance"), encoding="utf-8")

# ---------- TECH: construction / engineering / tech news ----------
# Parallel structure to FIN. The Product Spotlight refreshes every
# WEEKDAY (per Sanjay): fresh picks Mon–Fri, weekends carry Friday's.
# Display labels therefore say "Spotlight" even where a report draft
# said "product of the day".
TECH = {  # date -> (report glob, weekday label, archive one-liner)
 "2026-11-15": ("sharma-tech-news-2026-11-15-*", "Sunday, November 15, 2026",
   "Construction input costs jumped 13.3% year-over-year — copper wire & cable up 25.5% — while contractors' selling prices rose only 5.5%. Inaugural Product Spotlight: Leviton Lever Edge USB outlets (electrical) and Bosch YORK YD heat pumps (HVAC)."),
 "2026-11-16": ("sharma-tech-news-2026-11-16-*", "Monday, November 16, 2026",
   "Update: after the Brooklyn collapse, cracks at a Chinatown senior complex spark a call to halt jail construction next door; in Florida, GL Homes turns two Palm Beach County golf courses into housing under the new Infill Redevelopment Act. Product Spotlight (new today): Soneil Spark Mobile BESS (electrical) and Rinnai REHPW heat pump water heaters (HVAC)."),
 "2026-11-17": ("sharma-tech-news-2026-11-17-*", "Tuesday, November 17, 2026",
   "Florida existing single-family sales fell 10.1% in October to 19,049 with new pending sales down 15.7% (Florida Realtors, Nov 16); Caterpillar makes collision warning and mitigation standard on most new machines in 2027. Product Spotlight (new today): CMP Products Fortra cable glands (electrical) and Carrier Smart Thermostat with InteliSense (HVAC)."),
 "2026-11-18": ("sharma-tech-news-2026-11-18-*", "Wednesday, November 18, 2026",
   "Builder confidence fell four points to 25 in November — the lowest since April 2012 (NAHB, Nov 17) — with 46% of builders cutting prices; in Florida, Lee County awarded a $47.1M Alico Road contract. Product Spotlight (new today): GE Vernova HYpact-145g SF6-free switchgear (electrical) and Carrier ClimaVision 3-MyStat Pro Pack (HVAC)."),
 "2026-11-19": ("sharma-tech-news-2026-11-19-*", "Thursday, November 19, 2026",
   "October starts rose 9.9% to 1.309M but permits fell 7.4% to 1.295M — single-family permits down 8.7% to 772,000, the lowest since January 2023 (Census/HUD, Nov 18); Suffolk completed Gilead's research center on a four-tool contech stack, and WWE proposed a $100M Performance Center in downtown Orlando. Product Spotlight (new today): Enphase IQ Bidirectional EV Charger (electrical) and Bosch GoTemp Home + GoTemp Pro Remote Support (HVAC)."),
 "2026-11-20": ("sharma-tech-news-2026-11-20-*", "Friday, November 20, 2026",
   "Both tubes of the $16B Hudson Tunnel are now under construction (second TBM launched, GDC Nov 18); NYC orders the Flatbush-collapse-damaged 1323 Flatbush demolished, and EarthCam launches a 50+ app marketplace. In Florida, SECO Energy builds three Central Florida facilities with DPR and a jury convicts two men in an $8.9M VA contract fraud. Product Spotlight (new today): Resideo First Alert CX6T AI Camera + Resideo One (electrical) and Viessmann Vitocal 300-G intelligent energy (HVAC)."),
 "2026-11-21": ("sharma-tech-news-2026-11-21-*", "Saturday, November 21, 2026",
   "October construction starts rebounded 22.8% to $1.63T but excluding manufacturing they fell 1.1% (Dodge, Nov 20); the Senate passed the BAAJA permitting overhaul 62-33, and Coral Gables-based MasTec agreed to buy mechanical contractor Murphy for about $1.25B. In Florida, Fort Meade's 4.4M sq. ft. data center goes back for a fresh city vote and World Electric Supply leases 274,040 sq. ft. in Lakeland. Product Spotlight (carried from Friday): Resideo First Alert CX6T AI Camera + Resideo One (electrical) and Viessmann Vitocal 300-G intelligent energy (HVAC)."),
 "2026-11-22": ("sharma-tech-news-2026-11-22-*", "Sunday, November 22, 2026",
   "Ohio approved 2,150 MW of behind-the-meter gas plants built only for data centers (OPSB, Nov 19), and RMI research finds winter grid headroom could carry heat pumps into about 109 million homes. In Florida, Tampa's $1.528B Airside D moves toward MEP fit-out, Sarasota's 20-story 1000 Boulevard of the Arts is underway with Moss, and a 55-story Miami Edgewater tower won final approval. Product Spotlight (carried from Friday): Resideo First Alert CX6T AI Camera + Resideo One (electrical) and Viessmann Vitocal 300-G intelligent energy (HVAC)."),
 "2026-11-23": ("sharma-tech-news-2026-11-23-*", "Monday, November 23, 2026",
   "A Nov 20 executive order requires federal contractors and subcontractors to notify the White House of congressional inquiries, with termination or debarment among the penalties (ENR, Nov 22); ACHR News reports HVAC acquisition multiples have fallen from their 2021–2023 highs. In Florida, a 25-story Live Local Act tower is planned in West Palm Beach and Gateway Jax opened the 205-unit Vandeveer in Jacksonville. Product Spotlight (new today): Voltage Energy Microgrid System + LBD/CBX (electrical) and Moovair Mistral heat pump line via VAD (HVAC)."),
 "2026-11-24": ("sharma-tech-news-2026-11-24-*", "Tuesday, November 24, 2026",
   "Data center cancellations in Q3 more than doubled — 16 projects stopped, about $64 billion in planned investment, 11 of them stopped by local governments (Relae via Construction Dive, Nov 23); OSHA proposed $1.59M in penalties after a crane load contacted a 34.5-kV line, and heat pump adoption in new homes climbed to about 48% (Ekotrope via ACHR News). In Florida, Florida Polytechnic's 601-bed Lakeland residence hall was approved and a $150M permit was issued for Miami's 42-story 1775 Biscayne. Product Spotlight (new today): Briggs & Stratton SimpliPHI 16 battery (electrical) and ECO2 Systems Sanco 40kW heat pump (HVAC)."),
}
TECH_IMAGES = {  # photos pulled from the articles the report cites
 "2026-11-24": {
  "lead": ("tech-2026-11-24-lead.webp", "People protesting AI data centers at City Hall Park, New York City, October 5, 2026",
    "People protest AI data centers at City Hall Park in New York City on Oct 5, 2026 — U.S. data center cancellations more than doubled in Q3 2026, with 16 projects stopped and 11 of them stopped directly by local governments.",
    "Photo: Michael M. Santiago via Getty Images via Construction Dive"),
  "inline": ("tech-2026-11-24-inline.jpg", "Rendering of 1775 Biscayne, a 42-story tower in Miami",
    "Rendering of 1775 Biscayne in Miami — a $150 million construction permit was issued Nov 19 for the 42-story, 544-unit tower.",
    "Photo: AIMIR CG via Florida YIMBY"),
 },
 "2026-11-23": {
  "lead": ("tech-2026-11-23-lead.webp", "Collage of White House construction, the Reflecting Pool, the Kennedy Center and a proposed arch",
    "Collage of White House construction, the Reflecting Pool and the Kennedy Center — a Nov 20 executive order requires federal contractors and subcontractors to notify the White House of congressional inquiries about their government work.",
    "Photo: ENR"),
  "inline": ("tech-2026-11-23-inline.jpg", "Rendering of the proposed 25-story tower at 215 5th Street, West Palm Beach",
    "The proposed 25-story, 91-residence tower at 215 5th Street in West Palm Beach, planned under Florida's Live Local Act.",
    "Photo: Florida YIMBY"),
 },
 "2026-11-22": {
  "lead": ("tech-2026-11-22-lead.png", "Residents at the August 17 public meeting in Millersport, Ohio, on the Vantage data center gas plant",
    "Residents at the Aug 17 public meeting in Millersport, Ohio — the state Power Siting Board on Nov 19 approved the 1,350 MW behind-the-meter gas plant for Vantage's data center campus, plus an 800 MW plant for EdgeConneX.",
    "Photo: Jake Zuckerman via Signal Ohio"),
  "inline": ("tech-2026-11-22-inline.jpg", "An exterior heat pump installation",
    "An exterior heat pump installation — RMI research estimates about 109 million U.S. homes could use heat pumps within existing winter grid headroom.",
    "Photo: Nate Adams via ACHR News"),
 },
 "2026-11-21": {
  "lead": ("tech-2026-11-21-lead.webp", "Groundbreaking ceremony for the Ohio River Tunnel project in Pittsburgh, October 22, 2026",
    "Groundbreaking for the Ohio River Tunnel project in Pittsburgh on Oct 22, 2026 — at $1.1 billion, one of October's largest groundbreakings in a month when total starts rebounded 22.8% on Tesla's $16.8 billion Texas chip plant.",
    "Photo: Lane Construction via Construction Dive"),
  "inline": ("tech-2026-11-21-inline.webp", "MasTec to acquire Murphy Corporation",
    "MasTec, headquartered in Coral Gables, Florida, has agreed to acquire St. Louis mechanical contractor Murphy Corporation for about $1.25 billion in cash, announced Nov 20, 2026.",
    "Photo: MasTec, Yuttana Studio / Adobe Stock via ACHR News"),
 },
 "2026-11-20": {
  "lead": ("tech-2026-11-20-lead.webp", "Tunnel boring machines assembling the Hudson Tunnel tubes in North Bergen, New Jersey",
    "Tunnel boring machine assembly for the Hudson Tunnel Project in North Bergen, New Jersey — the second machine has launched into the southern tube, putting both $16 billion tubes under construction.",
    "Photo: Gateway Development Commission via Construction Dive"),
  "inline": ("tech-2026-11-20-inline.webp", "Luve ribbon-cutting at its expanded Jacksonville, Texas plant",
    "Luve's ribbon-cutting at its Jacksonville, Texas plant — a roughly 215,000 sq. ft. expansion, to just over 320,000 sq. ft., mainly to build outdoor cooling products for data centers.",
    "Photo: Luve via ACHR News"),
 },
 "2026-11-19": {
  "lead": ("tech-2026-11-19-lead.webp", "Gilead Sciences' new research center in Foster City, California",
    "Gilead Sciences' new research center in Foster City, California — Suffolk completed the build leaning on OpenSpace, Dusty Robotics, Kaya AI and Alice Technologies.",
    "Photo: Suffolk Construction via Construction Dive"),
  "inline": ("tech-2026-11-19-inline.webp", "Construction crews work on the Portal North Bridge over the Hackensack River",
    "Construction crews work on the Portal North Bridge — the Skanska–Traylor Bros JV has delivered the $1.6 billion, 2.4-mile fixed span, replacing a 116-year-old swing bridge.",
    "Photo: Skanska via Construction Dive"),
 },
 "2026-11-18": {
  "lead": ("tech-2026-11-18-lead.webp", "Port Authority stakeholders at a groundbreaking ceremony at Newark Liberty International Airport",
    "Port Authority stakeholders at the Oct 7, 2025 groundbreaking at Newark Liberty International Airport — the authority's proposed $10.3 billion 2027 budget, with $4 billion in capital spending, was reported Nov 17.",
    "Photo: Port Authority of New York and New Jersey via Construction Dive"),
  "inline": ("tech-2026-11-18-inline.png", "New York City",
    "New York City — a city safety-training provider has been indicted for allegedly selling Site Safety Training and OSHA cards with no training; about 2,000 of its cards have been invalidated.",
    "Photo: NRCA"),
 },
 "2026-11-17": {
  "lead": ("tech-2026-11-17-lead.jpg", "Florida home sales, October 2026",
    "Florida single-family home sales fell 10.1% in October to 19,049, with new pending sales down 15.7% — Florida Realtors data released Nov 16.",
    "Photo: RealtyWire"),
  "inline": ("tech-2026-11-17-inline.png", "City-approved excavation plan beside 1321 Flatbush Ave, Brooklyn",
    "The city-approved excavation plan for the lot beside 1321 Flatbush Ave — engineers say the collapsed building's side was the one place no added bracing was required.",
    "Photo: Department of Buildings via Gothamist"),
 },
 "2026-11-16": {
  "lead": ("tech-2026-11-16-lead.jpg", "Apple Home Collection accessories co-developed with LG and Schneider",
    "Apple Home Collection accessories, co-developed with LG and Schneider Electric — pre-orders opened Fri Nov 13, with the first products launching in December.",
    "Photo: 9to5Mac"),
 },
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
 "2026-11-24": {
  "2.1": ("tech-simpliphi.jpg", "Briggs & Stratton SimpliPHI 16 energy storage battery",
    "The Briggs & Stratton SimpliPHI 16 — a 16 kWh LFP battery that scales to 512 kWh, with an integrated BMS, built-in Wi-Fi gateway and automatic inverter detection. Introduced Nov 20, 2026; available for pre-order, price not disclosed.",
    "Photo: Briggs & Stratton via pv magazine USA"),
  "2.2": ("tech-sanco.webp", "ECO2 Systems Sanco 40kW heat pump for commercial hot water",
    "The ECO2 Systems Sanco 40kW — a 40 kW air-to-water heat pump for commercial hot water using natural CO2 (R744) refrigerant, at a COP of 5.0. Unveiled Nov 24, 2026; approaching launch, no price or availability date specified.",
    "Photo: ECO2 Systems via pv magazine"),
 },
 "2026-11-23": {
  "2.1": ("tech-voltage.jpg", "Voltage Energy Group products",
    "Voltage Energy Group — its Microgrid System (MGS) combines solar and battery storage in a pre-wired modular skid, unveiled Nov 17, 2026 at RE+ alongside the new LBD disconnect box and CBX combiner box.",
    "Photo: Voltage Energy Group via PR Newswire"),
  "2.2": ("tech-mistral.jpg", "Moovair Mistral heat pump outdoor unit",
    "The Moovair Mistral outdoor unit — a ductless heat pump line launched in the U.S. by VAD on Nov 17, 2026, rated up to 25.8 SEER2 with heating down to -13 °F.",
    "Photo: AC Pro Site"),
 },
 "2026-11-22": {  # weekend edition: Friday's pair carried forward unchanged
  "2.2": ("tech-vitocal.jpg", "Viessmann Vitocal 300-G intelligent energy ground-source heat pump",
    "The Viessmann Vitocal 300-G intelligent energy — an indoor ground-source heat pump on R290 (propane), 6–16 kW, SCOP up to 5.5, with the One Base Intelligence control platform. Announced Nov 2, 2026; deliveries begin Nov 30, 2026.",
    "Photo: Viessmann via Cooling Post"),
 },
 "2026-11-21": {  # weekend edition: Friday's pair carried forward unchanged
  "2.2": ("tech-vitocal.jpg", "Viessmann Vitocal 300-G intelligent energy ground-source heat pump",
    "The Viessmann Vitocal 300-G intelligent energy — an indoor ground-source heat pump on R290 (propane), 6–16 kW, SCOP up to 5.5, with the One Base Intelligence control platform. Announced Nov 2, 2026; deliveries begin Nov 30, 2026.",
    "Photo: Viessmann via Cooling Post"),
 },
 "2026-11-20": {
  "2.2": ("tech-vitocal.jpg", "Viessmann Vitocal 300-G intelligent energy ground-source heat pump",
    "The Viessmann Vitocal 300-G intelligent energy — an indoor ground-source heat pump on R290 (propane), 6–16 kW, SCOP up to 5.5, with the One Base Intelligence control platform. Announced Nov 2, 2026; deliveries begin Nov 30, 2026.",
    "Photo: Viessmann via Cooling Post"),
 },
 "2026-11-19": {
  "2.2": ("tech-gotemp.webp", "Bosch GoTemp Pro app on a phone",
    "The GoTemp Pro contractor app — its new Remote Support feature lets an on-site tech share live system data by Bluetooth with remote support for troubleshooting. The GoTemp Home homeowner app launched alongside it.",
    "Photo: Bosch Home Comfort Group via ACHR News"),
 },
 "2026-11-18": {
  "2.1": ("tech-gevernova.jpg", "GE Vernova HYpact-145g compact hybrid switchgear",
    "A rendering of GE Vernova's HYpact-145g — a 145 kV, 40 kA SF6-free hybrid switchgear using g3 gas, at least 50% smaller than a conventional air-insulated substation.",
    "Photo: GE Vernova"),
  "2.2": ("tech-climavision.png", "Carrier ClimaVision MyStat v2 IAQ sensor",
    "Carrier's ClimaVision MyStat v2 IAQ sensor — part of the ClimaVision 3-MyStat Pro Pack, which packages Carrier rooftop equipment with 75F controls, cloud technology and AI for light commercial buildings.",
    "Photo: Carrier"),
 },
 "2026-11-17": {
  "2.1": ("tech-fortra.jpg", "CMP Products Fortra cable gland",
    "A CMP Fortra cable gland — the next-generation range is built for fast installation with secure, inspectable terminations.",
    "Photo: CMP Products via Electrical Times"),
 },
 "2026-11-16": {
  "2.1": ("tech-soneil.jpg", "Soneil Spark Mobile BESS trailer",
    "The Soneil Spark Mobile BESS — battery storage and controls in a towable trailer, ready to connect on site.",
    "Photo: Soneil Spark via PR Newswire"),
  "2.2": ("tech-rinnai.jpg", "Rinnai REHPW heat pump water heater",
    "A Rinnai REHPW heat pump water heater — 50/65/80-gallon models at UEF 3.75–4.0, with Wi-Fi and demand-response certification.",
    "Photo: Rinnai via Electrek"),
 },
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
        kick = ("Electrical Spotlight" if "⚡" in headline
                else "HVAC Spotlight" if "❄" in headline
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
        head2 = headline.replace("PRODUCT OF THE DAY", "SPOTLIGHT")
        rest = full[len(marker.replace("PRODUCT OF THE DAY", "SPOTLIGHT")):] \
            if full.startswith(marker.replace("PRODUCT OF THE DAY", "SPOTLIGHT")) else full
        tctx = {"section": "tech", "date": date, "date_label": TECH[date][1],
                "sec_label": "Tech Briefing", "sec_home": "tech/index.html",
                "prefix": prefix, "sec_title": "Product Spotlight"}
        path = story_page(tctx, head2, "", "", entry, rest, deck_html=(ml + deck), kind="spotlight")
        href = f'{prefix}{path}'
        photo = photo_html(entry, prefix)
        if photo:
            photo = f'<a class="photolink" href="{href}">{photo}</a>'
        out.append(
            f'<div class="spotlight"><span class="kicker">{kick}</span>'
            f'<h3 class="item-head"><a href="{href}">{head2}</a></h3>'
            f'{photo}{ml}{deck}'
            f'<a class="cont" href="{href}">Read the full story &rarr;</a></div>')
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
        title = plain_heading(strip_tags(heading))
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
        nav_items.append('<a href="#spotlight">Product Spotlight</a>')
    sec_no = 0
    for title, body in generic:
        sec_no += 1
        sid = f"sec-{sec_no}"
        nav_items.append(f'<a href="#{sid}">{title}</a>')
        block = f'<h2 id="{sid}">{title}</h2>'
        if sec_no == 1 and imgs.get("lead"):
            block += (f'<a class="photolink" href="@@FIRSTSTORY@@">'
                      f'{photo_html(imgs["lead"], prefix)}</a>')
        tctx = {"section": "tech", "date": date, "date_label": TECH[date][1],
                "sec_label": "Tech Briefing", "sec_home": "tech/index.html",
                "prefix": prefix, "sec_title": title}
        block += render_section_body(body, tctx)
        if sec_no == 1 and imgs.get("inline"):
            inl = photo_html(imgs["inline"], prefix, "small")
            paths = story_paths_for("tech", date, "item") or story_paths_for("tech", date)
            if inl and paths:
                pick = paths[1] if len(paths) > 1 else paths[0]
                inl = f'<a class="photolink" href="{prefix}{pick}">{inl}</a>'
            block += inl
        rendered.append(block)
    nav = f'<nav class="jump">{"".join(nav_items)}</nav>' if nav_items else ""
    spot = ""
    if spotlight:
        spot = ('<h2 id="spotlight">Product Spotlight</h2>'
                '<p class="sec-intro">A cool new electrical product and a cool new '
                'HVAC product every weekday — fresh picks Monday–Friday; weekends '
                'carry Friday\'s picks.</p>' + spotlight)
    out = ('<div class="secname">Construction · Engineering · Tech</div>' +
            preamble + "\n".join(intro_bits) + nav + glance + spot +
            "\n".join(rendered) +
            '<p class="totop"><a href="#top">Back to top ↑</a></p>')
    paths = story_paths_for("tech", date, "item") or story_paths_for("tech", date)
    return out.replace("@@FIRSTSTORY@@", f'{prefix}{paths[0]}' if paths else "#")

# ---- tech archive pages + latest ----
(DOCS / "tech" / "archive").mkdir(parents=True, exist_ok=True)
for date, (pat, label, one) in TECH.items():
    body = (f'<p class="crumb"><a href="../index.html">Tech Briefing</a> · '
            f'<a href="index.html">Archive</a></p><article>{render_tech_article(tech_report(date), date, "../../")}</article>')
    (DOCS / "tech" / "archive" / f"{date}.html").write_text(
        shell("../../", f"Sharma Tech — {label}", body, active="tech"), encoding="utf-8")

tlatest = sorted(TECH)[-1]
body = (f'<p class="crumb"><span class="kicker">Construction · Engineering · Tech · Latest Edition</span></p>'
        f'<article>{render_tech_article(tech_report(tlatest), tlatest, "../")}</article>')
(DOCS / "tech" / "index.html").write_text(
    shell("../", f"Sharma Tech — {TECH[tlatest][1]}", body, active="tech"), encoding="utf-8")

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
    shell("../../", "Sharma Tech Archive", body, active="tech"), encoding="utf-8")

# ---------- PERMIT NEWS: compiled from the Lead Finder permit board ----------
# Source snapshot: permits-source.json in this repo root — a copy of the
# board's live data file (repo Sharmaelechvac/sharma-lead-finder,
# docs/data.json). Refresh = re-copy that file over permits-source.json
# and re-run this build. Nothing here is estimated: every number is
# counted from the snapshot with the board's own rules (its
# docs/index.html) — a record counts only when its builder name
# slug-matches a builder listed on the board, so records with no builder
# and do-not-contact builders' records stay hidden, exactly as on the
# board. Headline totals cross-check: stats.permits 2,832 in the file,
# minus 8 skipped DNC and 22 skipped no-builder records = 2,802 visible.
import json, collections, datetime

def _lf_clean(raw):
    if not raw:
        return ""
    s = re.sub(r"\s+", " ", str(raw))
    s = re.sub(r",?\s*d/b/a\s+", " ", s, flags=re.I)
    return s.strip()

def _lf_norm(raw):
    s = _lf_clean(raw).lower()
    s = re.sub(r"[.,'\"()]", " ", s)
    s = re.sub(r"\b(llc|l l c|inc|incorporated|corp|corporation|co|ltd|limited|company|companies|the)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def _lf_slug(raw):
    n = _lf_norm(raw) or _lf_clean(raw).lower()
    return re.sub(r"[^a-z0-9]+", "-", n).strip("-")[:80] or "unknown"

def _fmt_day(d):
    return f"{d.strftime('%B')} {d.day}, {d.year}"

def _fmt_rec_date(s):
    try:
        return _fmt_day(datetime.date.fromisoformat(str(s)[:10]))
    except Exception:
        return ihtml.escape(str(s or ""))

PERMITS = {"ok": False}
permit_card = ""
_psrc = ROOT / "permits-source.json"
if _psrc.exists():
    _pd = json.loads(_psrc.read_text(encoding="utf-8"))
    _builders = _pd.get("builders", [])
    _records = _pd.get("records", [])
    _recs = collections.defaultdict(list)
    for _r in _records:
        _recs[_lf_slug(_r.get("builder"))].append(_r)
    _vis_ids = {b["id"] for b in _builders}
    _vis = [r for r in _records if _lf_slug(r.get("builder")) in _vis_ids]
    _fetched = datetime.datetime.fromisoformat(
        _pd["fetchedAt"].replace("Z", "+00:00")).date()
    def _rdate(r):
        try:
            return datetime.date.fromisoformat(str(r.get("date"))[:10])
        except Exception:
            return None
    _vdates = [d for d in (_rdate(r) for r in _vis) if d]
    _county = {}
    for _b in _builders:
        for _c in (_b.get("counties") or []):
            _county[_c] = _county.get(_c, 0) + sum(
                1 for r in _recs.get(_b["id"], []) if r.get("county") == _c)
    _county_rows = sorted(((c, n) for c, n in _county.items() if n > 0),
                          key=lambda kv: (-kv[1], kv[0]))
    _top_builders = sorted(_builders,
                           key=lambda b: (-(b.get("permitCount") or 0), b["name"]))[:15]
    _latest = sorted(_vis, key=lambda r: str(r.get("date") or ""), reverse=True)[:25]
    PERMITS = {
        "ok": True, "fetched": _fetched, "visible": len(_vis),
        "builders_n": len(_builders), "counties_n": len(_county_rows),
        "last7": sum(1 for d in _vdates if d >= _fetched - datetime.timedelta(days=6)),
        "last30": sum(1 for d in _vdates if d >= _fetched - datetime.timedelta(days=29)),
        "county_rows": _county_rows, "top_builders": _top_builders,
        "latest": _latest,
        "top_county": _county_rows[0] if _county_rows else ("", 0),
        "top_builder": _top_builders[0] if _top_builders else {},
    }

if PERMITS["ok"]:
    P = PERMITS
    fetched_label = _fmt_day(P["fetched"])
    stats = keynums_html([
        ("Visible permits", f"{P['visible']:,}"),
        ("Builders tracked", f"{P['builders_n']:,}"),
        ("Counties with records", f"{P['counties_n']}"),
        ("Permits in the last 7 days", f"{P['last7']:,}"),
        ("Permits in the last 30 days", f"{P['last30']:,}")])
    county_rows = "\n".join(
        f'<tr><td>{ihtml.escape(c)}</td><td class="n">{n:,}</td>'
        f'<td class="n">{n / P["visible"] * 100:.1f}%</td></tr>'
        for c, n in P["county_rows"])
    builder_rows = "\n".join(
        f'<tr><td>{ihtml.escape(b["name"])}</td><td class="n">{b.get("permitCount") or 0:,}</td>'
        f'<td>{_fmt_rec_date(b.get("latestDate"))}</td>'
        f'<td class="n">{len(b.get("counties") or [])}</td></tr>'
        for b in P["top_builders"])
    latest_rows = "\n".join(
        f'<tr><td>{ihtml.escape(str(r.get("builder") or ""))}</td>'
        f'<td>{ihtml.escape(str(r.get("address") or ""))}</td>'
        f'<td>{ihtml.escape(str(r.get("county") or ""))}</td>'
        f'<td>{_fmt_rec_date(r.get("date"))}</td>'
        f'<td class="num">{ihtml.escape(str(r.get("permitNo") or ""))}</td></tr>'
        for r in P["latest"])
    _top3 = P["county_rows"][:3]
    _top3_sum = sum(n for _, n in _top3)
    _targets = {"Orange", "Osceola", "Polk", "Seminole", "Lake", "Marion",
                "Citrus", "Brevard", "Hernando", "Pasco", "Sumter"}
    _trows = [(c, n) for c, n in P["county_rows"] if c in _targets]
    _tsum = sum(n for _, n in _trows)
    _t3 = ", ".join(f"{c} ({n:,})" for c, n in _trows[:3])
    means = (
        f"The board's permits are concentrated: {_top3[0][0]}, {_top3[1][0]} and "
        f"{_top3[2][0]} together hold {_top3_sum:,} of the {P['visible']:,} visible "
        f"permits ({_top3_sum / P['visible'] * 100:.0f}%). "
        f"{ihtml.escape(str(P['top_builder'].get('name', '')))} is the most active "
        f"builder on the board with {P['top_builder'].get('permitCount') or 0:,} permits. "
        f"In Sharma's target counties, {_t3} lead; the {len(_trows)} target counties "
        f"with records hold {_tsum:,} permits between them. Builder names are shown "
        f"as the board lists them — the same company can appear under more than one "
        f"name variant.")
    pbody = f"""
<span class="kicker">Permit News</span>
<h1 class="pagehead">Permit News</h1>
<p class="windowline">Compiled from the Sharma Lead Finder board — data as of {fetched_label} · <a href="https://sharmaelechvac.github.io/sharma-lead-finder/">Open the Lead Finder board</a></p>
{stats}
<p class="sec-intro">{means}</p>
<h2 class="sec">Permits by county</h2>
<div class="tblwrap"><table class="data"><tr><th>County</th><th class="n">Permits</th><th class="n">Share</th></tr>
{county_rows}</table></div>
<h2 class="sec">Top builders by permits</h2>
<div class="tblwrap"><table class="data"><tr><th>Builder</th><th class="n">Permits</th><th>Latest permit</th><th class="n">Counties</th></tr>
{builder_rows}</table></div>
<h2 class="sec">Latest permits</h2>
<div class="tblwrap"><table class="data"><tr><th>Builder</th><th>Address</th><th>County</th><th>Date</th><th>Permit no.</th></tr>
{latest_rows}</table></div>
<p>Counting follows the board's own rules: a permit counts only when it belongs to a builder listed on the Lead Finder board. Permits with no builder named, and permits from do-not-contact builders, are left out — the board's file holds {len(_records):,} records in total, of which {P['visible']:,} are visible on this basis.</p>
<p class="totop"><a href="#top">Back to top ↑</a></p>
"""
    (DOCS / "permits").mkdir(parents=True, exist_ok=True)
    (DOCS / "permits" / "index.html").write_text(
        shell("../", "Permit News", pbody, active="permits"), encoding="utf-8")
    permit_card = f"""
<div class="techfeature nophoto"><span class="kicker">Permit News</span>
<h2 class="headline"><a href="permits/index.html">{P['visible']:,} permits from {P['builders_n']:,} builders across {P['counties_n']} counties</a></h2>
<p class="spotline">Top county: <b>{ihtml.escape(P['top_county'][0])}</b> ({P['top_county'][1]:,} permits) · Top builder: <b>{ihtml.escape(str(P['top_builder'].get('name', '')))}</b> ({P['top_builder'].get('permitCount') or 0:,} permits) · {P['last7']:,} permits in the last 7 days</p>
<p class="byline">Compiled from the Sharma Lead Finder board · Data as of {fetched_label}</p>
<a class="cont" href="permits/index.html">Read the permit news →</a></div>"""

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
<div class="masthead"><div class="mast-name">Sharma News</div><div class="mast-tag">Legal \u00b7 Finance \u00b7 Construction, Engineering &amp; Tech \u00b7 Permits</div></div>
{glance_html(HOME_GLANCE)}
<div class="front">
<div class="story nyt-lead"><span class="kicker">Legal Briefing</span>
<a class="photolink" href="{LEGAL_BASE}/">{photo_html(home_imgs.get("legal"), "")}</a>
<h2 class="headline"><a href="{LEGAL_BASE}/">{LEGAL['2026-11-22'][1]}</a></h2>
<p class="byline">Legal Briefing — Harvey, Legal Advisor · Edition of Nov 21, 2026</p>
<a class="cont" href="{LEGAL_BASE}/">Read today's legal briefing →</a></div>
<div class="story"><span class="kicker">Finance Briefing</span>
<a class="photolink" href="finance/index.html">{photo_html(home_imgs.get("finance"), "")}</a>
<h2 class="headline"><a href="finance/index.html">{FIN['2026-11-23'][2]}</a></h2>
<p class="byline">Finance Briefing — Warren Buffett, CFO · Edition of Nov 23, 2026</p>
<a class="cont" href="finance/index.html">Read today's finance briefing →</a></div>
</div>
<div class="techfeature"><span class="kicker">Construction · Engineering · Tech</span>
<a class="photolink" href="tech/index.html">{photo_html(tech_lead, "")}</a>
<h2 class="headline"><a href="tech/index.html">Data center cancellations doubled in Q3 — 16 projects stopped, $64 billion in planned investment</a></h2>
<p class="spotline">Product Spotlight — Electrical: <b>Briggs &amp; Stratton SimpliPHI 16 energy storage battery</b> · HVAC: <b>ECO2 Systems Sanco 40kW heat pump</b></p>
<p class="byline">Sharma Tech · Edition of Nov 24, 2026</p>
<a class="cont" href="tech/index.html">Read today's tech briefing →</a></div>
{permit_card}
<h2 class="sec">Legal — Back Issues</h2><ul class="arch">{legal_arch}</ul>
<h2 class="sec">Finance — Back Issues</h2><ul class="arch">{fin_arch}</ul>
<h2 class="sec">Tech — Back Issues</h2><ul class="arch">{tech_arch}</ul>
"""
(DOCS / "index.html").write_text(shell("", "Home — Monday, November 23, 2026", body, active="home"), encoding="utf-8")
for _path, (_title, _sbody, _sec) in STORY_PAGES.items():
    _p = DOCS / _path
    _p.parent.mkdir(parents=True, exist_ok=True)
    _p.write_text(shell("../../", _title, _sbody, active=_sec), encoding="utf-8")
print("story pages:", len(STORY_PAGES))
print("built:", [str(p.relative_to(DOCS)) for p in sorted(DOCS.rglob('*.html'))])
