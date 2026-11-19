# MS1 progress

**MS1 complete: implemented, runnable, and debug/release regression-tested.**
This tracker and PanelCraft are manually maintained, not automatic local-file
refreshes. See the [README](../README.md) for usage and explicit limitations.

## Delivered slices

- Trait-backed UTF-8 gap buffer with position-explicit replacement, chunk reads,
  revisions, validated byte boundaries and stabilised borrowed input.
- Unicode 16 extended grapheme traversal: **1,093 official conformance vectors**,
  reverse traversal, display widths, tabs, emoji/flags/keycaps, word/whitespace
  classification. Source inputs are SHA-256-pinned; generation is build-time.
- Operation-sized, buffer-owned history, branching undo/redo, cached document
  projection/line index, mixed endings and protected leading BOM.
- Independent view selections, preferred display columns, grapheme/word/line/
  page/paragraph navigation, counts, scroll-away and semantic edit adjustment
  across shared-buffer views. Command-emitting keyboard state machine.
- Normal/Insert editing, selection replacement, indentation heuristic, internal
  characterwise/linewise clipboard, cut/change/paste and one-operation duplicate
  of selected lines or the caret line, clearing character-based selections.
  Ctrl+Backspace deletes selections or the previous Ctrl+Left word range.
- Search preview, origin prefixes, cancellation/arrow restoration, wrap,
  remembered terms, next/previous match selections and passive highlighting.
  Literal one/all replacement; replace-all is one undo operation.
- Single-pane `std.term` surface with absolute/relative gutter, current-line
  horizontal scroll, status, wrapped/growing/scrollable messages and resize.
  Local full-grapheme bridge and retained idle framebuffer output.
- CLI opening/reset, new named/unnamed documents, `:buffers` / `:buffer N`, all
  agreed save/quit commands, save-all filename sequencing and partial success.
- Same-directory exclusive temporary/atomic replacement; symlink preservation,
  owner/mode/ACL/xattr copying, near-commit checks, file/directory durability.
  Unchanged ordinary save does not touch inode/mtime; force/conflict distinction.
- Live two-sample external polling: undoable unedited reload, edited conflict,
  deletion without recreation, and reappearance handling.
- Per-startup-folder continuation with flock ownership, content/history codec,
  checksum/version/path validation, debounced checkpoints and synchronous quit.
  `:q!` removes all unsaved buffers, including recovered work. `:kill[!]` removes
  the active buffer and all its views; disk writes never roll back. Second-instance and persistent-failure safeguards.
- SIGTERM/SIGHUP/SIGINT safe-exit requests through Linux signal descriptors;
  tested raw-terminal/alternate-screen restoration and SIGKILL checkpoint recovery.
- Standard `just` recipes, compiler/module overrides, debug/release executables
  and a reproducible PTY latency probe.

## Verification

### Headless

`just check`, `just format`, Python tooling compilation and `just test` have
passed. There are **20 project-authored named tests across 14 Nerd files**, with
many assertions and the 1,093 official Unicode vectors inside those tests.
Nerd additionally discovers imported standard-library tests; its per-file totals
must **not** be summed or described as the number of distinct ME tests.

### Real terminal integration

`python3 tests/terminal.py --binary _bin/me` and the equivalent release command
passed all **14 scenario groups**, including buffer lifecycle, gutter styling, selected-line duplication and word deletion,
on both debug and release builds:

1. Unsaved named continuation, individual undo, redo across saving/restart.
2. Removal of recovered and newly created unsaved buffers on `:q!`.
3. BOM/tabs/mixed endings/no final newline, unchanged/forced save, invalid input.
4. Live external reload/undo, conflict, missing/reappearing files.
5. Symlink target and symlink/`..` semantics, recovered inode-alias reuse,
   owner/mode/ACL/xattr preservation, save-as and long filenames.
6. Search cancellation, literal replace-all/undo, retained-buffer access,
   save-all unnamed prompting and preservation of partial successes.
7. Non-UTF-8 byte filenames, checkpoint failure/unsafe-quit refusal, recovery,
   and retention of corrupted snapshot evidence.
8. Second-instance isolation, no snapshot writes and safe quit policy.
9. SIGKILL recovery, persisted history, safe signal shutdown and terminal cleanup.
10. Combining/ZWJ presentation, grapheme deletion, resize and retained idle output.
11. Refused/forced kill, all shared views, fallback focus/order, disk preservation,
    no text-undo resurrection and removal from continuation.
