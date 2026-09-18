#!/usr/bin/env python3
"""Fetch official aid-station arrival times from Aravaipa Live and write splits.json.
Ground truth from timing mats — the runner's real time at each station he's crossed."""
import json, sys, urllib.request, datetime
from pathlib import Path

BASE = "https://live.aravaiparunning.com/api/v1/race_events"
EVENT_ID = 537            # run_rabbit_run-2026
PARTICIPANT_ID = 628957   # Ted Schultz (bib 777)
OUT = Path(__file__).resolve().parent.parent / "splits.json"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 rrr-tracker"})
    return json.load(urllib.request.urlopen(req, timeout=30))

def main():
    part = get(f"{BASE}/{EVENT_ID}/participants/{PARTICIPANT_ID}")
    event = get(f"{BASE}/{EVENT_ID}?live")

    race = next((r for r in event.get("races", []) if r.get("id") == part.get("raceId")), None)
    if race is None and event.get("races"):
        race = event["races"][0]
    if not race:
        print("No race found", file=sys.stderr); return 1

    splits = [s for s in race.get("splits", []) if s.get("distance") is not None and s.get("name") != "Roaming"]
    splits.sort(key=lambda s: s["distance"])

    arrival = {}
    for c in part.get("crossings", []):
        if not c.get("validCrossing"):
            continue
        sid, ts = c.get("splitId"), c.get("timestamp")
        if sid is None or ts is None:
            continue
        if sid not in arrival or ts < arrival[sid]:
            arrival[sid] = ts

    arrivals = [{
        "name": s["name"],
        "mi": round(s["distance"] / 1609.34, 1),
        "arrivedAt": arrival.get(s["id"]),
    } for s in splits]

    data = {
        "updated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "start": part.get("st") or part.get("waveStartTime"),
        "source": "live.aravaiparunning.com",
        "arrivals": arrivals,
    }
    OUT.write_text(json.dumps(data, indent=1) + "\n")
    reached = sum(1 for a in arrivals if a["arrivedAt"])
    print(f"Wrote {OUT.name}: {reached}/{len(arrivals)} stations reached")
    return 0

if __name__ == "__main__":
    sys.exit(main())
