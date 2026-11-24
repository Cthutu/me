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


def startup_modes(binary, folder):
    first = folder / "one.txt"
    second = folder / "two.txt"
    third = folder / "three.txt"
    for path in [first, second, third]:
        path.write_text(path.name)
    with Session(binary, folder) as session:
        session.send("old unnamed work")
        session.quit()
    snapshot = next((folder / "home/.config/me").glob("*/snapshot"))
    assert b"old unnamed work" in snapshot.read_bytes()
    with Session(binary, folder, first.name, second.name) as session:
        session.send(",")
        shown = screen(session)
        assert b"2/2" in shown and b"[unnamed]" not in shown, shown
        session.send(b"\x1b", 0.15)
        session.quit()
    assert b"old unnamed work" not in snapshot.read_bytes()
    with Session(binary, folder) as session:
        session.send(",")
        assert b"2/2" in screen(session), "bare me did not restore continuation"
        session.send(b"\x1b", 0.15)
        session.quit()
    with Session(binary, folder, "+" + third.name, "+" + first.name) as session:
        session.send("iT")
        session.send(b"\x13")
        assert third.read_bytes() == b"Tthree.txt", "+files did not display the first added path"
        session.send(",")
        assert b"3/3" in screen(session), "+files dropped recovered buffers or duplicated paths"
        session.send(b"\x1b", 0.15)
        session.quit()
    previous = snapshot.read_bytes()
    for arguments in [[first.name, "+" + second.name], ["-r", "+" + first.name], ["+"]]:
        result = subprocess.run([str(binary), *arguments], cwd=folder, capture_output=True)
        assert result.returncode == 2, (arguments, result.stderr)
        assert snapshot.read_bytes() == previous, "invalid CLI arguments erased continuation"
    (folder / "+literal").write_bytes(b"LITERAL")
    with Session(binary, folder, "++literal") as session:
        session.send("iL")
        session.send(b"\x13")
        assert (folder / "+literal").read_bytes() == b"LLITERAL"
        session.quit()
    # Failed +opens retain the recovered workspace; plain failed opens erase it.
    with Session(binary, folder, "+.", "+home") as session:
        assert session.process.poll() is None
        session.normal()
        session.send(",")
        assert b"4/4" in screen(session)
        session.send(b"\x1b", 0.15)
        session.quit()
    with Session(binary, folder, ".", "home") as session:
        assert session.process.poll() == 2
    assert not snapshot.exists(), "plain filenames did not erase the old snapshot"
    # Never continue silently when the owned snapshot cannot be erased.
    snapshot.mkdir()
    with Session(binary, folder, first.name, second.name) as session:
        assert session.process.poll() == 2
        assert b"Cannot erase" in session.output
        assert termios.tcgetattr(session.master) == session.original_attributes
    snapshot.rmdir()


def cli_files(binary, folder):
    first = folder / "first.txt"
    second = folder / "second file.txt"
    new = folder / "new.txt"
    first.write_bytes(b"FIRST")
    second.write_bytes(b"SECOND")
    (folder / "alias").symlink_to(first.name)
    with Session(binary, folder, "-r", first.name, second.name, "alias", first.name, new.name) as session:
        session.send("iA")
        session.send(b"\x13")
        assert first.read_bytes() == b"AFIRST", "CLI did not display the first argument"
        assert second.read_bytes() == b"SECOND" and not new.exists()
        session.send(",")
        assert b"3/3" in screen(session), "CLI aliases created duplicate buffers"
        session.send("second\r")
        session.send("iB")
        session.send(b"\x13")
        assert second.read_bytes() == b"BSECOND", "second CLI file was not loaded"
        session.send(",new\r")
        session.send("iN")
        session.send(b"\x13")
        assert new.read_bytes() == b"N", "missing CLI file was not a named buffer"
        session.quit()
    snapshot = next((folder / "home/.config/me").glob("*/snapshot"))
    with Session(binary, folder, "+" + second.name, "+" + first.name) as session:
        session.send(b"\x1b[H")
        session.send("iR")
        session.send(b"\x13")
        assert second.read_bytes() == b"RBSECOND", "restored buffers overrode first CLI argument"
        session.send(",")
        assert b"3/3" in screen(session), "CLI dropped recovered buffers or duplicated paths"
        session.send(b"\x1b", 0.15)
        session.quit()
    (folder / "invalid.bin").write_bytes(b"\xff")
    with Session(binary, folder, "-r", "invalid.bin", ".") as session:
        assert session.process.poll() == 2, bytes(session.output)
        assert b"not valid UTF-8" in session.output and b"non-regular" in session.output
        assert termios.tcgetattr(session.master) == session.original_attributes
    assert not snapshot.exists(), "explicit reset did not erase recovery"
    # Try every argument despite failures, including when the first one fails.
    with Session(binary, folder, "-r", ".", first.name, "invalid.bin", second.name) as session:
        assert b"non-regular" in session.output and b"not valid UTF-8" in session.output
        session.send(b"\x1b[H")
        session.send("iS")
        session.send(b"\x13")
        assert first.read_bytes() == b"SAFIRST", "first successful CLI path was not displayed"
        session.send(",")
        assert b"2/2" in screen(session), "a failed argument stopped later files opening"
        session.send(b"\x1b", 0.15)
        session.quit()
    home_file = folder / "home/home file.txt"
    home_file.write_bytes(b"HOME")
    raw = b"raw\xff.txt"
    with open(os.fsencode(folder) + b"/" + raw, "wb") as stream:
        stream.write(b"RAW")
    with Session(binary, folder, "-r", "~/home file.txt", raw) as session:
        session.send("iH")
        session.send(b"\x13")
        assert home_file.read_bytes() == b"HHOME"
        session.send(",raw\riR")
        session.send(b"\x13")
        with open(os.fsencode(folder) + b"/" + raw, "rb") as stream:
            assert stream.read() == b"RRAW", "CLI changed raw filename bytes"
        session.quit()
    rejected = subprocess.run([str(binary), first.name, "--unknown", second.name],
                              cwd=folder, capture_output=True)
    assert rejected.returncode == 2 and b"[filename ...]" in rejected.stderr


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
    with Session(binary, folder, "+note.txt") as session:
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
    # Explicit reset erases old continuation even if opening the file fails.
    with Session(binary, folder) as session:
        assert b"mixed.txt" not in screen(session)
        assert b"[unnamed]" in screen(session)
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
    with Session(binary, folder, "+outside/chosen.txt") as session:
        session.command("buffers")
        response = session.command("buffer 2")
        # Dirty-cell output can omit unchanged spaces between these words.
        assert b"buffer;" in response, "CLI alias duplicated a recovered buffer"
        session.quit()


def search_origins(binary, folder):
    path = folder / "origins.txt"
    original = b"term term"
    path.write_bytes(original)
    with Session(binary, folder, "-r", path.name) as session:
        session.send(b"\x1b[C" * 5)
        session.send("//term\r")
        session.send("iX")
        session.send(b"\x13")
        assert path.read_bytes() == b"Xterm term", "//term did not search from the beginning"
        session.send(b"\x1a\x13")
        assert path.read_bytes() == original
        session.normal()
        session.send(b"\x1b[C" * 5)
        session.send("/term\r")
        session.send("iY")
        session.send(b"\x13")
        assert path.read_bytes() == b"term Yterm", "/term lost current-caret search origin"
        session.send(b"\x1a\x13")
        session.normal()
        session.send("//term/X\r")
        session.send(b"\x13")
        assert path.read_bytes() == b"X X"
        session.send(b"\x1a\x13")
        session.normal()
        session.send("//term/Y/c\r")
        session.send("nA")
        session.send(b"\x13")
        assert path.read_bytes() == b"term Y"
        session.send(b"\x1a\x13")
        assert path.read_bytes() == original
        session.quit()
    path = folder / "escaped-origin.txt"
    path.write_bytes(b"src/old src/old")
    with Session(binary, folder, "-r", path.name) as session:
        session.send(b"\x1b[C" * 8)
        session.send("//src\\/old\r")
        session.send("iP")
        session.send(b"\x13")
        assert path.read_bytes() == b"Psrc/old src/old"
        session.quit()


