import json, html, sys
from weasyprint import HTML

if len(sys.argv) != 3:
    sys.exit("Nutzung: build_cv.py <input.json> <output.pdf>")
IN, OUT = sys.argv[1], sys.argv[2]
with open(IN, encoding="utf-8") as f:
    r = json.load(f)

def esc(s): return html.escape(str(s))
b = r["basics"]; loc = b.get("location", {})

def fmt(d):
    if not d: return ""
    p = d.split("-"); return f"{p[1]}/{p[0][2:]}" if len(p) >= 2 else p[0]
def daterange(it):
    s, e = it.get("startDate",""), it.get("endDate")
    if s and not e: return f"{fmt(s)} – heute"
    if s and e: return fmt(s) if fmt(s)==fmt(e) else f"{fmt(s)} – {fmt(e)}"
    return ""

P = []
ort = ", ".join(filter(None, [loc.get("address",""),
                              " ".join(filter(None, [loc.get("postalCode",""), loc.get("city","")]))]))
contact = "&nbsp;&nbsp;·&nbsp;&nbsp;".join(filter(None, [
    esc(ort), esc(b.get("phone","")),
    f'<a href="mailto:{esc(b["email"])}">{esc(b["email"])}</a>' if b.get("email") else "",
    f'<a href="{esc(b["url"])}">github.com/{esc(b["profiles"][0]["username"])}</a>' if b.get("profiles") else "",
]))
P.append(f'''<header>
  <h1>{esc(b["name"])}</h1>
  {("<div class=\"label\">"+esc(b.get("label",""))+"</div>") if b.get("label") else ""}
  <div class="contact">{contact}</div>
</header>
<p class="summary">{esc(b.get("summary",""))}</p>''')

# Education
edu = ""
for e in r.get("education", []):
    cs = e.get("courses", [])
    cs_html = f'<div class="courses"><span class="ck">Relevante Module</span> {esc(", ".join(cs))}</div>' if cs else ''
    edu += f'''<div class="entry">
      <div class="row"><span class="t">{esc(e["institution"])}</span><span class="d">{daterange(e)}</span></div>
      <div class="sub">{esc(e.get("studyType",""))} {esc(e.get("area",""))}</div>{cs_html}
    </div>'''
P.append(f'<section><h2>Ausbildung</h2>{edu}</section>')

# Projects
pr = ""
for p in r.get("projects", []):
    hl = "".join(f"<li>{esc(h)}</li>" for h in p.get("highlights", []))
    kw = ", ".join(p.get("keywords", []))
    link = f' &nbsp;·&nbsp; <a href="{esc(p["url"])}">{esc(p["url"].replace("https://",""))}</a>' if p.get("url") else ""
    pr += f'''<div class="entry">
      <div class="row"><span class="t">{esc(p["name"])}</span></div>
      <div class="desc">{esc(p.get("description",""))}</div>
      <ul>{hl}</ul>
      <div class="tech"><span class="tk">Technologien</span> {esc(kw)}{link}</div>
    </div>'''
P.append(f'<section><h2>Projekte</h2>{pr}</section>')

# Work
wk = ""
for w in r.get("work", []):
    hl = "".join(f"<li>{esc(h)}</li>" for h in w.get("highlights", []))
    wk += f'''<div class="entry">
      <div class="row"><span class="t">{esc(w["name"])} — {esc(w.get("position",""))}</span><span class="d">{daterange(w)}</span></div>
      <ul>{hl}</ul>
    </div>'''
P.append(f'<section><h2>Berufserfahrung</h2>{wk}</section>')

# Skills
sk = "".join(f'<div class="srow"><div class="scat">{esc(s["name"])}</div><div class="sval">{esc(" | ".join(s.get("keywords",[])))}</div></div>' for s in r.get("skills", []))
P.append(f'<section><h2>Kenntnisse</h2><div class="skills">{sk}</div></section>')

# Languages + Interests
langs = "".join(f'<div class="lrow"><span class="ln">{esc(l["language"])}</span><span class="lf">{esc(l["fluency"])}</span></div>' for l in r.get("languages", []))
ints = ", ".join(esc(i["name"]) for i in r.get("interests", []))
ints_html = f'<div class="col"><h2>Interessen</h2><p class="ip">{ints}</p></div>' if ints else ''
P.append(f'''<section class="cols">
  <div class="col"><h2>Sprachen</h2>{langs}</div>
  {ints_html}
</section>''')

NAVY="#243b53"; ACC="#2e5686"; INK="#1b1f24"; GRAY="#5a6470"; RULE="#d5dbe3"
CSS=f"""
@page {{ size: A4; margin: 1.25cm 1.4cm; }}
* {{ box-sizing: border-box; }}
body {{ font-family: 'Carlito','Calibri',sans-serif; color:{INK}; font-size:9.4pt; line-height:1.36; margin:0; }}
a {{ color:{ACC}; text-decoration:none; }}
header h1 {{ font-size:20pt; font-weight:700; letter-spacing:.2px; margin:0; color:{INK}; }}
.label {{ font-size:9.9pt; color:{NAVY}; font-weight:600; margin-top:3px; }}
.contact {{ font-size:8.7pt; color:{GRAY}; margin-top:4px; padding-bottom:6px; border-bottom:1.5px solid {NAVY}; }}
.summary {{ margin:8px 0 4px; font-size:9.3pt; color:#2b3138; }}
section {{ margin-top:8px; }}
h2 {{ font-size:9.3pt; font-weight:700; text-transform:uppercase; letter-spacing:1.4px; color:{NAVY};
      margin:0 0 6px; padding-bottom:3px; border-bottom:1px solid {RULE}; }}
.entry {{ margin-bottom:5px; }}
.entry:last-child {{ margin-bottom:0; }}
.row {{ display:flex; justify-content:space-between; align-items:baseline; }}
.t {{ font-weight:700; font-size:9.9pt; color:{INK}; }}
.d {{ font-size:8.5pt; color:{GRAY}; white-space:nowrap; padding-left:12px; }}
.sub {{ font-size:9.4pt; color:#2b3138; }}
.courses {{ font-size:8.9pt; color:#3a424c; margin-top:2px; }}
.ck, .tk {{ font-weight:700; color:{NAVY}; }}
.desc {{ font-size:9.3pt; color:#2b3138; margin:2px 0 3px; }}
ul {{ margin:2px 0 0; padding-left:16px; }}
li {{ margin-bottom:2px; }}
.tech {{ font-size:8.8pt; color:{GRAY}; margin-top:4px; }}
.skills {{ display:flex; flex-direction:column; gap:4px; }}
.srow {{ display:flex; align-items:baseline; margin-bottom:1px; }}
.scat {{ width:30%; font-weight:700; color:{NAVY}; font-size:9.3pt; }}
.sval {{ width:70%; font-size:9.3pt; color:#2b3138; }}
.cols {{ display:flex; gap:30px; }}
.col {{ flex:1; }}
.lrow {{ display:flex; margin-bottom:2px; font-size:9.2pt; }}
.ln {{ width:38%; font-weight:600; color:{INK}; }}
.lf {{ width:62%; color:#2b3138; }}
.ip {{ margin:0; font-size:9.2pt; color:#2b3138; }}
"""
doc=f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(P)}</body></html>"
HTML(string=doc).write_pdf(OUT)
from pypdf import PdfReader
seiten = len(PdfReader(OUT).pages)
print("Seiten:", seiten)
if seiten != 1:
    sys.exit(f"FEHLER: {seiten} Seiten — harte Regel ist genau 1 Seite (PDF wurde trotzdem geschrieben, zum Kürzen ansehen)")
