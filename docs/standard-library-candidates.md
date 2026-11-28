# Standard-library candidates

These facilities were investigated and implemented **locally first** in ME.
They are candidates for later evaluation, not approval to modify the standard
library. Runtime code uses Nerd/Linux syscalls, without added external libraries.

| Facility | Investigated gap | Local implementation and verification |
| --- | --- | --- |
| Extended grapheme segmentation | `std.text` exposes UTF-8/scalar operations, not UAX #29 cluster traversal | `src/characters.n`, generated Unicode 16 tables; all 1,093 official vectors, reverse traversal tests |
| Unicode display-cell measurement | `Rune.display_width()` has a small wide-range table and no complete combining/emoji treatment | Unicode 16 East Asian width, zero-width and emoji properties; cluster width, tab/flag/keycap/VS16 tests colocated in `src/characters.n` and `src/view.n` |
| Unicode word/whitespace classification | No general letter/digit/whitespace predicates found in `std.text` | Generated category/White_Space tables; local word runs and paragraph/indentation boundaries |
| Full-grapheme framebuffer cells | `std.term` cells hold one scalar, and private scalar-width accounting is incomplete | `src/terminal.n` bridges only complex/mismatched-width glyphs after retained-cell presentation; PTY tests cover combining/ZWJ rendering, resize and idle output. Prefer a native glyph-cell contract upstream rather than retaining this bridge indefinitely |
| Byte-safe display strings | Linux paths can be non-UTF-8 and contain terminal controls; document text has a different validation contract | `native.display_text`, live invalid-byte filename save/recovery test |
| Byte-safe directory enumeration | `std.files` exposes path metadata but no directory-entry iterator in the inspected API | `src/completion.n` uses Linux `getdents64`, validates record boundaries, closes descriptors on all exits, handles EINTR, bounds discovery, caches a byte-safe directory snapshot for pure query filtering, and preserves filename bytes; native/PTY tests cover dotfiles, symlink directories, whitespace/control/invalid-byte names and symlink-plus-`..` resolution. T4 adds cancellable recursive discovery in `src/file_picker.n`, using a child process/non-blocking byte pipe and bounded UI publication/filtering; stopped-worker PTYs verify responsive cancellation and reaping. This is local-first application machinery pending evaluation for a generic enumeration service |
| Durable atomic replacement | `std.files` lacks a complete same-directory exclusive temporary/flush/rename contract | `src/native.n`; follows live symlink targets, preserves owner/mode/ACLs/xattrs, rechecks identity/content, flushes file and directory; native and PTY fidelity/permission/long-name tests |
| File identity/change snapshots | `std.files` metadata does not expose the whole identity/timestamp comparison needed here | `native.metadata`/`same_file_state`, `Workspace.poll_files`; Linux stat plus two-sample polling; live reload/conflict/deletion/reappearance tests |
| Process environment and startup folder | No suitable high-level environment/CWD helpers found in the inspected API | `/proc/self/environ` and `getcwd` wrappers in `src/native.n`; exercised through actual startup/continuation |
| Per-folder process ownership | No high-level non-blocking advisory lock facility found | Local `flock` use in `src/workspace.n`; second-instance PTY tests prove snapshot isolation and unsafe-quit refusal |
| Safe process termination events | Terminal loop cleanup does not itself cover process termination signals | Linux `signalfd`/signal-mask integration in `src/terminal.n`; SIGTERM checkpoint and raw/alternate-screen restoration tested. No libc signal handlers or unsafe restorer stubs |
| Validating persistent history codec | No editor-specific history format is expected in the library; generic bounded codec helpers may be reusable | `src/codec.n`, workspace envelope/checksum, native malformed/replay tests and PTY corrupted-snapshot retention |

## Unicode case folding and generic fuzzy list — local candidates

`src/picker.n` owns a reusable fuzzy-list model with query/caret, stable consumer
IDs, source-order matches and selection/scroll state. It uses Unicode 16 default
full case folding (including multi-codepoint mappings) before codepoint-ordered
subsequence matching. `build/generate_unicode.py` generates the pinned C/F mappings
from `CaseFolding.txt` into `src/unicode_data.n`; locale-specific Turkic mappings
and canonical/accent normalisation are deliberately separate, unimplemented policies.
Labels are display-sanitised while consumer IDs retain exact filename identity.
The bounded popup layout/generic renderer is independent of workspace ownership.
This remains local-first functionality, not a dependency or automatic stdlib API.