def slash_replacement(binary, folder):
    path = folder / "confirm.txt"
    original = b"one one one one\nsrc/old\n"
    path.write_bytes(original)
    with Session(binary, folder, "-r", path.name) as session:
        changed = session.send("/one/XX/c\r")
        assert b"Replace" in changed
        session.send("i\r")  # unrelated keys cannot edit or accept an answer
        session.send("n")
        session.send("y")
        session.send(b"\x13")  # saving is blocked until confirmation stops
        assert path.read_bytes() == original
        session.send("Y")
        session.send(b"\x1b", 0.15)
        session.send(b"\x13")
        partial = b"one XX XX one\nsrc/old\n"
        assert path.read_bytes() == partial
        session.send(b"\x1a\x13")
        assert path.read_bytes() == original, "partial confirmation was not one undo unit"
        session.send(b"\x12\x13")
        assert path.read_bytes() == partial
        session.normal()
        session.send("/one/Z/c\r")
        session.send("A")
        session.send(b"\x13")
        changed_all = b"Z XX XX Z\nsrc/old\n"
        assert path.read_bytes() == changed_all
        session.normal()
        session.send("/src\\/old\r")
        session.send(b"\x13")
        assert path.read_bytes() == changed_all, "escaped slash search became replacement"
        session.normal()
        session.send("/src\\/old/new\r")
        session.send(b"\x13")
        assert path.read_bytes() == b"Z XX XX Z\nnew\n"
        session.normal()
        session.send("/XX/wrong/g\r")
        session.normal()
        session.send(b"\x13")
        assert path.read_bytes() == b"Z XX XX Z\nnew\n", "obsolete g flag was accepted"
        session.quit()
    unicode_path = folder / "unicode.txt"
    original_unicode = "\ufeffé-é-é\r\n".encode()
    unicode_path.write_bytes(original_unicode)
    with Session(binary, folder, "-r", unicode_path.name) as session:
        session.send("/é/長/c\r")
        session.send("nYa")
        session.send(b"\x13")
        assert unicode_path.read_bytes() == "\ufeffé-長-長\r\n".encode()
        session.send(b"\x1a\x13")
        assert unicode_path.read_bytes() == original_unicode
        session.quit()


def confirmation_recovery(binary, folder):
    path = folder / "recover-confirm.txt"
    original = b"a a a a"
    path.write_bytes(original)
    with Session(binary, folder, "-r", path.name) as session:
        session.send("/a/XX/c\r")
        session.send("yy")
        os.kill(session.process.pid, signal.SIGTERM)
        session.wait()
    assert path.read_bytes() == original
    with Session(binary, folder) as session:
        session.send(b"\x13")
        assert path.read_bytes() == b"XX XX a a"
        session.send(b"\x1a\x13")
        assert path.read_bytes() == original, "partial grouped checkpoint did not undo as one operation"
        session.send(b"\x12\x13")
        assert path.read_bytes() == b"XX XX a a"
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
        session.normal()
        session.send("/one/word\r")
        session.send(b"\x13")
        assert path.read_bytes() == b"Xword two ONE\r\nthree word"
        session.send(b"\x1a")
        session.send(b"\x13")
        assert path.read_bytes() == original, "replace-all was not a single undo operation"
        session.normal()
        session.send("/one/\r")
        session.send(b"\x13")
        assert path.read_bytes() == b"X two ONE\r\nthree "
        session.quit()
    with Session(binary, folder, "-r") as session:
        session.send("alpha")
        session.quit()
    with Session(binary, folder, "+missing/beta.txt") as session:
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
    with Session(binary, folder, "+alpha.txt") as session:
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


def undo_caret(binary, folder):
    path = folder / "caret.txt"
    path.write_bytes(b"abcd")
    with Session(binary, folder, "-r", "caret.txt") as session:
        session.send(b"\x1b[F")
        session.send(b"\x7f")
        session.quit()
    # Caret hints must survive continuation, not merely an in-memory undo.
    with Session(binary, folder) as session:
        session.send(b"\x1a")
        session.send("iX")
        session.send(b"\x13")
        assert path.read_bytes() == b"abcdX", "undo did not restore the pre-Backspace caret"
        session.send(b"\x1a")
        session.send(b"\x12")
        session.send("iY")
        session.send(b"\x13")
        assert path.read_bytes() == b"abcdXY", "redo did not restore the post-insertion caret"
        session.quit()

    # Convert a real checkpoint to the previous envelope/history format.
    # The new binary must recover it, then write v4 on its next checkpoint.
    snapshot = next((folder / "home/.config/me").glob("*/snapshot"))
    data = snapshot.read_bytes()
    offset = 0
    def number():
        nonlocal offset
        value, = struct.unpack_from("<Q", data, offset)
        offset += 8
        return value
    def text():
        nonlocal offset
        count = number()
        value = data[offset:offset + count]
        offset += count
        return value
    def encoded(value):
        return struct.pack("<Q", len(value)) + value
    assert text() == b"ME/MS1/4"
    old = bytearray(encoded(b"ME/MS1/1") + encoded(text()))
    documents = number()
    old.extend(struct.pack("<Q", documents))
    for _ in range(documents):
        old.extend(encoded(text()) + encoded(text()))
        old.extend(struct.pack("<QQ", number(), number()))
        old.extend(encoded(text()))
        applied, count = number(), number()
        old.extend(struct.pack("<QQ", applied, count))
        for _ in range(count):
            old.extend(struct.pack("<Q", number()) + encoded(text()) + encoded(text()))
            number()
            number()
    view_start = offset
    views = number()
    for _ in range(views * 8):
        number()
    number()  # active view; v3 access-order extension follows this
    access_start = offset
    old.extend(data[view_start:access_start])
    checksum = 14695981039346656037
    for byte in old:
        checksum = ((checksum ^ byte) * 1099511628211) & ((1 << 64) - 1)
    snapshot.write_bytes(old + struct.pack("<Q", checksum))
    with Session(binary, folder) as session:
        assert b"version or folder mismatch" not in session.output
        session.send(b"\x1a")
        session.send(b"\x13")
        assert path.read_bytes() == b"abcdX", "legacy history failed to recover"
        session.quit()
    assert snapshot.read_bytes()[8:16] == b"ME/MS1/4", "legacy continuation was not upgraded"
    # V2 already has caret hints, but no access-order tail.
    old2 = encoded(b"ME/MS1/2") + data[16:access_start]
    checksum = 14695981039346656037
    for byte in old2:
        checksum = ((checksum ^ byte) * 1099511628211) & ((1 << 64) - 1)
    snapshot.write_bytes(old2 + struct.pack("<Q", checksum))
    with Session(binary, folder) as session:
        assert b"version or folder mismatch" not in session.output
        session.quit()
    assert snapshot.read_bytes()[8:16] == b"ME/MS1/4", "v2 continuation was not upgraded"

    # V3 contains MRU access order but no pane tree.
    old3 = encoded(b"ME/MS1/3") + data[16:-24]
    checksum = 14695981039346656037
    for byte in old3:
        checksum = ((checksum ^ byte) * 1099511628211) & ((1 << 64) - 1)
    snapshot.write_bytes(old3 + struct.pack("<Q", checksum))
    with Session(binary, folder) as session:
        assert b"version or folder mismatch" not in session.output
        session.quit()
    assert snapshot.read_bytes()[8:16] == b"ME/MS1/4", "v3 continuation was not upgraded"


def word_delete(binary, folder):
    path = folder / "words.txt"
    path.write_bytes(b"alpha beta")
    for control_backspace in (b"\x1b[127;5u", b"\x1b[8;5u", b"\x08"):
        path.write_bytes(b"alpha beta")
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


