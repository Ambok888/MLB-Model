#!/usr/bin/env python3
"""gen_history.py — backtest headline numbers, stated accurately.

No live/posted record yet, so the History tab is the backtest only. Each
season is reported separately with its real start count and call count.
"""
import json, sys
ENGINE = "/home/nal/mytool/walks-board/mlb/walks"
sys.path.insert(0, ENGINE)
import model as M
STRONG = 0.60

def load(p):
    d = json.load(open(p))
    return [r for r in d["rows"] if r.get("full_prior_bf")
            and len(r["full_prior_bf"]) >= 3 and r.get("opp_bb_pct") is not None]

def prob(r):
    bf = r["full_prior_bf"]; pa = sum(bf); w = sum(r["full_prior_bb"])
    p = (w + M.REGRESSION_PA*M.LEAGUE_BB_RATE)/(pa+M.REGRESSION_PA)
    lam = (sum(bf)/len(bf))*M.log5(p, r["opp_bb_pct"]/100.0, M.LEAGUE_BB_RATE)
    return M.probabilities(lam)["p_over_1_5"]

def season(rows):
    calls = w = 0
    for r in rows:
        p = prob(r)
        if p >= STRONG: calls += 1; w += bool(r["over_1_5"])
        elif p <= 1-STRONG: calls += 1; w += (not bool(r["over_1_5"]))
    return {"starts": len(rows), "calls": calls, "w": w, "l": calls-w,
            "hit": round(100*w/calls, 1) if calls else 0}

def main():
    out = {}
    for yr, path in ((2026, "backtest.json"), (2025, "backtest_2025.json")):
        try: out[str(yr)] = season(load(f"{ENGINE}/{path}"))
        except Exception: pass
    try:
        ledger = json.load(open("plays_log.json"))["days"]
        for d in ledger:
            d["w"] = sum(1 for p in d["plays"] if p["result"] == "W")
            d["l"] = sum(1 for p in d["plays"] if p["result"] == "L")
    except Exception:
        ledger = []
    json.dump({"seasons": out, "days": ledger}, open("history.json", "w"), indent=2)
    for yr, s in out.items():
        print(f"  {yr}: {s['starts']} starts, {s['calls']} calls, {s['w']}-{s['l']} ({s['hit']}%)")

if __name__ == "__main__":
    main()
