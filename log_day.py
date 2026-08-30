#!/usr/bin/env python3
"""log_day.py — write a day's real record into plays_log.json, automatically.

The public record used to be typed by hand, and that is how a winning pick
(Blake Snell, 8/29, 3 BB) went missing and the day was published as 5-2 when
it was really 6-2. The record is the whole credibility of this project, so it
should not depend on remembering to type a row.

This reads the ARCHIVED board for a date, takes the model's calls (>=60% on a
side), looks up what each pitcher actually did from MLB's boxscores, and
upserts the day into plays_log.json.

  python3 log_day.py 2026-08-29          # write that day
  python3 log_day.py 2026-08-29 --dry    # show, change nothing

Existing hand-entered days are matched on pitcher name, so re-running is safe
and will report anything that disagrees rather than silently overwriting.
"""
import json, os, sys, argparse, collections, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "..", "engine", "mlb", "walks")
LOG = os.path.join(HERE, "plays_log.json")
API = "https://statsapi.mlb.com/api/v1"
CALL = 0.60          # a "call" = model >=60% on a side (matches gen_history)


def get(url):
    return json.load(urllib.request.urlopen(url, timeout=30))


def actual_bb(date):
    """{pitcher name: walks} for every STARTER on that US date."""
    out = {}
    sch = get(f"{API}/schedule?sportId=1&date={date}")
    for d in sch.get("dates", []):
        for g in d.get("games", []):
            try:
                bs = get(f"{API}/game/{g['gamePk']}/boxscore")
            except Exception:
                continue
            for side in ("home", "away"):
                t = bs["teams"][side]
                for pid in t.get("pitchers", []):
                    p = t["players"].get(f"ID{pid}", {})
                    st = p.get("stats", {}).get("pitching", {})
                    if st.get("gamesStarted"):
                        out[p["person"]["fullName"]] = st.get("baseOnBalls")
    return out


def calls_for(date, allow_reconstructed=False):
    """The model's calls from the archived board: (pitcher, side, prob)."""
    path = os.path.join(ENGINE, f"{date}.json")
    if not os.path.exists(path):
        raise SystemExit(f"No archived board {path}.\n"
                         f"Rebuild it:  cd {ENGINE} && python3 walks_board.py {date}")
    board = json.load(open(path))
    if board.get("reconstructed") and not allow_reconstructed:
        raise SystemExit(
            f"{path} is a RECONSTRUCTED board (built after the slate).\n"
            "Past lineups are confirmed, so a rebuild is better-informed than\n"
            "the board that was actually posted — on 8/29 that moved Ryan\n"
            "Johnson by -11.5 points. Writing it into the public record would\n"
            "claim picks that were never published.\n"
            "Grade reconstructed days by hand, or pass --allow-reconstructed\n"
            "if you know the day was never published.")
    out = []
    for r in board["board"]:
        p = (r.get("model") or {}).get("p_over_1_5")
        if not r.get("ranked") or p is None:
            continue
        if p >= CALL:
            out.append((r["pitcher"], "over", p))
        elif p <= 1 - CALL:
            out.append((r["pitcher"], "under", p))
    out.sort(key=lambda x: -x[2])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("date")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--allow-reconstructed", action="store_true",
                    help="write a day whose board was rebuilt after the slate")
    a = ap.parse_args()

    calls = calls_for(a.date, a.allow_reconstructed)
    real = actual_bb(a.date)

    plays, missing = [], []
    for name, side, p in calls:
        bb = real.get(name)
        if bb is None:
            missing.append(name)          # didn't start / postponed
            continue
        won = (bb > 1.5) if side == "over" else (bb < 1.5)
        plays.append(collections.OrderedDict(
            [("pitcher", name), ("side", side), ("line", "1.5"),
             ("result", "W" if won else "L"), ("bb", bb)]))
    plays.sort(key=lambda x: -x["bb"])

    w = sum(1 for x in plays if x["result"] == "W")
    l = len(plays) - w
    print(f"{a.date}: {len(calls)} calls, {len(plays)} started -> {w}-{l}")
    for x in plays:
        print(f"   {x['result']}  {x['bb']} BB  {x['pitcher']} ({x['side']} 1.5)")
    if missing:
        print(f"   did not start: {', '.join(missing)}")

    raw = open(LOG).read()
    log = json.loads(raw, object_pairs_hook=collections.OrderedDict)
    prev = next((d for d in log["days"] if d["date"] == a.date), None)
    if prev:
        old = {x["pitcher"]: x for x in prev["plays"]}
        new = {x["pitcher"]: x for x in plays}
        for nm in sorted(set(old) - set(new)):
            print(f"   ! in log but not a model call now: {nm}")
        for nm in sorted(set(new) - set(old)):
            print(f"   + newly logged: {nm}")
        for nm in sorted(set(old) & set(new)):
            if old[nm]["result"] != new[nm]["result"] or old[nm]["bb"] != new[nm]["bb"]:
                print(f"   ! disagrees on {nm}: log {old[nm]['result']}/{old[nm]['bb']}"
                      f" vs actual {new[nm]['result']}/{new[nm]['bb']}")

    if a.dry:
        print("   (dry run — plays_log.json untouched)")
        return

    entry = collections.OrderedDict(
        [("date", a.date), ("note", "model calls (60%+ on a side)"),
         ("plays", plays)])
    log["days"] = [d for d in log["days"] if d["date"] != a.date]
    log["days"].append(entry)
    log["days"].sort(key=lambda d: d["date"], reverse=True)
    open(LOG, "w").write(json.dumps(log, indent=2, ensure_ascii=True)
                         + ("\n" if raw.endswith("\n") else ""))
    print(f"   wrote {LOG}")


if __name__ == "__main__":
    main()