def buffer_picker(binary, folder):
    alpha = folder / "alpha.txt"
    beta = folder / "BetaTest.n"
    gamma = folder / "gamma.txt"
    for path, content in [(alpha, b"alpha"), (beta, b"beta"), (gamma, b"gamma")]:
        path.write_bytes(content)
    with Session(binary, folder, "-r", alpha.name) as session:
        session.command("e BetaTest.n")
        session.command("e gamma.txt")
        session.send(",")
        shown = screen(session)
        assert shown.index(b"gamma.txt") < shown.index(b"BetaTest.n") < shown.index(b"alpha.txt")
        assert b"Buffers" in shown and b"3/3" in shown
        session.send("\r")  # second row is the most recently used other buffer
        session.send("iB")
        session.send(b"\x13")
        assert beta.read_bytes() == b"Bbeta", (beta.read_bytes(), gamma.read_bytes(), screen(session))
        session.send(",\r")
        session.send("iC")
        session.send(b"\x13")
        assert gamma.read_bytes() == b"Cgamma"
        session.command("buffer 1")
        session.send("iQ")
        session.normal()
        session.send(",ignored")
        session.send(b"\x1b", 0.15)
        session.send("iR")
        session.send(b"\x13")
        assert alpha.read_bytes() == b"QRalpha", "cancel changed caret or leaked query"
        session.send(",btt\r")
        session.send("iF")
        session.send(b"\x13")
        assert beta.read_bytes() == b"BFbeta", "case-insensitive subsequence did not select BetaTest"
        session.send(",zzzzhjklq,")
        assert b"No matches" in screen(session)
        session.send("\r")
        assert b"No matches" in screen(session), "Enter dismissed an empty picker"
        session.send(b"\x7f" * 10)
        assert b"3/3" in screen(session), screen(session)
        # A release must not move the initial selection a second time.
        session.send(b"\x1b", 0.15)
        session.send(",")
        session.send(b"\x1b[1;1:1B\x1b[1;1:3B")  # row 1 -> row 2, not wrapped
        session.send(b"\x1b[1;1:1A\x1b[1;1:3A")
        session.send("\r")
        session.send("iS")
        session.send(b"\x13")
        assert alpha.read_bytes() == b"QRSalpha", "picker cursor actions selected the wrong row"
        session.send(",")
        fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 8, 20, 0, 0))
        session.drain(0.15)
        session.send(b"\x1b[6~\x1b[5~")
        fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        session.drain(0.15)
        session.send(b"\x1b", 0.15)
        session.send("iD")
        session.normal()
        session.send(",")
        session.send(b"\x1b[A")  # current buffer is first in access order
        changed = session.send(b"\x17")
        assert b"unsaved" in screen(session), "Ctrl W discarded unsaved work"
        assert alpha.read_bytes() == b"QRSalpha"
        session.send(b"\x1b", 0.15)
        session.send(b"\x1a\x13")
        assert alpha.read_bytes() == b"QRSalpha"
        # Associated control text must not close the fallback buffer as well.
        session.send(",")
        session.send(b"\x1b[A")
        session.send(b"\x1b[119;5;23u\x1b[119;5:3u")
        assert b"2/2" in screen(session)
        session.send(b"\x1b", 0.15)
        session.send(",")
        session.send(b"\x1b[A\x17\x1b", 0.15)  # close current Beta in picker
        session.send("iG")
        session.send(b"\x13")
        assert gamma.read_bytes() == b"CGgamma"
        session.send(",\x17\x1b", 0.15)  # last clean buffer -> fresh empty buffer
        session.send(",\r")
        assert b"[unnamed]" in screen(session)
        session.quit()


def await_file_picker(session, *, timeout=8):
    finish = time.monotonic() + timeout
    while time.monotonic() < finish:
        shown = screen(session)
        if b"Files" in shown and b"scanning" not in shown and b"filtering" not in shown:
            return shown
        session.drain(0.05)
    raise AssertionError(("file discovery did not finish", screen(session)))


def file_picker(binary, folder):
    with tempfile.TemporaryDirectory(prefix="me-linked-") as linked_name:
        (folder / "src").mkdir()
        (folder / "src" / "AlphaBeta.n").write_bytes(b"ALPHA_FILE")
        (folder / "src" / "Straße.n").write_bytes(b"UNICODE_FILE")
        (folder / "src" / "drop.tmp").write_bytes(b"IGNORED_FILE")
        (folder / "src" / "keep.tmp").write_bytes(b"KEPT_FILE")
        (folder / "src" / ".gitignore").write_text("!keep.tmp\n")
        (folder / "build").mkdir()
        (folder / "build" / "output.n").write_bytes(b"BUILD_FILE")
        (folder / ".hidden.n").write_bytes(b"HIDDEN_FILE")
        (folder / ".gitignore").write_text("*.tmp\nbuild/\n")
        (folder / "alias.n").symlink_to("src/AlphaBeta.n")
        (folder / "cycle").symlink_to(".", target_is_directory=True)
        linked = Path(linked_name)
        (linked / "external.n").write_bytes(b"EXTERNAL_FILE")
        (linked / "back").symlink_to(folder, target_is_directory=True)
        (folder / "linked").symlink_to(linked, target_is_directory=True)
        (folder / "broken").symlink_to("absent")
        os.mkfifo(folder / "special")
        raw = os.fsencode(folder) + b"/raw-\xff\x1b.n"
        with open(raw, "wb") as stream:
            stream.write(b"RAW_FILE")
        base = folder / "base.txt"
        base.write_bytes(b"base")
        with Session(binary, folder, base.name) as session:
            session.send("iUNSAVED")
            session.normal()
            session.send(" ")
            session.drain(0.2)
            assert b"Space menu" not in screen(session)
            session.drain(1.1)
            assert b"Space menu" in screen(session) and b"Open file" in screen(session)
            session.send(" ")
            shown = await_file_picker(session)
            assert b"Files" in shown and b"AlphaBeta.n" in shown and b"keep.tmp" in shown, shown
            for included in [b"drop.tmp", b"output.n", b".hidden.n", b".gitignore"]:
                assert included in shown, (included, shown)
            for excluded in [b"cycle/", b"broken", b"special"]:
                assert excluded not in shown, (excluded, shown)
            fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 8, 20, 0, 0))
            session.drain(0.1)
            fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
            session.drain(0.1)
            session.send("src/abn")
            session.drain(0.2)
            assert b"1/" in screen(session), screen(session)
            session.send(b"\x1b", 0.15)
            session.send("iX")  # cancellation preserved the originating caret
            session.send(b"\x13")
            assert base.read_bytes() == b"UNSAVEDXbase"
            session.command("files")
            await_file_picker(session)
            session.send("strasse")
            session.drain(0.2)
            session.send("\r")
            assert b"Files" not in screen(session)
            session.send("iY")
            session.send(b"\x13")
            assert (folder / "src" / "Straße.n").read_bytes() == b"YUNICODE_FILE"
            session.send(b"\x1b[32u\x1b[32;1:3u\x1b[32u\x1b[32;1:3u")
            await_file_picker(session)
            session.send("alias.n")
            session.drain(0.2)
            session.send("\r")
            session.send("iZ")
            session.send(b"\x13")
            assert (folder / "src" / "AlphaBeta.n").read_bytes() == b"ZALPHA_FILE"
            session.command("files")
            await_file_picker(session)
            session.send("src/alphabeta")
            session.drain(0.2)
            session.send("\r")
            session.send(",")
            assert b"3/3" in screen(session), "file picker duplicated an already-open inode alias"
            session.send(b"\x1b", 0.15)
            session.send(" ")
            session.send(b"\x1b", 0.15)
            assert b"Space menu" not in screen(session)
            session.send("  ")
            await_file_picker(session)
            session.send("linked/external")
            session.drain(0.2)
            assert b"1/" in screen(session), screen(session)
            session.send("\r")
            session.send("iE")
            session.send(b"\x13")
            assert (linked / "external.n").read_bytes() == b"EEXTERNAL_FILE"
            session.command("files")
            await_file_picker(session)
            session.send("raw-")
            session.drain(0.2)
            session.send("\r")
            session.send("iB")
            session.send(b"\x13")
            with open(raw, "rb") as stream:
                assert stream.read() == b"BRAW_FILE"
            session.quit()