## CSI cursor-key actions — fixed in Nerd

Traditional CSI cursor/Home/End/tilde reports accepted modifier subparameters but
discarded event types, so enhanced key release reports became fresh presses.
Nerd now shares action decoding with CSI-u and preserves press/repeat/release in
its key events. ME ignores decoded releases in ordinary UI handlers but retains
all actions in diagnostics. This is a library bug fix, not local escape parsing;
see the revision and full-gate evidence in [MS1 progress](ms1-progress.md).

## Home-relative path expansion — local candidate

`src/native.n` provides `expand_home_path` over the existing environment reader:
only a complete leading `~`/`~/` uses HOME, with an explicit error for unset or
non-absolute HOME. Workspace opening/saving and completion discovery share it;
non-home bytes, whitespace and OS symlink/`..` resolution are preserved. There is
no shell parser, variable expansion or passwd/user lookup. This small, tested
path-policy helper may suit a future standard path module; it remains local
first rather than extending Nerd as part of this editor fix.

## Keyboard protocol audit — implemented in Nerd

The user explicitly requested completing relevant `std.term` facilities rather
than maintaining an ME workaround. Nerd now exposes actual Kitty reply flags
and probe completion, handles the following DA response without leaking its
parameters as text, and avoids overclaiming capabilities from partial flags.
ME consumes those public fields in `:keys`; it neither negotiates the protocol
nor decodes escape sequences itself. Missing responses remain pending, and raw
byte access/other terminal-specific protocols are not implied. See the toolchain
revision and verification in [MS1 progress](ms1-progress.md).

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

Compiler bugs are **not** library candidates. Completed compiler fixes used
dedicated Nerd worktrees and full gates before integration into local `main`; see
[MS1 progress](ms1-progress.md).


## Cancellable discovery — local candidate

`src/file_picker.n` separates blocking filesystem traversal from the terminal
loop with a syscall-only child, per-scan pipe, explicit cancellation/reaping,
parent-death handling and bounded transport. `src/picker.n` adds incremental
query filtering while preserving the synchronous buffer consumer. Tests cover
partial frames/EOF, new query invalidation, stopped-worker cancellation,
descriptor ownership, directory-link cycles and exact invalid/control-byte filenames.

## Bounded JSON protocol reader — local candidate

`src/json.n` provides a strict bounded UTF-8 JSON reader with arena-owned decoded
strings, checked escapes/surrogate pairs, duplicate-key rejection and indexed
subtrees. `json_quote` escapes outgoing protocol strings. The current standard
library inventory has no JSON module; this implementation serves LSP transport
without selecting JSON for ME configuration. Native protocol and round-trip
checks evaluate it locally before any standard-library proposal.

## Non-blocking provider transport — local candidate

`src/nerd_lsp.n` uses Nerd Linux syscalls for a bidirectional child socket, bounded
Content-Length framing, non-blocking reads/writes, process-group cancellation,
parent-death handling and reaping. The existing synchronous process runner cannot
serve the terminal loop. This remains a local evaluation, alongside cancellable
file discovery; general child-process/framing facilities could later avoid their
duplicated lifecycle primitives. LSP synchronisation and Nerd's diagnostics barrier
are editor/provider policies, not proposed standard-library APIs.


## Isolated bounded formatter execution — local candidate

`src/formatter.n` uses a private directory and syscall-only child to invoke an
installed executable with explicit arguments, isolated standard descriptors,
parent-death termination, a monotonic deadline and timeout kill/reap. It validates
output before saving. Start/poll keep the terminal loop responsive; cancellation
kills/reaps the worker. The current `std.process` runner waits without a deadline
or descriptor policy; this local worker is not a generic provider API. Shared PATH discovery lives in `native.installed_nerd`
and is also used by the LSP transport. Native/PTY checks exercise real formatting,
failure isolation, overwrite timing, target races, missing executables and reaping.
These are candidates for evaluation, not automatic standard-library changes.
