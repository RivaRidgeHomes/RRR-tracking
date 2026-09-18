# Run Rabbit Run 100 — live inReach tracker

A single-page map that overlays a runner's Garmin inReach position on the RRR 100 course,
with grade-aware ETAs to each aid station and a projected finish. Hosted free on GitHub Pages;
a scheduled GitHub Action keeps the position fresh.

## How it works

- **`index.html`** — the map (Leaflet + OpenTopoMap tiles). Reads `position.json` every 2 min.
- **`routedata100.js`** — the course: track, aid stations (official mileages/elevations),
  and a precomputed grade-aware "effort" profile used for per-leg pace and the finish estimate.
- **`position.json`** — the latest inReach fix. **Updated automatically** by the Action below.
- **`.github/workflows/track.yml`** — runs `scripts/fetch_position.py` every ~5 min, which
  pulls `share.garmin.com/Feed/Share/seetedrun` and commits the new position back to the repo.
  (GitHub's runner can reach Garmin directly — CORS only blocks browsers, which is why the page
  can't fetch the feed itself.)

## Publish it (one-time)

```bash
# from inside this folder
git init -b main
git add .
git commit -m "Run Rabbit Run 100 tracker"
gh repo create rrr100-tracker --public --source=. --push   # or create the repo on github.com and push
```

Then in the repo on github.com:

1. **Settings → Pages →** Source = "Deploy from a branch", Branch = `main`, folder = `/ (root)` → Save.
   Your page appears at `https://<your-username>.github.io/rrr100-tracker/`.
2. **Settings → Actions → General →** Workflow permissions = **"Read and write permissions"** → Save.
   (Lets the Action commit `position.json`.)
3. **Actions** tab → enable workflows if prompted → open **"Update inReach position"** →
   **Run workflow** once to seed the first live update. After that it runs every ~5 min.

## Notes & knobs

- **Freshness:** GitHub cron fires about every 5 min and is often a few minutes late — fine for a
  100-miler. The page shows the fix age and greys the dot when it's stale.
- **Pace model:** `scripts`-free; it's in the data. Effort = 1 mile + 1 mile per 1000 ft of climb,
  with a mild descent credit. Change the runner's start time in `index.html` (`START_UTC`) if needed.
- **Different runner/course:** point `FEED` in `scripts/fetch_position.py` at another MapShare feed
  and regenerate `routedata100.js` from that course's GPX.
- **Privacy:** this makes a person's live location public. Only publish a feed the runner has chosen
  to share, and share the page URL accordingly.
- **Cost:** $0 — public repo, GitHub Pages, and Actions minutes are free for public repositories.