def file_picker_stale_and_cancel(binary, folder):
    base = folder / "base.txt"
    base.write_bytes(b"base")
    gone = folder / "vanished.n"
    gone.write_bytes(b"gone")
    with Session(binary, folder, base.name) as session:
        session.command("files")
        await_file_picker(session)
        session.send("vanished")
        session.drain(0.15)
        gone.unlink()
        session.send("\r")
        shown = screen(session)
        assert b"Files" in shown and b"no longer exists" in shown, shown
        assert not gone.exists()
        os.mkfifo(gone)
        session.send("\r")
        assert b"no longer a regular file" in screen(session)
        session.send(b"\x17")  # file candidates must never be treated as buffer IDs
        assert b"Files" in screen(session)
        session.send(b"\x1b", 0.15)
        session.send("iX")
        session.send(b"\x13")
        assert base.read_bytes() == b"Xbase"
        session.quit()
    unreadable = folder / "unreadable"
    unreadable.mkdir(mode=0)
    try:
        with Session(binary, folder, base.name) as session:
            session.send("  ")
            shown = await_file_picker(session)
            assert b"incomplete" in shown and b"Cannot read" in shown, shown
            session.send(b"\x1b", 0.15)
            session.quit()
    finally:
        unreadable.chmod(0o755)
    (folder / "large").mkdir()
    for index in range(5000):
        (folder / "large" / f"candidate-{index:05}.n").touch()
    with Session(binary, folder, base.name) as session:
        before = len(list(Path(f"/proc/{session.process.pid}/fd").iterdir()))
        for _ in range(3):
            session.send("  ", 0.04)
            children_path = Path(f"/proc/{session.process.pid}/task/{session.process.pid}/children")
            children = [int(value) for value in children_path.read_text().split()]
            assert children, "discovery did not start a cancellable worker"
            for child in children:
                os.kill(child, signal.SIGSTOP)
            start = time.monotonic()
            session.send("quick-query", 0.05)
            assert b"quick-query" in screen(session), "typing blocked on discovery"
            session.send(b"\x1b", 0.15)
            assert b"Files" not in screen(session), "Escape failed to dismiss discovery"
            session.drain(0.15)
            assert time.monotonic() - start < 1.5
            assert not children_path.read_text().strip(), "cancelled worker was not reaped"
        after = len(list(Path(f"/proc/{session.process.pid}/fd").iterdir()))
        assert before == after, ("discovery descriptor leak", before, after)
        session.send("iR")
        session.send(b"\x13")
        assert base.read_bytes() == b"RXbase"
        session.quit()


def buffer_picker_close_selected(binary, folder):
    for name in ["alpha.txt", "beta.txt", "gamma.txt"]:
        (folder / name).write_bytes(name.encode())
    with Session(binary, folder, "alpha.txt", "beta.txt", "gamma.txt") as session:
        session.command("buffer 3")
        session.send("iX")
        session.normal()
        session.send(",")
        session.send(b"\x1b[119;5;23u\x1b[119;5:3u")
        shown = screen(session)
        assert b"Buffers" in shown and b"2/2" in shown and b"alpha.txt" not in shown, shown
        session.send("gamma")
        session.send(b"\x17")
        shown = screen(session)
        assert b"unsaved" in shown and b"Buffers" in shown, "dirty refusal dismissed the picker"
        session.send(b"\x7f" * 5)
        session.send("no-match")
        session.send(b"\x17")
        assert b"No matches" in screen(session), "empty picker closed a buffer"
        session.send(b"\x7f" * 8)
        session.send("beta")
        session.send(b"\x17")
        shown = screen(session)
        assert b"Buffers" in shown and b"No matches" in shown, "close lost the query or popup"
        session.send(b"\x7f" * 4)
        assert b"1/1" in screen(session) and b"gamma.txt" in screen(session)
        session.send(b"\x1b", 0.15)
        session.send(b"\x13")
        assert (folder / "gamma.txt").read_bytes() == b"Xgamma.txt"
        session.send(",\x17")
        shown = screen(session)
        assert b"Buffers" in shown and b"[unnamed]" in shown and b"gamma.txt" not in shown
        session.send(b"\x1b", 0.15)
        session.quit()


def buffer_picker_preview(binary, folder):
    first = folder / "alpha.txt"
    second = folder / "beta.txt"
    first.write_bytes(b"ALPHA_ONLY\nfirst line two")
    second.write_bytes(b"BETA_ONLY\nsecond line two")
    with Session(binary, folder, first.name, second.name) as session:
        def preview():
            return "\n".join(line[34:74] for line in screen(session).decode().splitlines()[4:21])
        session.send(",")
        assert "Preview (read-only)" in preview() and "BETA_ONLY" in preview(), preview()
        assert "ALPHA_ONLY" not in preview()
        session.send(b"\x1b[A")
        assert "ALPHA_ONLY" in preview() and "BETA_ONLY" not in preview(), preview()
        session.send(b"\x1b", 0.15)
        session.send("iX")
        session.send(b"\x13")
        assert first.read_bytes().startswith(b"XALPHA_ONLY"), "preview switched the active buffer"
        session.send(",beta\r")
        session.send("iUNSAVED_")
        session.normal()
        session.send(",beta")
        assert "UNSAVED_BETA_ONLY" in preview(), "preview read disk instead of unsaved text"
        assert second.read_bytes().startswith(b"BETA_ONLY")
        fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 8, 40, 0, 0))
        session.drain(0.15)
        assert b"Preview (read-only)" not in screen(session, 40, 8)
        fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        session.drain(0.15)
        assert "UNSAVED_BETA_ONLY" in preview()
        session.send("zzzz")
        assert "No selection" in preview() and "BETA_ONLY" not in preview(), preview()
        session.send(b"\x1b", 0.15)
        session.quit("q!")
    assert second.read_bytes() == b"BETA_ONLY\nsecond line two"


def buffer_picker_recovery(binary, folder):
    for name in ["alpha.txt", "beta.txt", "gamma.txt"]:
        (folder / name).write_text(name)
    with Session(binary, folder, "-r", "alpha.txt") as session:
        session.command("e beta.txt")
        session.command("e gamma.txt")
        session.send(",ap\r")  # alpha, gamma, beta
        session.quit()
    with Session(binary, folder) as session:
        session.send(",")
        shown = screen(session)
        assert shown.index(b"alpha.txt") < shown.index(b"gamma.txt") < shown.index(b"beta.txt")
        session.send("\r")
        session.send("iR")
        session.send(b"\x13")
        assert (folder / "gamma.txt").read_bytes() == b"Rgamma.txt"
        session.quit()


def buffer_picker_unicode_bytes(binary, folder):
    unicode_file = folder / "Straße_Σ.txt"
    unicode_file.write_bytes(b"unicode")
    raw = os.fsencode(folder) + b"/odd\xff\x1b[31m.txt"
    with open(raw, "wb") as stream:
        stream.write(b"raw")
    with Session(binary, folder, "-r", unicode_file.name) as session:
        session.normal()
        session.send(":e odd\t\r")
        session.send(",STRASSEσ\r")
        session.send("iU")
        session.send(b"\x13")
        assert unicode_file.read_bytes() == b"Uunicode"
        session.send(",odd")
        assert b"\x1b[31m" not in session.output, "filename control escaped popup sanitisation"
        session.send("\r")
        session.send("iR")
        session.send(b"\x13")
        with open(raw, "rb") as stream:
            assert stream.read() == b"Rraw"
        session.quit()


def enhanced_key_actions(binary, folder):
    target = folder / "arrows.txt"
    target.write_bytes(b"abcd\nEFGH\nijkl\nMNOP\n")
    prompt_target = folder / "promp-t"
    prompt_target.write_bytes(b"prompt")
    with Session(binary, folder, "-r", "arrows.txt") as session:
        session.send("i")
        session.send(b"\x1b[1;1:1C\x1b[1;1:3C")
        session.send("X")
        session.send(b"\x13")
        assert target.read_bytes() == b"aXbcd\nEFGH\nijkl\nMNOP\n", target.read_bytes()

        session.send(b"\x1b[1;5:1H\x1b[1;5:3H")
        session.send("i")
        session.send(b"\x1b[1;1:1B\x1b[1;1:3B")
        session.send("D")
        session.send(b"\x13")
        assert target.read_bytes() == b"aXbcd\nDEFGH\nijkl\nMNOP\n"

        session.send(b"\x1b[1;5:1H\x1b[1;5:3H")
        session.send("i")
        session.send(b"\x1b[1;1:1B\x1b[1;1:2B\x1b[1;1:3B")
        session.send("R")
        session.send(b"\x13")
        assert target.read_bytes() == b"aXbcd\nDEFGH\nRijkl\nMNOP\n"

        session.send(b"\x1b[1;5:1F\x1b[1;5:3F")
        session.send("i")
        session.send(b"\x1b[1;1:1A\x1b[1;1:3A")
        session.send("U")
        session.send(b"\x13")
        assert target.read_bytes() == b"aXbcd\nDEFGH\nRijkl\nUMNOP\n"

        session.send(b"\x1b[1;5:1H\x1b[1;5:3H")
        session.send("i")
        session.send(b"\x1b[1;1:1F\x1b[1;1:3F\x1b[1;1:1D\x1b[1;1:3D")
        session.send("L")
        session.send(b"\x13")
        expected = b"aXbcLd\nDEFGH\nRijkl\nUMNOP\n"
        assert target.read_bytes() == expected

        session.send(b"\x1b[1;5:1H\x1b[1;5:3H")
        session.send(b"\x1b[1;2:1C\x1b[1;2:3C")  # Shift+Right selects one character
        session.send(b"\x1b[127;5:1u\x1b[127;5:3u")
        session.send(b"\x13")
        assert target.read_bytes() == expected[1:]
        session.send(b"\x1a\x13")
        assert target.read_bytes() == expected

        session.send(b"\x1b[1;5:1H\x1b[1;5:3H")
        session.send("i")
        session.send(b"\x1b[3;1:1~\x1b[3;1:3~")
        session.send(b"\x13")
        assert target.read_bytes() == expected[1:]

        session.send(":e prompt")
        session.send(b"\x1b[1;1:1D\x1b[1;1:3D")
        session.send("-\r")
        session.send("iT")
        session.send(b"\x13")
        assert prompt_target.read_bytes() == b"Tprompt"
        assert not (folder / "prom-pt").exists()
        session.quit()


