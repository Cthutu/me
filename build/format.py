#!/usr/bin/env python3
"""Format ME source through Nerd's standard formatter."""
import argparse
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--nerd", default="nerd")
args = parser.parse_args()
paths = [Path("main.n"), *sorted(Path("src").glob("*.n")), *sorted(Path("tests").glob("*.n"))]
for path in paths:
    subprocess.run([args.nerd, "format", str(path)], check=True)