12. Current-line gutter emphasis, highlight movement, muted former-line numbers
    and preservation of emphasis in Insert.
13. Repeated selected-line block duplication, one-operation undo, current-line
    fallback with character-selection clearing and mixed-ending fidelity.
14. Distinct Ctrl+Backspace events delete previous words or active selections;
    deletion is one undo operation, including when invoked from Insert.

Normal/signal exits compare the actual PTY attributes against startup and check
alternate-screen restoration. Tests use isolated temporary HOME/folders and do
not touch the user's continuation state.

`ldd` verifies no accidental GL/X11/XCB linkage. The executable retains only
existing Nerd runtime/native toolchain dependencies under the explicit temporary
exception; ME has **no direct libc FFI or added runtime library**.

### Latency measurement

The initial MS1 release PTY probe (seven runs each, 80×24, this machine) measured
median startup-to-first-frame **17.1 ms empty / 22.7 ms with 1 MiB**, and
input-to-present **16.2 ms** for both. Reproduce with:

```sh
python3 build/benchmark.py --binary _bin/me-release
```

This measures bytes delivered to the PTY, not emulator paint completion or a
hard real-time guarantee. Complex-grapheme overlays add one simulation step.
Document projection/index rebuilding remains correctness-first, not a claim
about very large-file scalability.

## Nerd fixes — nine completed

All compiler changes used dedicated worktrees. Each fix passed the unified full
gate (**72 passed, 0 failed, 2 platform skips**), formatting and isolated installed
compiler smoke checks before integration. A combined-main gate also passed;
the latest record-field context/layout gate includes all earlier fixes.

| Commit | Fix |
| --- | --- |
| `5e1396dd` | Do not materialise void success binders in LLVM or C |
| `e98fc396` | Nested value-`on` leaves its enclosing fallback branch intact |
| `0f6748c2` | Resolve loop headers after enclosing pattern bindings exist |
| `b5894f92` | Unwrap optional/result expected context for enum payloads |
| `a0ab3d25` | Normalise implicit dynamic-array pointer receivers in HIR |
| `ae9e8acc` | Preserve extraction binders in formatted return guards |
| `37a024a3` | Omit unused FFI libraries from executable links |
| `2776f687` | Preserve unterminated string bytes and formatter idempotence |
| `93c8a38a` | Wrap optional/result record fields and preserve enum payload storage layout |

Fixes are committed, pushed on their own `agent` branches, and integrated into
**local Nerd `main` at `93c8a38a`**, not pushed directly to remote `main`. Their
merged worktrees and local temporary branches have been removed. Other agents'
worktrees/checkouts are untouched. `_tools/` contains the isolated compiler and
modules. The validated `93c8a38a` compiler passed isolated and user-installed
regression checks. The user subsequently clarified that normal installation must
run directly in `~/nerd`, not an installation-only worktree. That recipe has now
installed its current `remove-linux-libc` checkout at `21681187`, including matching
modules and editor support. This is distinct from local `main`/ME's private
`93c8a38a` toolchain; no branch switch or merge was performed. Installation from
`~/nerd` is required after each fully validated compiler fix.

The investigation initially described as “pointer slice assignment” was the
implicit receiver normalisation bug above. Typed expression-function return
annotations were unsupported syntax, not another compiler bug; no workaround or
spurious compiler patch remains.

## Explicit remaining limits / later milestones

- No mouse, desktop clipboard integration, picker, pane-management UI, repeat
  recording, configuration or Nerd language intelligence.
- Legacy `std.term` Escape ambiguity currently has 100 ms Linux resolution;
  bracketed-paste boundaries are not exposed. Paste from a terminal in Insert.
- Unicode widths vary by terminal/font; the local full-grapheme bridge is a
  candidate for a proper standard-library cell API, not an extra framework.
- Cached full document projection/indexes rebuild on edits. Incremental indexing,
  asynchronous services and wider large-file benchmarks remain future work.
- Ordinary rename-based saving cannot remove the final race with an uncooperative
  external writer; this is documented rather than claimed as transactional.
- Provisional implementation answers are in design §24, not presented as newly
  agreed user requirements. Further UX changes remain open to feedback.
