#!/usr/bin/env python3
"""Fetch checksum-pinned Unicode 16 build inputs, never runtime dependencies."""
import hashlib
import json
from pathlib import Path
import urllib.request

root = Path(__file__).resolve().parents[1]
destination = root / "_tmp/unicode"
destination.mkdir(parents=True, exist_ok=True)
manifest = json.loads((root / "build/unicode-sources.json").read_text())
for name, source in manifest.items():
    path = destination / name
    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]:
        continue
    data = urllib.request.urlopen(source["url"], timeout=60).read()
    if hashlib.sha256(data).hexdigest() != source["sha256"]:
        raise SystemExit(f"Unicode checksum mismatch: {name}")
    path.write_bytes(data)
    print(f"Fetched {name}")
