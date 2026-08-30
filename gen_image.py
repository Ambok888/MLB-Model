#!/usr/bin/env python3
"""gen_image.py — render today's picks as a shareable PNG, matching the site.

Builds a standalone card.html (same dark style as the site), then screenshots
it with headless Chrome. Post the PNG where links aren't allowed.

  python3 gen_image.py /path/to/walks_board.json
"""
import os
import json, sys, subprocess, os, datetime as dt

SRC = sys.argv[1] if len(sys.argv) > 1 else \
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "engine", "mlb", "walks", "walks_board.json")


TEAMS={"Arizona Diamondbacks":"ARI","Athletics":"ATH","Atlanta Braves":"ATL",
"Baltimore Orioles":"BAL","Boston Red Sox":"BOS","Chicago Cubs":"CHC","Chicago White Sox":"CWS",
"Cincinnati Reds":"CIN","Cleveland Guardians":"CLE","Colorado Rockies":"COL","Detroit Tigers":"DET",
"Houston Astros":"HOU","Kansas City Royals":"KC","Los Angeles Angels":"LAA","Los Angeles Dodgers":"LAD",
"Miami Marlins":"MIA","Milwaukee Brewers":"MIL","Minnesota Twins":"MIN","New York Mets":"NYM",
"New York Yankees":"NYY","Philadelphia Phillies":"PHI","Pittsburgh Pirates":"PIT","San Diego Padres":"SD",
"San Francisco Giants":"SF","Seattle Mariners":"SEA","St. Louis Cardinals":"STL","Tampa Bay Rays":"TB",
"Texas Rangers":"TEX","Toronto Blue Jays":"TOR","Washington Nationals":"WSH"}


def dec(p): return f"{1/p:.2f}" if 0 < p < 1 else "—"


def main():
    b = json.load(open(SRC))
    date = b["date"]
    rows = [e for e in b["board"] if e.get("ranked") and e.get("model")
            and not e["model"].get("error")]
    overs = sorted([e for e in rows if e["model"]["p_over_1_5"] >= 0.60],
                   key=lambda e: -e["model"]["p_over_1_5"])
    unders = sorted([e for e in rows if 1-e["model"]["p_over_1_5"] >= 0.60],
                    key=lambda e: -(1-e["model"]["p_over_1_5"]))

    def line(e, side):
        m = e["model"]; mm = e.get("mechanism") or {}; sr = e.get("season_rates") or {}
        p = e.get("pillars") or {}
        if side == "over":
            p15, p25 = m["p_over_1_5"], m["p_over_2_5"]; tag = "OVER"
        else:
            p15, p25 = 1-m["p_over_1_5"], 1-m["p_over_2_5"]; tag = "UNDER"
        opp = TEAMS.get(e['opp_team'], e['opp_team'][:3].upper())
        log = "".join(f"<span class='pip{" cl" if (s.get("bb") or 0)>=2 else ""}'>{s.get("bb")}</span>"
                      for s in (e.get("walk_log") or [])[-5:])
        data = (f"<span class='d'>last 5 <em>{log}</em></span>"
                f"<span class='d'>season <b>{sr.get('prior_bb')}/{sr.get('prior_bf')}</b></span>"
                f"<span class='d'>opp walk <b>{e.get('opp_bb_pct_30d')}%</b></span>"
                f"<span class='d'>zone <b>{mm.get('zone_pct')}%</b></span>"
                f"<span class='d'>1st-K <b>{mm.get('first_pitch_strike_pct')}%</b></span>"
                f"<span class='d'>WHIP <b>{mm.get('whip')}</b></span>")
        return f"""<div class="r">
          <div class="top">
            <div class="nm">{e['pitcher']}<span class="op">vs {opp}</span></div>
            <div class="ln"><span class="lb">{tag} 1.5</span><b>{round(p15*100)}%</b><i>{dec(p15)}</i></div>
            <div class="ln"><span class="lb">{tag} 2.5</span><b>{round(p25*100)}%</b><i>{dec(p25)}</i></div>
          </div>
          <div class="data">{data}</div>
        </div>"""

    body = ""
    if overs:
        body += '<div class="grp">Overs the model likes</div>' + "".join(line(e,"over") for e in overs)
    if unders:
        body += '<div class="grp">Unders</div>' + "".join(line(e,"under") for e in unders)

    html = f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap">