def screen(session, width=80, height=24):
    # Reconstruct the ASCII diagnostic area; retained rendering may only
    # write changed cells, not complete phrases or their separating spaces.
    cells = [[" "] * width for _ in range(height)]
    row = column = 0
    for part in re.split(r"(\x1b\[[0-?]*[ -/]*[@-~])", session.output.decode("utf-8", "replace")):
        if part.startswith("\x1b["):
            if part[-1] in "Hf":
                values = part[2:-1].split(";")
                row = int(values[0] or "1") - 1
                column = int(values[1] or "1") - 1 if len(values) > 1 else 0
            continue
        for character in part:
            if character == "\n":
                row, column = row + 1, 0
            elif character == "\r":
                column = 0
            elif ord(character) >= 32:
                if 0 <= row < height and 0 <= column < width:
                    cells[row][column] = character
                column += 1
    return "\n".join("".join(line) for line in cells).encode()


def keyboard_diagnostics(binary, folder):
    path = folder / "keys.txt"
    original = b"unchanged"
    path.write_bytes(original)
    with Session(binary, folder, "-r", path.name) as session:
        assert b"\x1b[>31u\x1b[?u\x1b[c" in session.output, "keyboard/DA probes missing"
        session.command("keys")
        assert b"probe pending" in screen(session)
        session.send(b"\x1b[?1;2c")
        assert b"probe complete" in screen(session)
        assert b"Text codepoint=49" not in screen(session), "DA parameters leaked into text events"
        session.send(b"\x1b[?0u")
        assert b"Kitty reply flags=0" in screen(session), "zero reply was confused with no reply"
        session.send(b"\x1b[?7u")
        assert b"Kitty reply flags=7" in screen(session)
        assert b"physical=no releases=no modifiers=yes" in screen(session), "partial flags overclaimed held keys"
        session.send(b"\x1b[?31u")
        assert b"physical=yes releases=yes modifiers=yes" in screen(session)
        session.send(b"\x1b[104;5u")
        assert b"Key H press mods=4 Ctrl=yes" in screen(session)
        session.send(b"\x1b[127;5u")
        assert b"Key Backspace press mods=4 Ctrl=yes" in screen(session)
        session.send(b"\x1b[104;5:3u")
        assert b"Key H release" in screen(session)
        session.send(b"\x13")
        session.send("iqhjklx")
        assert path.read_bytes() == original, "diagnostic keys edited or saved the buffer"
        session.send(b"\x08")
        assert b"legacy 0x08" in screen(session), "legacy Ctrl+H ambiguity was hidden"
        session.send(b"\x1b[1;1:1C\x1b[1;1:2C\x1b[1;1:3C")
        assert b"Right release" in screen(session), "cursor release was not diagnosed"
        assert b"Right repeat" in screen(session), "cursor repeat was not diagnosed"
        fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 8, 20, 0, 0))
        session.drain(0.15)
        session.send(b"\x1b[6;3~\x1b[5;3~")  # Alt+Page Down/Up scroll the diagnostic.
        fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        session.drain(0.15)
        session.send(b"\x1b", 0.15)
        session.send("iZ")
        session.send(b"\x13")
        assert path.read_bytes() == b"Z" + original, "diagnostic exit swallowed the next key"
        session.quit()
        assert b"\x1b[<u" in session.output, "keyboard mode was not restored"


def hjkl_and_line_selection(binary, folder):
    path = folder / "hjkl.txt"
    original = "a👩‍💻bc\nx\na👩‍💻bc"
    path.write_text(original)
    with Session(binary, folder, "-r", path.name) as session:
        session.send("2ljjkkhliX")
        session.send(b"\x13")
        assert path.read_text() == "a👩‍💻Xbc\nx\na👩‍💻bc", "hjkl lost grapheme/preferred-column motion"
        session.send(b"\x1a\x13")
        assert path.read_text() == original
        session.send(b"\x1b[1;5H")
        session.send("2qx")
        session.send(b"\x13")
        assert path.read_text() == "a👩‍💻bc", "2q did not select two complete lines"
        session.send(b"\x1a\x13")
        session.send(b"\x1b[1;5H")
        session.send("qqx")
        session.send(b"\x13")
        assert path.read_text() == "a👩‍💻bc", "repeated q did not extend the line selection"
        session.send(b"\x1a\x13")
        session.send(b"\x1b[1;5H")
        session.send("iqhjkl")
        session.send(b"\x13")
        assert path.read_text() == "qhjkl" + original, "Normal bindings leaked into Insert"
        session.normal()
        session.send("/qhjkl\r")
        session.send("iZ")
        session.send(b"\x13")
        assert path.read_text() == "Zqhjkl" + original, "search prompt did not retain literal qhjkl"
        session.quit()


def leader_overlay(binary, folder):
    path = folder / "leader-overlay.txt"
    original = b"".join(f"visible-row-{index:02}\n".encode() for index in range(70))
    path.write_bytes(original)
    with Session(binary, folder, "-r", path.name) as session:
        before = screen(session)
        session.send(" ")
        session.drain(0.15)
        assert b"Space menu" not in screen(session)
        session.drain(1.1)
        shown = screen(session)
        assert b"Space menu" in shown and b"[ SPC ]" in shown and b"Open file" in shown, shown
        assert shown.splitlines()[:14] == before.splitlines()[:14], "menu resized or scrolled the document"
        assert all(b"visible-row-" not in row for row in shown.splitlines()[15:]), "document leaked through menu"
        # Both press repeats and releases must leave the delayed menu open.
        session.send(b"\x1b[32;1:2;32u\x1b[32;1:3u")
        assert b"Space menu" in screen(session) and b"Files" not in screen(session)
        fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 4, 12, 0, 0))
        session.drain(0.15)
        assert session.process.poll() is None
        fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        session.drain(0.15)
        assert b"Space menu" in screen(session)
        session.send(b"\x1b", 0.15)
        assert screen(session) == before, "cancelling the overlay did not restore the editor"
        session.send("  ")
        await_file_picker(session)
        session.send(b"\x1b", 0.15)
        session.send(" b")  # illustrative submenu remains unassigned
        assert b"Unknown Space sequence" in screen(session)
        session.normal()
        session.send("iX")
        session.send(b"\x13")
        assert path.read_bytes() == b"X" + original
        session.quit()


def control_hjkl(binary, folder):
    path = folder / "control-hjkl.txt"
    tail = b"".join(f"line-{index:03}\n".encode() for index in range(1, 71))
    path.write_bytes(b"one two three\n" + tail)
    with Session(binary, folder, "-r", path.name) as session:
        session.send("2")
        session.send(b"\x1b[108;5;12u\x1b[108;5:3u")
        session.send("iX")
        session.send(b"\x1b[104;5;8u\x1b[104;5:3u")
        session.send("Y")  # Ctrl+H preserves Insert and does not delete a word
        session.send(b"\x13")
        assert path.read_bytes() == b"one two YXthree\n" + tail
        session.send(b"\x1b[1;5H")
        session.send(b"\x1b[108;6;12u\x1b[108;6:3u")
        session.send("iR")
        session.send(b"\x13")
        assert path.read_bytes() == b"Rtwo YXthree\n" + tail, "Ctrl+Shift+L did not extend selection"
        session.send(b"\x1b[1;5H")
        session.send("3")
        session.send(b"\x1b[106;5;10u\x1b[106;5:2;10u\x1b[106;5:3u")
        shown = screen(session)
        assert b"line-004" in shown.splitlines()[0], shown
        session.send(b"\x1b[107;5;11u\x1b[107;5:3u")
        assert b"line-003" in screen(session).splitlines()[0]
        session.send("iQ")  # scrolling left the caret on the first line
        session.send(b"\x13")
        assert path.read_bytes() == b"QRtwo YXthree\n" + tail, "scrolling moved the caret or inserted a control character"
        other = folder / "other.txt"
        other.write_bytes(b"other")
        session.command("e other.txt")
        session.send(",")
        session.send(b"\x1b[107;5;11u\x1b[107;5:3u")
        session.send("\r")
        session.send("iB")
        session.send(b"\x13")
        assert other.read_bytes() == b"Bother", "Ctrl+K did not select the previous popup row"
        session.send(",")
        session.send(b"\x1b[107;5u\x1b[106;5;10u\x1b[106;5:3u")
        session.send("\r")
        session.send("iS")
        session.send(b"\x13")
        assert path.read_bytes() == b"QSRtwo YXthree\n" + tail, ("Ctrl+J did not select the next popup row", path.read_bytes()[:35], other.read_bytes(), screen(session))
        session.quit()


