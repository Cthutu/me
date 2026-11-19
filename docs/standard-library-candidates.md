# Standard-library candidates

These facilities were investigated and implemented **locally first** in ME.
They are candidates for later evaluation, not approval to modify the standard
library. Runtime code uses Nerd/Linux syscalls, without added external libraries.

| Facility | Investigated gap | Local implementation and verification |
| --- | --- | --- |
| Extended grapheme segmentation | `std.text` exposes UTF-8/scalar operations, not UAX #29 cluster traversal | `src/characters.n`, generated Unicode 16 tables; all 1,093 official vectors, reverse traversal tests |
| Unicode display-cell measurement | `Rune.display_width()` has a small wide-range table and no complete combining/emoji treatment | Unicode 16 East Asian width, zero-width and emoji properties; cluster width, tab/flag/keycap/VS16 tests in `tests/characters.n` |
| Unicode word/whitespace classification | No general letter/digit/whitespace predicates found in `std.text` | Generated category/White_Space tables; local word runs and paragraph/indentation boundaries |
| Full-grapheme framebuffer cells | `std.term` cells hold one scalar, and private scalar-width accounting is incomplete | `src/terminal.n` bridges only complex/mismatched-width glyphs after retained-cell presentation; PTY tests cover combining/ZWJ rendering, resize and idle output. Prefer a native glyph-cell contract upstream rather than retaining this bridge indefinitely |
| Byte-safe display strings | Linux paths can be non-UTF-8 and contain terminal controls; document text has a different validation contract | `native.display_text`, live invalid-byte filename save/recovery test |
| Durable atomic replacement | `std.files` lacks a complete same-directory exclusive temporary/flush/rename contract | `src/native.n`; follows live symlink targets, preserves owner/mode/ACLs/xattrs, rechecks identity/content, flushes file and directory; native and PTY fidelity/permission/long-name tests |
| File identity/change snapshots | `std.files` metadata does not expose the whole identity/timestamp comparison needed here | `native.metadata`/`same_file_state`, `Workspace.poll_files`; Linux stat plus two-sample polling; live reload/conflict/deletion/reappearance tests |
| Process environment and startup folder | No suitable high-level environment/CWD helpers found in the inspected API | `/proc/self/environ` and `getcwd` wrappers in `src/native.n`; exercised through actual startup/continuation |
| Per-folder process ownership | No high-level non-blocking advisory lock facility found | Local `flock` use in `src/workspace.n`; second-instance PTY tests prove snapshot isolation and unsafe-quit refusal |
| Safe process termination events | Terminal loop cleanup does not itself cover process termination signals | Linux `signalfd`/signal-mask integration in `src/terminal.n`; SIGTERM checkpoint and raw/alternate-screen restoration tested. No libc signal handlers or unsafe restorer stubs |
| Validating persistent history codec | No editor-specific history format is expected in the library; generic bounded codec helpers may be reusable | `src/codec.n`, workspace envelope/checksum, native malformed/replay tests and PTY corrupted-snapshot retention |

## Further investigated gaps, not locally solved

- **Escape timeout resolution:** Linux `std.term` requests 25 ms but rounds it to
  a 100 ms `termios` tick. Tests must wait for this legacy ambiguity window;
  rapid Escape+letter can otherwise be an Alt sequence. A poll-based byte wait
  would be a general backend improvement. ME does not silently fork or patch the
  standard library to change it.
- **Bracketed paste boundaries:** ordered key/character events do not expose a
  paste event/boundary. ME's internal clipboard is implemented, but terminal
  paste should be performed in Insert. A library event contract is preferable
  to interpreting clipboard text as Normal commands.

## Evaluation notes

- Generated inputs are SHA-256-pinned in `build/unicode-sources.json`; fetching
  and generation are build-time Python tooling, not runtime dependencies.
- Terminal width conventions remain terminal/font dependent. Ambiguous-width
  characters are narrow; the Unicode version is explicit.
- Atomic rename cannot eliminate every race with an uncooperative external
  writer. ME verifies bytes and metadata near commit but does not claim a
  filesystem transaction. Metadata preservation errors leave the target intact
  before rename; a post-rename directory-flush failure is reported explicitly.
- Polling and persistence policy are editor/workspace concerns; only lower-level
  metadata, locks, codecs and durable-replacement primitives are likely library
  candidates. Cross-platform contracts would need separate design.

Compiler bugs are **not** library candidates. Eight fixes were made in dedicated
Nerd worktrees, fully gated and merged into local `main`; see
[MS1 progress](ms1-progress.md).
