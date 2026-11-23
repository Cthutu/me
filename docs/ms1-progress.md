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
  Undo/redo restores optional before/after caret hints without undoing navigation
  or restoring selections. Snapshot v2 preserves hints and imports v1 history;
  codec checks reject out-of-bounds or split-UTF-8 history carets.
- `:keys` keyboard diagnostics show actual Kitty flags/query completion, reliable
  capabilities and a bounded six-event decoded trace. Keys do not edit/save;
  Escape closes and Alt+Page Up/Down scroll. Private CSI replies are consumed by
  Nerd; partial flags do not overclaim held keys. Legacy 0x08 ambiguity is explicit.
- Normal HJKL movement aliases the arrows, including counts, graphemes, preferred
  columns and selection clearing. `q` selects lines, with counts/repeated extension;
  arrows remain available and these letters stay literal in Insert/prompts.
- Search preview, forward/backward origin prefixes, cancellation/arrow restoration, wrap,
  remembered terms, next/previous match selections and passive highlighting.
  `/old/new` replaces all by default; `/old/new/c` confirms using Y/N/A/Escape.
  Completed or stopped approved edits form one undo unit, already valid in
  partial checkpoints. `:replace` and `g` are removed; `//` and `??` origins
  remain, parsed before replacement fields. Escaped slashes remain searchable.
  A batches the remaining original matches.
- Green Normal/red Insert caret and status presentation with contrasting UTF-8
  mode badges, separators and modified marker. Narrow mode badges preserve room
  for warnings. Composite overlays now use the same RGB ordering as native cells.
- Single-pane `std.term` surface with absolute/relative gutter, current-line
  horizontal scroll, status, wrapped/growing/scrollable messages and resize.
  Local full-grapheme bridge and retained idle framebuffer output.
- `:e <path>` opening/creation and inode-alias reuse without discarding unsaved
  work; filename Tab completion for `:e` / `:w` / `:w!` / `:ww`, with common-prefix
  expansion, directory slashes and a selectable message-area ambiguity list.
  Raw filename bytes survive completion and safe prompt display.
- Command-name Tab completion, with filename handoff after the separating space.
  The prompt stays on the bottom row, candidate lists above it. Typing/deletion
  filter an open list even with one/zero matches; same-folder filtering uses a
  cached directory snapshot. Acceptance never executes a command.
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
passed. All **33 project-authored named tests are colocated across 15 source
modules**, with many assertions and all 1,093 official Unicode vectors in the
marked test section of `src/characters.n`. All 24 test helper functions and
additional test-only imports live in bare `test { ... }` sections. The 17 former
standalone Nerd test files have been removed.

`just test` uses the single `main.n` root: **144 tests passed**, comprising 33 ME
tests and 111 imported library tests, discovered once rather than repeated per
test program. Inventory comparison verified that all 29 original named tests
remain discoverable exactly once, and all 53 moved test/helper bodies were
preserved before formatting. Unicode regeneration and a second formatting pass
are byte-idempotent. The release executable is byte-identical to the pre-migration
build, confirming no production-code or test-only-code leakage.

### Real terminal integration

`python3 tests/terminal.py --binary _bin/me` and the equivalent release command
passed all **25 scenario groups**, including buffer lifecycle, gutter styling,
selected-line duplication, word deletion, file opening and filename completion,
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
14. Ctrl+Backspace CSI-u (`127;5u`, `8;5u`) and legacy WezTerm `0x08`
    events delete previous words or active selections;
    deletion is one undo operation, including when invoked from Insert.
15. Backspace Undo and insertion Redo restore the initiating caret, including
    after restart; legacy v1 snapshots retain history and upgrade to v2.
16. Green Normal/red Insert cursors and status, UTF-8 mode/modified markers,
    correct composite-grapheme RGB, contrast, narrow layouts and resize.
17. Real Tab completion, common-prefix and selectable ambiguity, directory suffixes,
    list-only cancellation, create/open/reuse without discarding unsaved buffers,
    and non-regular/invalid-content refusal.
18. Completion and saving of control/non-UTF-8/whitespace filenames, safe prompt
    presentation across resize, literal trailing spaces, and symlink/`..` resolution.
19. Command-name completion, empty-prefix discovery, safe acceptance, filtering,
    cancellation and handoff to filename completion.
20. Persistent live filtering, zero-match navigation/acceptance, Backspace
    widening, bottom-anchored input across resize, and directory transitions.
21. Second-slash replacement, Y/N/A/Escape confirmation, blocked unrelated input,
    single undo/redo for partial edits, literal slash searches, obsolete-flag
    refusal, Unicode, protected BOM and CRLF fidelity.
22. SIGTERM during confirmation preserves partial unsaved edits and a valid single
    undo/redo unit on continuation recovery, without writing the backing file.
23. Forward search from caret versus `//` document-start origin, prefixed
    replacement/confirmation, undo and escaped literal-slash searches.
24. Real-key counted HJKL movement across graphemes/short lines, `q` line
    selection with counts/repetition, linewise cutting and undo, and literal
    HJKL/q input in Insert and search prompts.
25. Actual keyboard status/DA replies, pending/negative/zero/partial/full states,
    distinct enhanced Ctrl+H and Ctrl+Backspace, release events, legacy ambiguity,
    diagnostic input capture without edits/saves, scrolling/resize, clean Escape
    exit and keyboard-mode restoration.

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

## Nerd fixes — ten completed

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
| `98883071` | Reacquire local bindings after generic inference grows semantic tables |

Fixes are committed, pushed on their own `agent` branches, and integrated into
**local Nerd `main` at `7cd7e0ec`**, not pushed directly to remote `main`. Their
merged worktrees and local temporary branches have been removed. Other agents'
worktrees/checkouts are untouched. `_tools/` contains the isolated compiler and
modules. The validated `93c8a38a` compiler passed isolated and user-installed
regression checks. The user subsequently clarified that normal installation must
run directly in `~/nerd`, not an installation-only worktree. That recipe has now
installed its current `remove-linux-libc` checkout at `174a4576`, including matching
modules and editor support. This is distinct from local `main`/ME's private
`7cd7e0ec` toolchain/modules; no branch switch or merge was performed. Integration
of the latest local-binding/protocol changes into that other agent's branch
awaits coordination. Installation from
`~/nerd` is required after each fully validated compiler fix.

### Keyboard protocol library completion

Nerd `7cd7e0ec` adds public `kitty_flags: ?u32` and `query_complete` capability
fields, queries primary DA after Kitty status, consumes private CSI through its
final byte, and requires appropriate all-key flags before claiming reliable
physical-key/release/associated-text reporting. Native console input is complete
immediately. Zero replies, pending/negative probes, malformed/overflow status and
partial/full flags have native regression coverage; ME PTYs exercise real bytes.
Updated CLI/LSP location fixtures retain exact definition/diagnostic coverage.

The initial full gate exposed stale location expectations after adding public
fields; those were corrected, then the complete gate passed: **72 passed, 0
failed, 2 platform skips**. Formatting and the required direct `~/nerd just
install` passed; that installation remains the unchanged libc-removal checkout
`174a4576`, not this library revision. The feature commit is pushed on its agent
branch and retained on local `main`; its clean completed worktree was removed.
ME's private validated compiler/modules include it. The existing Escape-timeout
and bracketed-paste gaps are not claimed fixed by this scoped protocol audit.

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
