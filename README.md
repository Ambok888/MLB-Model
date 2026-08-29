# Walkline — MLB walk-props model

A daily model for MLB pitcher **walk props**. Ranks every probable starter by
his chance of going over (or under) his walk line, shows the fair price, and
the data behind it.

### 👉 Live site: https://ambok888.github.io/MLB-Model/

Punch in your own book's odds and it flags value, shows both the 1.5 and 2.5
line, and has a History tab with how it's backtested over two seasons.

---

## How it works

Walks come down to two things: how many batters a pitcher faces, and how often
he walks one. The model estimates **expected walks = batters faced × walk
rate**, blended with how patient the opposing lineup has been, and turns that
into a real probability you can compare against a price.

Backtested across two seasons (~7,000 starts) before going live. 2025 —
a season the model was never built on — is the honest test.

## Files

- `index.html` — the site (self-contained, regenerated daily)
- `template.html` — the page source
- `build.py` — turns the model output + history into `index.html`
- `gen_history.py` — backtest headline numbers + posted-picks record
- `gen_image.py` — renders a shareable picks image (for where links aren't allowed)

---

**Experimental · information only, not betting advice · gamble responsibly.**
Inspired by the walk-props method of u/CSmith20001 — an imitation, not the original.