def duplicate_selection(binary, folder):
    path = folder / "duplicate.txt"
    block = b"one\r\ntwo\n"
    path.write_bytes(block + b"three")
    with Session(binary, folder, "-r", "duplicate.txt") as session:
        session.send("2q")
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


def command_completion(binary, folder):
    (folder / "base.txt").write_bytes(b"base")
    (folder / "alpha.txt").write_bytes(b"alpha")
    (folder / "alpine.txt").write_bytes(b"alpine")
    with Session(binary, folder, "-r", "base.txt") as session:
        changed = session.send(":ww\t")
        assert b"ww" in changed and b"\x1b[24;" in changed
        session.normal()
        session.send(":\t")
        changed = session.send("e")
        assert b"\x1b[24;" in changed, "command-entry line moved away from the bottom"
        session.send("z")  # zero matches must not execute or dismiss the list
        session.send("\r")
        assert session.process.poll() is None
        session.send(b"\x7f")
        session.send("\r")  # accept e; Escape cancels the still-open prompt
        session.send(b"\x1b", 0.15)
        session.normal()
        session.send(":bu\t")
        session.send("s")
        session.send("\r")
        session.send("\r")  # execute buffers only after accepting its name
        session.normal()
        session.send(":e\t")  # exact command, not filename completion yet
        session.send(" al\t")
        changed = session.send("ha")  # 'alp' -> 'alpha', keeping the one-match list open
        assert b"\x1b[24;" in changed
        session.send("\r")
        session.send("\r")
        session.send("iC")
        session.send(b"\x13")
        assert (folder / "alpha.txt").read_bytes() == b"Calpha"
        assert not (folder / "alpha").exists()
        session.quit()


def live_completion_filter(binary, folder):
    for name in ["base", "alpha", "alpine", "another"]:
        (folder / (name + ".txt")).write_text(name)
    (folder / "nested").mkdir()
    (folder / "nested/deep.txt").write_bytes(b"deep")
    with Session(binary, folder, "-r", "base.txt") as session:
        session.send(":e al\t")
        session.send("z")
        session.send("\r")
        session.send(b"\x1b[B\t")  # navigation with no matches must be harmless
        assert not (folder / "alpz").exists()
        assert session.process.poll() is None
        session.send(b"\x7f\x7f\x7f")  # widen all the way back to 'a'
        session.send("lpi")
        fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 2, 8, 0, 0))
        session.drain(0.15)
        fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        changed = session.drain(0.15)
        assert b"\x1b[24;" in changed
        session.send("\r")
        session.send("\r")
        session.send("iL")
        session.send(b"\x13")
        assert (folder / "alpine.txt").read_bytes() == b"Lalpine"
        assert not (folder / "alpi").exists()
        session.normal()
        session.send(":e \t")
        session.send("nested/")  # entering a folder refreshes the candidate snapshot
        session.send("dee")
        session.send("\r")
        session.send("\r")
        session.send("iN")
        session.send(b"\x13")
        assert (folder / "nested/deep.txt").read_bytes() == b"Ndeep"
        session.quit()


def file_completion(binary, folder):
    first = folder / "first.txt"
    first.write_bytes(b"first")
    (folder / "alias.txt").symlink_to("first.txt")
    files = folder / "files"
    files.mkdir()
    for name, data in [("alpha.txt", b"alpha"), ("alpine.txt", b"alpine"),
                       ("unique name.txt", b"unique"), (".secret", b"hidden")]:
        (files / name).write_bytes(data)
    (files / "nested").mkdir()
    deep = files / "nested/deep.txt"
    deep.write_bytes(b"deep")
    (files / "invalid.txt").write_bytes(b"\xff")
    with Session(binary, folder, "-r", "first.txt") as session:
        session.send("idirty")
        session.normal()
        changed = session.send(":e files/uni\t")
        assert b"unique" in changed and b"name.txt" in changed
        session.send("\r")
        session.send("iU")
        session.send(b"\x13")
        assert (files / "unique name.txt").read_bytes() == b"Uunique"
        session.normal()
        changed = session.send(":e files/al\t")
        assert b"alpha.txt" in changed and b"alpine.txt" in changed
        session.send(b"\x1b[B")
        session.send("\r")  # choose, without executing :e yet
        session.send("\r")
        session.send("iP")
        session.send(b"\x13")
        assert (files / "alpine.txt").read_bytes() == b"Palpine"
        session.normal()
        session.send(":e files/al\t")
        session.send(b"\x1b", 0.15)  # dismiss only the list, retaining 'files/alp'
        session.send("ha.txt\r")
        session.send("iA")
        session.send(b"\x13")
        assert (files / "alpha.txt").read_bytes() == b"Aalpha"
        session.normal()
        changed = session.send(":e files/ne\t")
        assert b"nested/" in changed
        session.send("deep\t\r")
        session.send("iD")
        session.send(b"\x13")
        assert deep.read_bytes() == b"Ddeep"
        session.normal()
        changed = session.send(":e files/nope\t")
        assert all(word in changed for word in [b"No", b"filename", b"match"])
        assert not (files / "nope").exists()
        session.command("e created.txt")
        session.send("new")  # new empty buffers start in Insert
        session.send(b"\x13")
        assert (folder / "created.txt").read_bytes() == b"new"
        changed = session.command("e files/")
        assert b"non-regular" in changed and b"file" in changed
        changed = session.command("e files/invalid.txt")
        assert b"UTF-8" in changed
        session.send(b"\x13")
        assert (folder / "created.txt").read_bytes() == b"new"
        session.command("e alias.txt")  # inode reuse must retain first.txt's unsaved work
        session.send(b"\x13")
        assert first.read_bytes() == b"dirtyfirst"
        assert (folder / "alias.txt").is_symlink()
        session.quit()


def home_paths(binary, folder):
    work = folder / "working directory"
    work.mkdir()
    home = work / "home"
    home.mkdir()
    config = home / ".wezterm.lua"
    config.write_bytes(b"config")
    (work / "first.txt").write_bytes(b"first")
    literal = work / "~"
    literal.mkdir()
    (literal / "literal.txt").write_bytes(b"literal")
    (work / "~someone").write_bytes(b"named")
    nested = home / "config dir"
    nested.mkdir()
    (nested / "deep.txt").write_bytes(b"deep")
    real = folder / "real"
    real.mkdir()
    (real / "sub").mkdir()
    (real / "dot.txt").write_bytes(b"right")
    (home / "jump").symlink_to(real / "sub")
    (home / "dot.txt").write_bytes(b"wrong")
    with Session(binary, work, "-r", "first.txt") as session:
        session.normal()
        session.command("e ~/.wezterm.lua")
        session.send("iD")
        session.send(b"\x13")
        assert config.read_bytes() == b"Dconfig"
        session.normal()
        session.send(":e ~/.we\t\r")
        session.send(b"\x1a")  # same expanded document: opening again retains history
        session.send(b"\x13")
        assert config.read_bytes() == b"config"

        (home / ".well.txt").write_bytes(b"well")
        session.normal()
        session.send(":e ~/.w\t")
        session.send("z")  # common .we prefix -> .wez, with live-filtered list retained
        session.send("\r\r")
        session.send("iF")
        session.send(b"\x13")
        assert config.read_bytes() == b"Fconfig"

        session.normal()
        session.send(":e ~/conf\t")
        session.send("dee\t\r")
        session.send("iN")
        session.send(b"\x13")
        assert (nested / "deep.txt").read_bytes() == b"Ndeep"
        session.normal()
        session.command("w ~/saved name.txt")
        assert (home / "saved name.txt").read_bytes() == b"Ndeep"
        (home / "existing.txt").write_bytes(b"old")
        session.command("w! ~/existing.txt")
        assert (home / "existing.txt").read_bytes() == b"Ndeep"
        session.command("ww ~/ '$HOME' ")
        assert (home / " '$HOME' ").read_bytes() == b"Ndeep"
        session.send("iT")
        session.send(b"\x13")
        session.send(":w! ~/saved n\t\r")
        assert (home / "saved name.txt").read_bytes() == b"NTdeep"

        session.send(":e ~\t")  # bare ~ completes to ~/ before listing children
        session.send("conf\tdee\t\r")
        session.send("iB")
        session.send(b"\x13")
        assert (nested / "deep.txt").read_bytes() == b"BNdeep"
        session.normal()
        session.send(":e ./~/lit\t\r")
        session.send("iL")
        session.send(b"\x13")
        assert (literal / "literal.txt").read_bytes() == b"Lliteral"
        session.normal()
        session.command("e ~someone")
        session.send("iU")
        session.send(b"\x13")
        assert (work / "~someone").read_bytes() == b"Unamed"
        session.normal()
        session.command("e ~/jump/../dot.txt")
        session.send("iR")
        session.send(b"\x13")
        assert (real / "dot.txt").read_bytes() == b"Rright"
        assert (home / "dot.txt").read_bytes() == b"wrong"
        assert not (literal / ".wezterm.lua").exists()
        session.quit()


