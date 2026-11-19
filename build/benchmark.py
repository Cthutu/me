#!/usr/bin/env python3
"""Small reproducible PTY latency probe; not a hard real-time guarantee."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import pty
import select
import signal
import statistics
import struct
import subprocess
import tempfile
import termios
import time


def wait_for(master, marker, process):
    output = bytearray()
    finish = time.monotonic() + 5
    while time.monotonic() < finish:
        if select.select([master], [], [], 0.002)[0]:
            output.extend(os.read(master, 65536))
            if marker in output:
                return time.perf_counter()
        if process.poll() is not None:
            raise RuntimeError(f"ME exited before the marker: {bytes(output)!r}")
    raise RuntimeError(f"Timed out waiting for {marker!r}")


def sample(binary, size):
    with tempfile.TemporaryDirectory(prefix="me-latency-") as directory:
        folder = Path(directory)
        (folder / "home").mkdir()
        arguments = [str(binary), "-r"]
        if size:
            (folder / "sample.txt").write_bytes((b"word word\n" * (size // 10 + 1))[:size])
            arguments.append("sample.txt")
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        start = time.perf_counter()
        process = subprocess.Popen(arguments, cwd=folder, stdin=slave, stdout=slave,
                                   stderr=slave, start_new_session=True,
                                   env={**os.environ, "HOME": str(folder / "home"), "TERM": "xterm-256color"})
        os.close(slave)
        try:
            first = wait_for(master, b"NORMAL" if size else b"INSERT", process)
            if size:
                os.write(master, b"i")
                wait_for(master, b"INSERT", process)
            # Drain any remaining bytes from the preceding presentation.
            while select.select([master], [], [], 0)[0]:
                os.read(master, 65536)
            typed = time.perf_counter()
            os.write(master, b"Q")
            presented = wait_for(master, b"Q", process)
            process.send_signal(signal.SIGTERM)
            finish = time.monotonic() + 5
            while process.poll() is None and time.monotonic() < finish:
                if select.select([master], [], [], 0.01)[0]:
                    try:
                        os.read(master, 65536)
                    except OSError:
                        break
            process.wait(timeout=2)
            if process.returncode:
                raise RuntimeError(f"ME exited with status {process.returncode}")
            return (first - start) * 1000, (presented - typed) * 1000
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            os.close(master)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=7)
    args = parser.parse_args()
    results = {}
    for size in (0, 1024 * 1024):
        samples = [sample(args.binary.resolve(), size) for _ in range(args.iterations)]
        results[str(size)] = {
            name: {"median_ms": round(statistics.median(values), 3),
                   "min_ms": round(min(values), 3), "max_ms": round(max(values), 3)}
            for name, values in (("startup_to_frame", [s[0] for s in samples]),
                                 ("input_to_present", [s[1] for s in samples]))
        }
    print(json.dumps({"iterations": args.iterations, "file_bytes": results}, indent=2))


if __name__ == "__main__":
    main()