<style>
*{{margin:0;box-sizing:border-box}}
body{{width:880px;background:#0d1219;color:#eaeef4;
  font-family:"Plus Jakarta Sans",sans-serif;padding:32px 34px}}
.mono{{font-family:"JetBrains Mono",monospace}}
.head{{display:flex;align-items:baseline;gap:12px;border-bottom:1px solid #232d3a;padding-bottom:16px;margin-bottom:6px}}
.logo{{font-weight:800;font-size:26px;letter-spacing:-.02em}}
.logo span{{color:#2fd693}}
.date{{font-family:"JetBrains Mono",monospace;font-size:13px;color:#8b97a7;margin-left:auto}}
.sub{{font-size:13px;color:#8b97a7;margin:10px 0 4px}}
.grp{{font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
  color:#5e6b7b;margin:20px 0 9px}}
.r{{background:#151c26;border:1px solid #232d3a;border-radius:12px;padding:13px 17px;margin-bottom:8px}}
.top{{display:grid;grid-template-columns:1fr 150px 150px;gap:12px;align-items:center}}
.data{{display:flex;flex-wrap:wrap;gap:16px;margin-top:11px;padding-top:11px;border-top:1px solid #202a36}}
.data .d{{font-family:"JetBrains Mono",monospace;font-size:12px;color:#5e6b7b}}
.data .d b{{color:#b7c0cd;font-weight:600}}
.data .d em{{font-style:normal}}
.pip{{display:inline-block;min-width:18px;text-align:center;background:#202a36;color:#8b97a7;
  border-radius:4px;padding:2px 0;margin-left:2px;font-weight:600}}
.pip.cl{{background:#12241d;color:#2fd693}}
.nm{{font-weight:700;font-size:17px}}
.op{{font-family:"JetBrains Mono",monospace;font-size:12px;color:#8b97a7;margin-left:8px;font-weight:500}}
.ln{{text-align:right;font-family:"JetBrains Mono",monospace}}
.ln .lb{{display:block;font-size:9.5px;color:#5e6b7b;letter-spacing:.06em}}
.ln b{{font-size:19px;color:#eaeef4;font-weight:700}}
.ln i{{font-style:normal;font-size:12px;color:#8b97a7;margin-left:6px}}
.foot{{margin-top:22px;padding-top:14px;border-top:1px solid #232d3a;font-size:12px;color:#5e6b7b;line-height:1.6}}
.foot b{{color:#8b97a7;font-weight:600}}
</style></head><body>
  <div class="head"><span class="logo">walk<span>·</span>line</span>
    <span class="date">{date}</span></div>
  <div class="sub">Model % that a starter goes over (or under) his walk line, with the fair decimal price. Take a line only if your book pays more than the fair number.</div>
  {body}
  <div class="foot"><b>Still testing — not betting advice.</b> Numbers from MLB's free data. Full tool + history: walkline (Ambok888/MLB-Model on GitHub Pages).</div>
</body></html>"""

    open("card.html", "w").write(html)
    out = os.path.abspath(f"picks-{date}.png")
    tmp = os.path.abspath("_card_full.png")
    # render tall, then auto-crop the dark background off the bottom
    subprocess.run([
        "google-chrome", "--headless=new", "--no-sandbox",
        "--force-device-scale-factor=2", "--hide-scrollbars",
        "--window-size=880,2400",
        f"--screenshot={tmp}", os.path.abspath("card.html")
    ], check=True, capture_output=True)
    # crop away the empty dark area below the content
    from PIL import Image
    im = Image.open(tmp).convert("RGB")
    W, H = im.size
    px = im.load()
    bg = (13, 18, 25)  # #0d1219
    last = 0
    for y in range(H-1, -1, -1):
        row_bg = all(abs(px[x, y][c]-bg[c]) <= 3 for x in range(0, W, 40) for c in range(3))
        if not row_bg:
            last = y; break
    im.crop((0, 0, W, min(H, last+34*2))).save(out)  # +padding (scaled x2)
    os.remove(tmp)
    print(f"wrote {out}  ({im.size[0]}px wide)")


if __name__ == "__main__":
    main()