def completion_byte_paths(binary, folder):
    odd = folder / "odd"
    odd.mkdir()
    raw = os.fsencode(odd) + b"/ \xff\t\n\x1b[2J "
    with open(raw, "wb") as stream:
        stream.write(b"odd")
    (folder / "base.txt").write_bytes(b"base")
    (folder / "output").mkdir()
    real = folder / "real"
    (real / "inner").mkdir(parents=True)
    (real / "target.txt").write_bytes(b"right")
    (folder / "target.txt").write_bytes(b"wrong")
    (folder / "jump").symlink_to("real/inner")
    with Session(binary, folder, "-r", "base.txt") as session:
        session.send(":e odd/\t")
        assert b"\xff" not in session.output, "raw invalid filename byte leaked to the terminal"
        fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 2, 8, 0, 0))
        session.drain(0.15)
        fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        session.drain(0.15)
        session.send("\r")
        session.send("iB")
        session.send(b"\x13")
        with open(raw, "rb") as stream:
            assert stream.read() == b"Bodd"
        session.normal()
        session.send(":w out\t")
        session.send("copy new \r")
        assert (folder / "output/copy new ").read_bytes() == b"Bodd"
        session.normal()
        session.send(":e jump/../tar\t\r")
        session.send("iR")
        session.send(b"\x13")
        assert (real / "target.txt").read_bytes() == b"Rright"
        assert (folder / "target.txt").read_bytes() == b"wrong"
        bytes(session.output).decode("utf-8")
        session.quit()


def mode_presentation(binary, folder):
    path = folder / "readable.txt"
    emoji = "👩‍💻".encode()
    original = b"a" + emoji + b"b"
    path.write_bytes(original)
    green = b"48;2;123;216;143m"
    red = b"48;2;240;113;120m"
    with Session(binary, folder, "-r", "readable.txt") as session:
        assert green in session.output
        assert b"48;2;33;76;56m" in session.output
        assert "◆".encode() in session.output and "│".encode() in session.output
        assert b"NORMAL" in session.output
        changed = session.send(b"\x1b[C")
        assert b"\x1b[" + green + emoji in changed, "composite cursor did not use the Normal palette"
        changed = session.send("i")
        assert b"\x1b[" + red + emoji in changed, "composite cursor did not use the Insert palette"
        assert red in changed and b"48;2;96;45;53m" in changed
        assert "✎".encode() in changed and b"INSERT" in changed
        changed = session.send("x")
        assert "●".encode() in changed, "UTF-8 modified marker did not appear"
        fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 2, 8, 0, 0))
        session.drain(0.2)
        session.normal()
        fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        changed = session.drain(0.25)
        assert green in changed and b"NORMAL" in changed, "mode colours did not survive resize"
        session.quit("q!")
    assert path.read_bytes() == original


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



