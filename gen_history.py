#!/usr/bin/env python3
"""gen_history.py — the numbers the History tab publishes.

These are LEAVE-ONE-SEASON-OUT figures from the engine's validate.py: each
season is scored by a calibration that never saw it. That matters, because the
production calibration is now fit on all three seasons — scoring a season with
a calibration that saw it would be marking our own homework, and the old
headline (+12% ROI) was exactly that.

The honest number is smaller and still good: 65.5% over 2,390 calls, +9.1% ROI
at -150, break-even around -190.
"""
import json, sys, os
ENGINE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "engine", "mlb", "walks")
sys.path.insert(0, ENGINE)
import validate as V


def main():
    r = V.loso_results(market="1.5", side="over")
    out, pooled = r["seasons"], r["pooled"]

    try:
        ledger = json.load(open("plays_log.json"))["days"]
        for d in ledger:
            d["w"] = sum(1 for p in d["plays"] if p["result"] == "W")
            d["l"] = sum(1 for p in d["plays"] if p["result"] == "L")
    except Exception:
        ledger = []

    json.dump({"seasons": out, "pooled": pooled, "days": ledger},
              open("history.json", "w"), indent=2)

    for yr, s in sorted(out.items()):
        print(f"  {yr}: {s['starts']} starts, {s['calls']} calls, "
              f"{s['w']}-{s['l']} ({s['hit']}%), ROI {s['roi']:+}%")
    if pooled:
        print(f"  pooled ({pooled['method']}): {pooled['calls']} calls, "
              f"{pooled['w']}-{pooled['l']} ({pooled['hit']}%), "
              f"ROI {pooled['roi']:+}%, break-even {pooled['be_price']}")


if __name__ == "__main__":
    main()
