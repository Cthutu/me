#!/usr/bin/env python3
"""Linux PTY integration checks. Core unit tests remain native Nerd tests."""
import argparse
import fcntl
import os
from pathlib import Path
import pty
import re
import select
import signal
import struct
import subprocess
import tempfile
import termios
import time


class Session:
    def __init__(self, binary, folder, *arguments):
        self.master, slave = pty.openpty()
        self.original_attributes = termios.tcgetattr(self.master)
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        home = folder / "home"
        home.mkdir(exist_ok=True)
        self.output = bytearray()
        self.process = subprocess.Popen(
            [str(binary), *arguments], cwd=folder, stdin=slave, stdout=slave,
            stderr=slave, start_new_session=True,
            env={**os.environ, "HOME": str(home), "TERM": "xterm-256color"},
        )
        os.close(slave)
        self.drain(0.25)

    def drain(self, seconds=0.12):
        finish = time.monotonic() + seconds
        start = len(self.output)
        while time.monotonic() < finish:
            if select.select([self.master], [], [], 0.015)[0]:
                try:
                    chunk = os.read(self.master, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                self.output.extend(chunk)
        return bytes(self.output[start:])

    def send(self, text, seconds=0.12):
        os.write(self.master, text.encode() if isinstance(text, str) else text)
        return self.drain(seconds)

    def normal(self):
        # Escape precedence is prompt, message, Insert, then selection/count.
        for _ in range(3):
            # Linux std.term currently rounds its 25 ms escape timeout to a
            # 100 ms termios tick. Do not accidentally send an Alt sequence.
            self.send(b"\x1b", 0.15)

    def command(self, command):
        self.normal()
        return self.send(":" + command + "\r", 0.18)

    def quit(self, command="q"):
        self.command(command)
        self.wait()

    def wait(self):
        finish = time.monotonic() + 4
        while self.process.poll() is None and time.monotonic() < finish:
            self.drain(0.04)
        assert self.process.poll() == 0, (self.process.poll(), bytes(self.output[-2000:]))
        self.drain(0.04)
        assert b"\x1b[?1049l" in self.output, "alternate screen was not restored"
        assert termios.tcgetattr(self.master) == self.original_attributes, "raw terminal attributes leaked"
        self.close()

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
            self.process.wait()
        if self.master >= 0:
            os.close(self.master)
            self.master = -1

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def recovery(binary, folder):
    path = folder / "note.txt"
    with Session(binary, folder, "-r", "note.txt") as session:
        session.send("one")
        session.quit()
    assert not path.exists(), "quit must not write an unsaved backing file"
    with Session(binary, folder) as session:
        assert b"NORMAL" in session.output
        session.send(b"\x1a")  # undo one character, not the Insert session
        session.send(b"\x13")
        assert path.read_bytes() == b"on"
        session.send(b"\x12")  # redo survives a successful save
        session.quit("q!")
    assert path.read_bytes() == b"on", "q! must never undo a disk write"
    with Session(binary, folder, "note.txt") as session:
        session.send(b"\x12")
        session.send(b"\x13")
        assert path.read_bytes() == b"on", "discarded buffer history reappeared"
        session.quit()


def unnamed_discard(binary, folder):
    with Session(binary, folder, "-r") as session:
        session.send("recovered")
        session.quit()
    with Session(binary, folder) as session:
        session.quit("q!")
    snapshot = next((folder / "home/.config/me").glob("*/snapshot"))
    assert b"recovered" not in snapshot.read_bytes(), "q! retained recovered unsaved work"
    with Session(binary, folder, "-r") as session:
        session.send("discard-me")
        session.quit("q!")
    snapshot = next((folder / "home/.config/me").glob("*/snapshot"))
    assert b"discard-me" not in snapshot.read_bytes()
    with Session(binary, folder) as session:
        session.send("fresh")
        session.send(b"\x13")
        session.send("fresh.txt\r")
        assert (folder / "fresh.txt").read_bytes() == b"fresh"
        session.quit()


def buffer_kill(binary, folder):
    path = folder / "saved.txt"
    path.write_bytes(b"saved")
    with Session(binary, folder, "-r", "saved.txt") as session:
        session.command("kill")
        assert path.read_bytes() == b"saved"
        session.send("recovered")
        session.quit()
    with Session(binary, folder) as session:
        session.command("kill")
        assert session.process.poll() is None
        session.send(b"\x13")
        session.send("retained.txt\r")
        assert (folder / "retained.txt").read_bytes() == b"recovered", "refused kill changed content"
        session.send("i!")
        session.command("kill!")
        session.send(b"\x1a")
        session.send("ifresh")
        session.send(b"\x13")
        session.send("fresh.txt\r")
        assert (folder / "fresh.txt").read_bytes() == b"fresh", "text undo resurrected a killed buffer"
        assert (folder / "retained.txt").read_bytes() == b"recovered"
        session.command("kill")
        session.quit()
    with Session(binary, folder) as session:
        assert b"INSERT" in session.output
        session.send("new")
        session.send(b"\x13")
        session.send("new.txt\r")
        assert (folder / "new.txt").read_bytes() == b"new", "killed buffer reappeared from continuation"
        session.quit()


def fidelity(binary, folder):
    path = folder / "mixed.txt"
    content = b"\xef\xbb\xbf\talpha\r\nbeta\nlast"
    path.write_bytes(content)
    path.chmod(0o640)
    before = path.stat()
    with Session(binary, folder, "-r", "mixed.txt") as session:
        session.command("w")
        after = path.stat()
        assert path.read_bytes() == content
        assert (after.st_ino, after.st_mtime_ns) == (before.st_ino, before.st_mtime_ns), "unchanged :w wrote the file"
        session.command("ww")
        assert path.read_bytes() == content
        assert path.stat().st_ino != before.st_ino
        session.send("iX")
        session.send(b"\x13")
        assert path.read_bytes() == b"\xef\xbb\xbfX\talpha\r\nbeta\nlast", "BOM, tabs or mixed endings changed"
        assert path.stat().st_mode & 0o777 == 0o640
        session.quit()
    invalid = folder / "invalid.txt"
    invalid.write_bytes(b"\xff\xfe\x00")
    with Session(binary, folder, "-r", "invalid.txt") as session:
        assert session.process.wait(timeout=3) == 2
        assert b"UTF-8" in session.output
    assert invalid.read_bytes() == b"\xff\xfe\x00"
    # A failed reset/open must not overwrite the earlier valid recovery state.
    with Session(binary, folder) as session:
        assert b"mixed.txt" in session.output
        session.quit()


def external_files(binary, folder):
    path = folder / "external.txt"
    path.write_bytes(b"old")
    with Session(binary, folder, "-r", "external.txt") as session:
        replacement = folder / "replacement"
        replacement.write_bytes(b"new\ntext")
        replacement.replace(path)
        session.drain(0.95)
        session.send(b"\x1a")
        session.send(b"\x13")
        assert path.read_bytes() == b"old", "external reload was not one undoable edit"
        session.quit()
    path.write_bytes(b"disk")
    with Session(binary, folder, "-r", "external.txt") as session:
        session.send("iuser")
        path.write_bytes(b"outside")
        session.drain(0.9)
        assert b"!conflict" in session.output
        session.send(b"\x13")
        assert path.read_bytes() == b"outside", "ordinary save overwrote an external conflict"
        session.command("ww")
        assert path.read_bytes() == b"outside", ":ww bypassed conflict protection"
        session.command("w!")
        assert path.read_bytes() == b"userdisk"
        session.quit()
    path.write_bytes(b"retained")
    with Session(binary, folder, "-r", "external.txt") as session:
        path.unlink()
        session.drain(0.75)
        session.quit()
    assert not path.exists(), "quit recreated an externally deleted file"
    with Session(binary, folder) as session:
        session.send(b"\x13")
        assert path.read_bytes() == b"retained"
        session.quit()
    with Session(binary, folder, "-r", "external.txt") as session:
        path.unlink()
        session.drain(0.6)
        path.write_bytes(b"reappeared")
        session.drain(0.9)
        session.send(b"\x1a")
        session.send(b"\x13")
        assert path.read_bytes() == b"retained", "reappearance did not use reload/history policy"
        session.quit()


def symlinks_and_save_as(binary, folder):
    target = folder / "target.txt"
    target.write_bytes(b"target")
    target.chmod(0o660)
    os.setxattr(target, "user.me-test", b"attribute bytes\x00unchanged")
    identity = (target.stat().st_uid, target.stat().st_gid)
    acl = struct.pack("<I", 2) + b"".join(
        struct.pack("<HHI", tag, permissions, identifier)
        for tag, permissions, identifier in [(1, 6, 0xffffffff), (2, 4, 65534),
                                              (4, 6, 0xffffffff), (16, 6, 0xffffffff),
                                              (32, 0, 0xffffffff)]
    )
    os.setxattr(target, "system.posix_acl_access", acl)
    long_name = folder / ("a" * 250)
    long_name.write_bytes(b"long")
    link = folder / "link.txt"
    link.symlink_to("target.txt")
    other = folder / "other.txt"
    other.write_bytes(b"unrelated")
    with Session(binary, folder, "-r", "link.txt") as session:
        session.send("iedit")
        session.send(b"\x13")
        assert link.is_symlink() and target.read_bytes() == b"edittarget"
        assert target.stat().st_mode & 0o777 == 0o660
        assert (target.stat().st_uid, target.stat().st_gid) == identity
        assert os.getxattr(target, "user.me-test") == b"attribute bytes\x00unchanged"
        assert os.getxattr(target, "system.posix_acl_access") == acl
        session.command("w other.txt")
        assert other.read_bytes() == b"unrelated"
        session.command("w! other.txt")
        assert other.read_bytes() == b"edittarget"
        session.normal()
        session.send("iZ")
        session.send(b"\x13")
        assert other.read_bytes() == b"editZtarget"
        assert target.read_bytes() == b"edittarget", "save-as failed to reassociate"
        session.command("w missing-directory/file")
        session.send(b"\x13")
        assert other.read_bytes() == b"editZtarget"
        session.quit()
    with Session(binary, folder, "-r", long_name.name) as session:
        session.send("iX")
        session.send(b"\x13")
        assert long_name.read_bytes() == b"Xlong", "valid long filenames must not overflow temporary names"
        session.quit()
    (folder / "outside/nested").mkdir(parents=True)
    (folder / "jump").symlink_to("outside/nested", target_is_directory=True)
    chosen = folder / "outside/chosen.txt"
    chosen.write_bytes(b"right")
    wrong = folder / "chosen.txt"
    wrong.write_bytes(b"wrong")
    with Session(binary, folder, "-r", "jump/../chosen.txt") as session:
        session.send("iX")
        session.send(b"\x13")
        assert chosen.read_bytes() == b"Xright", "lexical dot removal ignored symlink resolution"
        assert wrong.read_bytes() == b"wrong"
        session.quit()
    with Session(binary, folder, "outside/chosen.txt") as session:
        session.command("buffers")
        response = session.command("buffer 2")
        # Dirty-cell output can omit unchanged spaces between these words.
        assert b"buffer;" in response, "CLI alias duplicated a recovered buffer"
        session.quit()


def search_replace_and_buffers(binary, folder):
    path = folder / "words.txt"
    path.write_bytes(b"one two ONE\r\nthree one")
    with Session(binary, folder, "-r", "words.txt") as session:
        session.send("/three")
        session.send(b"\x1b", 0.15)
        session.send("iX")
        session.send(b"\x13")
        original = b"Xone two ONE\r\nthree one"
        assert path.read_bytes() == original, f"cancelled search failed to restore the caret: {path.read_bytes()!r}"
        session.command("replace /one/word/g")
        session.send(b"\x13")
        assert path.read_bytes() == b"Xword two ONE\r\nthree word"
        session.send(b"\x1a")
        session.send(b"\x13")
        assert path.read_bytes() == original, "replace-all was not a single undo operation"
        session.command("replace /one//g")
        session.send(b"\x13")
        assert path.read_bytes() == b"X two ONE\r\nthree "
        session.quit()
    with Session(binary, folder, "-r") as session:
        session.send("alpha")
        session.quit()
    with Session(binary, folder, "missing/beta.txt") as session:
        session.send("beta")
        session.command("wq")
        assert session.process.poll() is None
        session.send("alpha.txt\r")
        assert (folder / "alpha.txt").read_bytes() == b"alpha"
        assert session.process.poll() is None, "wq quit despite a later save failure"
        session.command("buffers")
        session.command("buffer 2")
        session.command("w beta.txt")
        assert (folder / "beta.txt").read_bytes() == b"beta"
        session.quit("wq")
    with Session(binary, folder, "alpha.txt") as session:
        session.command("buffer 2")
        session.send("i!")
        session.send(b"\x13")
        assert (folder / "beta.txt").read_bytes() == b"beta!"
        assert (folder / "alpha.txt").read_bytes() == b"alpha"
        session.quit()


def byte_paths_and_checkpoint_failures(binary, folder):
    filename = b"raw_\xff.txt"
    raw_path = os.fsencode(folder) + b"/" + filename
    descriptor = os.open(raw_path, os.O_WRONLY | os.O_CREAT, 0o640)
    os.write(descriptor, b"raw")
    os.close(descriptor)
    with Session(binary, folder, "-r", filename) as session:
        session.send("iX")
        session.send(b"\x13")
        with open(raw_path, "rb") as source:
            assert source.read() == b"Xraw", "byte filenames must not hang presentation or change backing paths"
        session.quit()
    with Session(binary, folder, "-r") as session:
        session.send("precious")
        storage = next((folder / "home/.config/me").glob("*/lock")).parent
        held = storage.with_name(storage.name + ".held")
        storage.rename(held)
        storage.write_bytes(b"not a directory")
        session.drain(1.3)
        assert b"!C" in session.output, "checkpoint failure did not remain indicated"
        session.command("q")
        assert session.process.poll() is None, "checkpoint failure allowed unsafe normal quit"
        storage.unlink()
        held.rename(storage)
        session.drain(1.3)
        session.quit()
    with Session(binary, folder) as session:
        session.send(b"\x13")
        session.send("precious.txt\r")
        assert (folder / "precious.txt").read_bytes() == b"precious"
        session.quit()
    snapshot = next((folder / "home/.config/me").glob("*/snapshot"))
    damaged = bytearray(snapshot.read_bytes())
    damaged[len(damaged) // 2] ^= 1
    snapshot.write_bytes(damaged)
    with Session(binary, folder) as session:
        session.send("new")
        session.command("q")
        assert session.process.poll() is None
        session.quit("q!")
    assert snapshot.read_bytes() == damaged, "failed recovery overwrote the damaged original snapshot"


def second_instance(binary, folder):
    with Session(binary, folder, "-r") as owner:
        owner.send("owner")
        owner.drain(1.25)
        with Session(binary, folder) as second:
            assert b"Another ME owns" in second.output
            second.send("other")
            second.command("q")
            assert second.process.poll() is None, "non-persisting instance discarded unsaved work"
            assert b"Cannot quit safely" in second.output
            second.quit("q!")
        snapshot = next((folder / "home/.config/me").glob("*/snapshot"))
        data = snapshot.read_bytes()
        assert b"owner" in data and b"other" not in data
        owner.quit()
    with Session(binary, folder) as session:
        session.send(b"\x13")
        session.send("owner.txt\r")
        assert (folder / "owner.txt").read_bytes() == b"owner"
        session.quit()


def crash_and_signals(binary, folder):
    with Session(binary, folder, "-r") as session:
        session.send("crash")
        session.drain(1.4)
        session.process.kill()
        session.process.wait()
    with Session(binary, folder) as session:
        assert b"NORMAL" in session.output, "non-empty recovery must start in Normal"
        session.send(b"\x1a")
        session.send(b"\x13")
        session.send("crash.txt\r")
        assert (folder / "crash.txt").read_bytes() == b"cras"
        session.quit()
    with Session(binary, folder, "-r") as session:
        session.send("signal")
        session.process.send_signal(signal.SIGTERM)
        session.wait()
    with Session(binary, folder) as session:
        session.send(b"\x13")
        session.send("signal.txt\r")
        assert (folder / "signal.txt").read_bytes() == b"signal"
        session.quit()


def word_delete(binary, folder):
    path = folder / "words.txt"
    path.write_bytes(b"alpha beta")
    control_backspace = b"\x1b[127;5u"
    with Session(binary, folder, "-r", "words.txt") as session:
        session.send(b"\x1b[F")
        session.send("i")
        session.send(control_backspace)
        session.send(b"\x13")
        assert path.read_bytes() == b"alpha ", "Ctrl+Backspace did not delete the previous word"
        session.send(b"\x1a")
        session.send(b"\x13")
        assert path.read_bytes() == b"alpha beta", "word deletion was not one undo operation"
        session.send(b"\x1b[H")
        session.send(b"\x1b[1;6C")
        session.send(control_backspace)
        session.send(b"\x13")
        assert path.read_bytes() == b"beta", "Ctrl+Backspace did not delete the active selection"
        session.quit()


def duplicate_selection(binary, folder):
    path = folder / "duplicate.txt"
    block = b"one\r\ntwo\n"
    path.write_bytes(block + b"three")
    with Session(binary, folder, "-r", "duplicate.txt") as session:
        session.send("2l")
        session.send(b"\x04")
        session.send(b"\x04")
        session.send(b"\x13")
        assert path.read_bytes() == block * 3 + b"three", "Ctrl+D did not repeat the selected line block"
        session.send(b"\x1a")
        session.send(b"\x13")
        assert path.read_bytes() == block * 2 + b"three", "block duplication was not one undo operation"
        session.send(b"\x1b[A")
        session.send(b"\x1b[1;2C")
        session.send(b"\x04")
        session.send("iX")
        session.send(b"\x13")
        assert path.read_bytes() == block * 2 + b"tXwo\nthree", "character selection was not cleared when duplicating the caret line"
        session.quit()


def gutter_highlight(binary, folder):
    (folder / "lines.txt").write_bytes(b"a\nb\nc")
    gold = rb"\x1b\[38;2;214;179;90m(?:\x1b\[[0-9;]*m)* *"
    with Session(binary, folder, "-r", "lines.txt") as session:
        assert re.search(gold + b"1", session.output), "current absolute line number was not highlighted"
        moved = session.send(b"\x1b[B")
        assert re.search(gold + b"2", moved), "gutter highlight did not follow caret movement"
        assert b"38;2;115;130;153m" in moved, "former current line did not return to muted numbering"
        inserted = session.send("i")
        # Numbering becomes absolute, but the current line keeps its emphasis.
        assert b"INSERT" in inserted
        session.send(b"\x1b[B")
        assert re.search(gold + b"3", session.output), "Insert-state current line lost its highlight"
        session.quit()


def graphemes_and_resize(binary, folder):
    with Session(binary, folder, "-r") as session:
        session.send("ae\u0301👩\u200d💻b")
        session.drain(0.15)
        assert "e\u0301".encode() in session.output, "combining grapheme was not presented"
        assert "👩\u200d💻".encode() in session.output, "emoji cluster was not presented"
        session.send(b"\x1b[D")
        session.send(b"\x7f")
        fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 6, 24, 0, 0))
        session.drain(0.15)
        fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        session.drain(0.15)
        session.send(b"\x13")
        session.send("unicode.txt\r")
        assert (folder / "unicode.txt").read_text() == "ae\u0301b", "Backspace split a grapheme cluster"
        # With no changes, the retained framebuffer should emit no full repaint.
        session.drain(0.1)
        idle = session.drain(0.25)
        assert len(idle) < 100, f"idle terminal output was not retained ({len(idle)} bytes)"
        session.quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--filter", default="")
    args = parser.parse_args()
    binary = args.binary.resolve()
    linked = subprocess.run(["ldd", str(binary)], capture_output=True, text=True)
    dependencies = linked.stdout + linked.stderr
    static = "not a dynamic executable" in dependencies or "statically linked" in dependencies
    assert linked.returncode == 0 or static, dependencies
    names = set() if static else {line.split()[0] for line in dependencies.splitlines() if line.strip()}
    allowed = {"libc.so.6", "libm.so.6", "libgcc_s.so.1", "linux-vdso.so.1"}
    unexpected = {name for name in names if name not in allowed and not Path(name).name.startswith("ld-linux-")}
    assert not unexpected, f"Unexpected runtime libraries: {unexpected}\\n{dependencies}"
    checks = [recovery, unnamed_discard, buffer_kill, fidelity, external_files, symlinks_and_save_as,
              search_replace_and_buffers, byte_paths_and_checkpoint_failures,
              second_instance, crash_and_signals, word_delete, duplicate_selection, gutter_highlight, graphemes_and_resize]
    for check in checks:
        if args.filter not in check.__name__:
            continue
        with tempfile.TemporaryDirectory(prefix=f"me-{check.__name__}-") as directory:
            check(binary, Path(directory))
        print(f"PASS {check.__name__}", flush=True)
    print("PTY integration checks passed", flush=True)


if __name__ == "__main__":
    main()