def pane_controls(binary, folder):
    path = folder / "shared.txt"
    path.write_bytes(b"alpha\nbeta\ngamma\n")
    with Session(binary, folder, "-r", path.name) as session:
        session.send("l wh")
        shown = screen(session)
        assert shown.splitlines()[0].count(b"alpha") == 2, shown
        session.send("liX")
        session.normal()
        session.send(" h")
        # The left caret adjusts with shared edits but keeps its own position.
        session.send("iL")
        session.normal()
        session.send(b"\x13")
        assert path.read_bytes() == b"aLlXpha\nbeta\ngamma\n", path.read_bytes()
        session.send(" l")
        session.send(b"\x1a")  # shared undo history: undo the left pane's edit
        session.send(b"\x13")
        assert path.read_bytes() == b"alXpha\nbeta\ngamma\n"
        session.normal()
        session.send(" wv")
        session.send(" k")
        session.send("iU")
        session.normal()
        session.send(b"\x13")
        assert b"U" in path.read_bytes()
        session.send(" ")
        session.send(b"\x1b[B")  # root leader arrow focuses the lower pane
        session.send("iD")
        session.normal()
        session.send(b"\x13")
        assert b"D" in path.read_bytes()
        session.quit()
    snapshot = next((folder / "home/.config/me").glob("*/snapshot"))
    assert snapshot.read_bytes()[8:16] == b"ME/MS1/4"
    with Session(binary, folder) as session:
        shown = screen(session)
        assert shown.count(path.read_bytes().splitlines()[0]) >= 3, shown
        fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 4, 12, 0, 0))
        session.drain(0.15)
        assert session.process.poll() is None
        fcntl.ioctl(session.master, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        session.drain(0.15)
        assert screen(session).count(path.read_bytes().splitlines()[0]) >= 3
        for _ in range(4):
            session.send(" wc")
        assert session.process.poll() is None
        assert screen(session).count(path.read_bytes().splitlines()[0]) == 1
        session.send("iUNSAVED")
        session.normal()
        session.send(" wh wc")
        session.send(",")
        assert b"1/1" in screen(session), "closing a pane killed its buffer"
        session.send(b"\x1b", 0.15)
        session.quit()


def pane_ctrl_w(binary, folder):
    for name, text in (("alpha.txt", b"ALPHA"), ("beta.txt", b"BETA"),
                       ("gamma.txt", b"GAMMA")):
        (folder / name).write_bytes(text)
    with Session(binary, folder, "-r", "alpha.txt") as session:
        session.send(" wh")
        session.command("e beta.txt")
        session.send(" wv")
        session.command("e gamma.txt")
        shown = screen(session)
        assert all(text in shown for text in (b"ALPHA", b"BETA", b"GAMMA")), shown
        session.send(b"\x17")
        shown = screen(session)
        assert shown.count(b"ALPHA") == 1 and shown.count(b"BETA") == 1, shown
        assert b"GAMMA" not in shown, "Ctrl W left the current pane open"
        # Closing the lower pane restores the full-height right-hand pane.
        assert shown.splitlines()[0].count(b"BETA") == 1, shown
        session.send(b"\x1b[119;5;23u\x1b[119;5:3u")
        shown = screen(session)
        assert shown.count(b"ALPHA") == 1 and b"BETA" not in shown, shown
        session.send("iUNSAVED")
        session.normal()
        session.send(" wh")
        session.send(b"\x17")
        shown = screen(session)
        assert shown.count(b"UNSAVEDALPHA") == 1, shown
        session.send(b"\x17")  # keep the final pane and unsaved work
        assert screen(session).count(b"UNSAVEDALPHA") == 1
        session.send(",gamma.txt")
        session.send("\r")
        assert b"GAMMA" in screen(session), "closed pane's buffer was removed"
        session.quit()


def repeat_recording(binary, folder):
    path = folder / "original.txt"
    path.write_bytes(b"BASE\n")
    with Session(binary, folder, "-r", path.name) as session:
        session.send("1[")
        assert b"does not accept a count" in screen(session) and b" REC" not in screen(session)
        session.normal()
        session.send("[")
        assert b" REC" in screen(session), screen(session)
        session.send("iAB")
        session.send(b"\x1b[122;5;26u\x1b[122;5:3u")  # undo B once
        session.send("iC")
        session.normal()
        session.send("1]")
        assert b"does not accept a count" in screen(session) and b" REC" in screen(session)
        session.normal()
        session.send("]")
        assert b" REC" not in screen(session), screen(session)
        session.send("1.")
        assert b"does not accept a count" in screen(session)
        session.normal()
        session.send(" wh")
        session.send(b"\x0e")
        session.normal()
        session.send(".")
        session.send(b"\x13")
        session.send("replayed.txt\r")
        replayed = folder / "replayed.txt"
        assert replayed.read_bytes() == b"AC", replayed.read_bytes()
        session.send(b"\x1a")
        session.send(b"\x13")
        assert replayed.read_bytes() == b"", "replay was not one undo unit"
        session.send(b"\x12\x13")
        assert replayed.read_bytes() == b"AC", "redo lost replay grouping"
        session.send(".")
        session.send(b"\x13")
        assert replayed.read_bytes() == b"ACAC"
        session.send(b"\x1a\x13")
        assert replayed.read_bytes() == b"AC"
        assert b"ACBASE" in screen(session), "replay changed another pane's buffer"
        assert path.read_bytes() == b"BASE\n"
        session.quit()
    with Session(binary, folder) as session:
        session.send(".")
        assert b"No recorded sequence" in screen(session), "recording escaped session scope"
        session.send(b"\x1a\x13")
        assert replayed.read_bytes() == b"", "recovered history lost grouping"
        session.send(b"\x12\x13")
        assert replayed.read_bytes() == b"AC"
        session.quit()


def repeat_failure(binary, folder):
    (folder / "source.txt").write_bytes(b"abc")
    with Session(binary, folder, "-r", "source.txt") as session:
        session.send("[iX")
        session.normal()
        session.send("wy]")  # selection/copy succeeds in this buffer
        session.send(b"\x0e")
        session.normal()
        session.send(".")  # after inserting X, w at EOF leaves no selection for y
        shown = screen(session)
        assert b"Replay stopped at step" in shown and b"No selection" in shown, shown
        session.send(b"\x13")
        session.send("partial.txt\r")
        partial = folder / "partial.txt"
        assert partial.read_bytes() == b"X", "failed replay rolled back completed work"
        session.send(b"\x1a\x13")
        assert partial.read_bytes() == b"", "partial result did not undo as one unit"
        session.send(b"\x12\x13")
        assert partial.read_bytes() == b"X"
        session.quit()


def new_buffer(binary, folder):
    path = folder / "original.txt"
    path.write_bytes(b"ORIGINAL")
    with Session(binary, folder, "-r", path.name) as session:
        session.send("iUNSAVED")
        session.normal()
        session.send(" wh")
        session.send(b"\x0e")
        shown = screen(session)
        assert shown.count(b"UNSAVEDORIGINAL") == 1, shown
        assert b"[unnamed]" in shown and b"INSERT" in shown, shown
        session.send("FIRST")
        # Enhanced key + associated text + release must create exactly one buffer.
        session.send(b"\x1b[110;5;14u\x1b[110;5:3u")
        session.send("SECOND")
        session.normal()
        session.send(",")
        assert b"3/3" in screen(session), screen(session)
        session.send(b"\x1b", 0.15)
        session.send(b"\x13")
        session.send("second.txt\r")
        assert (folder / "second.txt").read_bytes() == b"SECOND"
        assert path.read_bytes() == b"ORIGINAL", "Ctrl N wrote or discarded previous work"
        session.quit()
    with Session(binary, folder) as session:
        assert b"SECOND" in screen(session) and b"UNSAVEDORIGINAL" in screen(session)
        session.send(",")
        session.send("\r")  # previous unnamed buffer is selected initially
        assert b"FIRST" in screen(session), screen(session)
        session.quit()


def pane_file_picker(binary, folder):
    (folder / "first.txt").write_bytes(b"FIRST")
    (folder / "second.txt").write_bytes(b"SECOND")
    with Session(binary, folder, "-r", "first.txt") as session:
        before = screen(session)
        session.send(" ww")
        await_file_picker(session)
        session.send(b"\x1b", 0.15)
        assert screen(session) == before, "cancelled split picker changed the layout"
        session.send(" ww")
        await_file_picker(session)
        session.send("second.txt")
        session.drain(0.2)
        (folder / "second.txt").unlink()
        session.send("\r")
        assert b"Selected file no longer exists" in screen(session)
        session.send(b"\x1b", 0.15)
        session.normal()
        assert screen(session).count(b"FIRST") == 1
        (folder / "second.txt").write_bytes(b"SECOND")
        session.send(" ww")
        await_file_picker(session)
        session.send("second.txt")
        session.drain(0.2)
        session.send("\r")
        shown = screen(session)
        assert b"FIRST" in shown and b"SECOND" in shown, shown
        session.send("iX")
        session.send(b"\x13")
        assert (folder / "second.txt").read_bytes() == b"XSECOND"
        assert (folder / "first.txt").read_bytes() == b"FIRST"
        session.normal()
        session.send(" wc,")
        assert b"2/2" in screen(session), "pane close removed the picked buffer"
        session.send(b"\x1b", 0.15)
        session.quit()


def exit_input_cleanup(binary, folder):
    reports = b"\x1b[13;1:3u\x1b[<0;10;5m\x1b[?31u\x1b[?1;2c"
    home = folder / "home"
    home.mkdir(exist_ok=True)
    for kind in ("q", "q!", "signal"):
        master, slave = pty.openpty()
        original = termios.tcgetattr(slave)
        process = None
        output = bytearray()
        sent = False
        late = kind != "signal"
        try:
            fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
            process = subprocess.Popen([str(binary), "-r"], cwd=folder,
                                       stdin=slave, stdout=slave, stderr=slave,
                                       start_new_session=True,
                                       env={**os.environ, "HOME": str(home), "TERM": "xterm-256color"})
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                if select.select([master], [], [], 0.01)[0]:
                    output.extend(os.read(master, 65536))
                if not sent and b"\x1b[?1006h" in output:
                    if kind == "signal":
                        os.killpg(process.pid, signal.SIGTERM)
                    else:
                        os.write(master, b"\x1b")
                        time.sleep(0.15)
                        os.write(master, (":" + kind + "\r").encode() + reports * 8)
                    sent = True
                if not late and b"\x1b[<u" in output:
                    time.sleep(0.01)
                    os.write(master, reports)
                    late = True
                if process.poll() is not None:
                    break
            assert sent and late and process.wait(timeout=1) == 0, bytes(output[-2000:])
            assert termios.tcgetattr(slave) == original, "exit leaked terminal attributes"
            assert b"\x1b[?1049l" in output and b"\x1b[<u" in output
            os.write(master, b"shell-input\n")
            assert select.select([slave], [], [], 1)[0]
            leftover = os.read(slave, 4096)
            assert leftover == b"shell-input\n", (kind, "reports leaked into shell", leftover)
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait()
            os.close(master)
            os.close(slave)

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
    checks = [repeat_recording, repeat_failure, new_buffer, exit_input_cleanup, pane_controls, pane_ctrl_w, pane_file_picker, file_picker, file_picker_stale_and_cancel, cli_files, startup_modes, recovery, unnamed_discard, buffer_kill, fidelity, external_files, symlinks_and_save_as,
              search_replace_and_buffers, search_origins, slash_replacement, confirmation_recovery, byte_paths_and_checkpoint_failures,
              second_instance, crash_and_signals, undo_caret, word_delete, buffer_picker, buffer_picker_close_selected, buffer_picker_preview, buffer_picker_recovery, buffer_picker_unicode_bytes, enhanced_key_actions, keyboard_diagnostics, hjkl_and_line_selection, leader_overlay, control_hjkl, duplicate_selection, command_completion, live_completion_filter, file_completion, home_paths, completion_byte_paths, mode_presentation, gutter_highlight, graphemes_and_resize]
    selected = [check for check in checks if args.filter in check.__name__]
    if not selected:
        parser.error(f"No PTY checks match {args.filter!r}")
    for check in selected:
        with tempfile.TemporaryDirectory(prefix=f"me-{check.__name__}-") as directory:
            check(binary, Path(directory))
        print(f"PASS {check.__name__}", flush=True)
    print("PTY integration checks passed", flush=True)


if __name__ == "__main__":
    main()
