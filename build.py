#!/usr/bin/env python3
"""build.py — turn a walks_board.json into the public picks site.

Reads the private engine's output and emits a single self-contained index.html.
Only PICKS + supporting data go in — no model code, no backtests. Run daily.

  python3 build.py /path/to/walks_board.json
"""
import os
import json, sys, datetime as dt, html

SRC = sys.argv[1] if len(sys.argv) > 1 else \
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "engine", "mlb", "walks", "walks_board.json")


def slim(e):
    """Extract only what the public page shows."""
    m = e.get("model") or {}
    mm = e.get("mechanism") or {}
    sr = e.get("season_rates") or {}
    p = e.get("pillars") or {}
    log = [s.get("bb") for s in (e.get("walk_log") or [])[-5:]]
    return {
        "pitcher": e.get("pitcher"),
        "team": e.get("team"),
        "opp": e.get("opp_team"),
        "throws": e.get("pitcher_throws"),
        "ranked": bool(e.get("ranked")),
        "stale": e.get("stale_log"),
        "gt": e.get("game_time_utc"),
        # model outputs
        "p15": m.get("p_over_1_5"),
        "p25": m.get("p_over_2_5"),
        "fair15": m.get("fair_price_o1_5"),
        "fair25": m.get("fair_price_o2_5"),
        "lam": m.get("lambda"),
        "bf": m.get("expected_batters_faced"),
        "starts": m.get("starts_used"),
        # context
        "log": log,
        "season_bb": sr.get("prior_bb"),
        "season_bf": sr.get("prior_bf"),
        "opp_pct": e.get("opp_bb_pct_30d"),
        "zone": mm.get("zone_pct"),
        "fstrike": mm.get("first_pitch_strike_pct"),
        "ppa": mm.get("pitches_per_pa"),
        "velo": mm.get("avg_fastball_mph"),
        "whip": mm.get("whip"),
        "med_pit": p.get("median_pitches_last5"),
        "reads": mm.get("reads") or [],
        "bullpen": (e.get("bullpen") or {}).get("read"),
        "chase": (e.get("opp_chase") or {}).get("read"),
    }


def main():
    board = json.load(open(SRC))
    date = board.get("date")
    rows = [slim(e) for e in board["board"]]
    # ranked first (by model prob), then excluded
    ranked = sorted([r for r in rows if r["ranked"] and r["p15"] is not None],
                    key=lambda r: -r["p15"])
    excl = [r for r in rows if not r["ranked"]]
    data = {"date": date, "rows": ranked, "excluded": excl,
            "built": dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M UTC")}

    try:
        hist = json.load(open("history.json"))
    except Exception:
        hist = {}
    tmpl = open("template.html").read()
    out = tmpl.replace("/*DATA*/", json.dumps(data)).replace("/*HISTORY*/", json.dumps(hist))
    open("index.html", "w").write(out)
    print(f"built index.html — {len(ranked)} ranked, {len(excl)} excluded, "
          f"slate {date}")


if __name__ == "__main__":
    main()
