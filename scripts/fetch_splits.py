#!/usr/bin/env python3
"""Fetch the latest Garmin inReach MapShare position and write position.json.
Run by .github/workflows/track.yml on a schedule. No third-party proxy needed:
GitHub's runner reaches share.garmin.com directly (CORS only affects browsers)."""
import json, re, sys, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path

FEED = "https://share.garmin.com/Feed/Share/seetedrun"
RUNNER_NAME = "Ted Schultz"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "position.json"
HIST = ROOT / "positions.jsonl"   # append-only trajectory, one JSON fix per line

def localname(tag): return tag.split('}')[-1]

def main():
    req = urllib.request.Request(FEED, headers={"User-Agent": "Mozilla/5.0 rrr-tracker"})
    raw = urllib.request.urlopen(req, timeout=30).read()
    root = ET.fromstring(raw)

    best = None
    for pm in root.iter():
        if localname(pm.tag) != "Placemark":
            continue
        coord = when = vel = None
        for e in pm.iter():
            ln = localname(e.tag)
            if ln == "coordinates" and e.text and coord is None:
                parts = e.text.strip().split(",")
                if len(parts) >= 2:
                    coord = (float(parts[1]), float(parts[0]),
                             float(parts[2]) if len(parts) > 2 and parts[2] else None)
            elif ln == "when" and e.text:
                when = e.text.strip()
            elif ln == "Data" and e.get("name") == "Velocity":
                for v in e:
                    if localname(v.tag) == "value" and v.text:
                        m = re.search(r"[\d.]+", v.text)
                        if m:
                            vel = float(m.group())
        if coord is None or when is None:
            continue
        if best is None or when > best[0]:
            best = (when, coord, vel)

    if not best:
        print("No position placemark found in feed; leaving position.json unchanged.", file=sys.stderr)
        return 1

    when, (lat, lon, ele), vel = best
    data = {
        "lat": round(lat, 6),
        "lon": round(lon, 6),
        "ele": round(ele, 1) if ele is not None else None,
        "ts": when,
        "speed_kmh": vel,
        "name": RUNNER_NAME,
        "updated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    OUT.write_text(json.dumps(data, indent=1) + "\n")

    last_ts = None
    if HIST.exists():
        tail = HIST.read_text().strip().splitlines()
        if tail:
            try:
                last_ts = json.loads(tail[-1]).get("ts")
            except Exception:
                last_ts = None
    if when != last_ts:
        line = json.dumps({"ts": when, "lat": data["lat"], "lon": data["lon"], "speed_kmh": vel})
        with HIST.open("a") as f:
            f.write(line + "\n")
        print("Appended to", HIST.name)

    print("Wrote", OUT, "->", data)
    return 0

if __name__ == "__main__":
    sys.exit(main())
