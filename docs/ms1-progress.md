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
  or restoring selections. Snapshot v3 preserves v2 hints, imports v1/v2 history and persists buffer MRU;
  codec checks reject out-of-bounds or split-UTF-8 history carets.
- Plain CLI filenames start fresh with only those files, first successful path
  displayed. They and `-r` erase the old snapshot before opens, including failures.
  Bare `me` restores; `+filename` opts into restoration before adding files.
  Mixed modes fail without touching recovery; second instances stay isolated.
- The popup's right-hand preview shows highlighted buffers' live unsaved text,
  safely clipped with Unicode/tab widths. It never switches/edits buffers or
  changes caret/history/MRU; narrow/short screens fall back to a full-width list.
- Normal comma opens the first reusable large fuzzy popup: Unicode full-case-folded
  subsequence matching, MRU buffer order, second-row initial selection and immediate
  Enter acceptance. Escape cancels; query/selection remain separate from text views.
  Ctrl+W safely closes the highlighted picker buffer (otherwise the active one),
  preserves focus when closing another buffer, focuses MRU surviving work when needed and
  refuses unsaved work. Input-stream suppression survives switching/closing views.
- Enhanced cursor/Home/End/tilde-key releases no longer execute commands. Nerd
  preserves CSI action subparameters; ME ignores decoded releases in ordinary
  handlers, including message scrolling. Repeats still navigate and diagnostics
  retain releases for inspection.
- Leading `~`/`~/` paths expand HOME consistently for opening, saving and filename
  completion. The prompt retains `~/`; bare `~` Tab adds `/` first. Preserve literal
  bytes, symlink/`..` semantics and explicit `./~` access. Invalid HOME errors safely.
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

## Highlighted-buffer close adjustment (T3d)

Ctrl+W in the buffer picker closes its highlighted saved buffer. Legacy and
enhanced input share the selected-target path; no matches do nothing. A close
attempt keeps the picker open, refuses unsaved work, and preserves active work
when closing another buffer. Query/caret and the selected row are retained,
clamping to remaining matches. Candidate IDs and preview targets are rebuilt
after removal; no-match results stay open. Existing active-close MRU/last-buffer and paired
text/release suppression rules remain in effect.

Verification: formatting/type checking, **156 native tests** (44 ME + 112 imported),
all **34 debug PTY groups**, all five release buffer-picker groups, Python
compilation and diff checks passed. The additional native and PTY regressions
cover target identity, dirty work, filtering/no matches and input suppression.
Changes were pushed and installed at `b5be63e`; installed selected-close PTYs passed.

## File discovery and Space leader (T4)

Normal Space starts a leader sequence. Its known-key menu appears after one
second; Space Space opens the file picker immediately. Escape or an unknown
key cancels the sequence. Spaces remain literal in Insert and prompts; enhanced
key releases/repeats cannot accidentally advance the leader.

The picker scans the startup folder in a cancellable child process and applies
bounded incremental Unicode subsequence filtering. Hidden and ignored files are
included. File and directory symlinks are followed, including outside the startup
folder; opened-directory device/inode ancestry detects cycles. Broken links and
special files are omitted. Existing buffers are reused through normal path/inode
identity. Enter revalidates stale candidates; errors retain the popup. Escape
preserves the originating editing state. The file list has no content preview
and Ctrl+W has no action there.

Native regressions cover incremental filtering, bounded work, partial transport
frames/EOF and leader input precedence. PTY groups cover delayed/immediate leader
invocation, cancellation, enhanced releases, hidden/ignored names, Unicode,
external directory aliases/cycles, inode reuse, stale/special files, byte-safe
names, resize, unreadable directories, stopped-worker input/cancellation, reaping
and descriptor ownership. Exact limits and contracts are in design §26.

Installed Nerd `c80d7775` on `remove-linux-libc` passes `just format`, `just check`,
all **159 native tests** (47 ME across 17 modules + 112 imported), `just build`
and `just release`. Both ME profiles have no ELF `NEEDED` dependencies or
`INTERP` segment. Installed compiler bytes and modules match `~/nerd` exactly.
All **36 debug and 36 release PTY groups** passed on these builds, along with
Python compilation and diff checks. The release is installed with `just install`;
the focused installed picker checks exercise both new PTY groups.

## Ctrl+HJKL navigation (T4a)

Enhanced Ctrl+H/L mirror word movement and Ctrl+J/K mirror scroll-only movement,
including Normal counts, Shift semantics, repeats and Normal/Insert preservation.
A shared scan-code mapping also gives picker popups their existing arrow actions:
J/K select rows and H/L move the query caret. Associated text is suppressed and
release events do not execute. Legacy Backspace/Enter bytes retain their previous
meaning; these aliases require distinguishable enhanced keyboard reports.

Native coverage exercises all four aliases with counts, Shift, associated text,
release and repeat events. The new PTY group checks actual word movement,
Insert preservation, selection replacement, counted scrolling with an unmoved
caret and popup row selection. Installed Nerd remains `c80d7775` from
`remove-linux-libc`; no compiler change is required for this adjustment.

Verification: `just format`, `just check`, all **160 native tests** (48 ME + 112
imported), all **37 debug PTY groups**, `just release`, the focused release
Ctrl+HJKL PTY group, Python compilation and diff checks passed. Installation uses
`just install` after commit/push, followed by the installed Ctrl+HJKL smoke.

## Sliding Space menu (T4b)

The leader's delayed hint now uses a full-width bottom overlay with a border,
coloured key labels, action names and cancellation hint. It slides upwards over
180 ms after the one-second delay. Rendering leaves document view
geometry and the message area intact, masks composite graphemes underneath and
restores the underlying editor on cancellation. Resizes and very small surfaces
remain clipped.

`src/leader_menu.n` supplies one declarative sequence table to both the dispatcher
and renderer. Group prefixes, path headings and parent navigation prepare future
submenus. Space Space was the initial action; T5 adds the agreed Windows
submenu and directional focus. Space b d was explicitly only an example. Modal input consumes Enter and other non-menu keys, ignores releases
and repeats, and supports enhanced labels with or without paired text.

Native regressions cover nested fixture lookup, animation bounds, opacity,
unchanged geometry/messages, tiny sizes and modal Enter/Backspace handling.
The new PTY group checks delayed display, overlay opacity, unchanged upper text,
repeat/release handling, resize, complete restoration and immediate file opening.
A rendered PTY preview was inspected for layout and colours. Nerd remains the
installed `c80d7775` compiler from `remove-linux-libc`; no compiler change is needed.

Verification: formatting/type checking, **162 native tests** (50 ME across 18
modules + 112 imported), all **38 debug and 38 release PTY groups**, Python
compilation and diff checks passed. Release installation uses `just install`
after commit/push, followed by the focused installed overlay smoke.
The follow-up delay adjustment uses one second, with native assertions at
999 ms and 1,000 ms. All 162 native tests and focused debug overlay/file-picker
and release overlay checks validate the adjustment; the 180 ms slide is retained.

## Split panes (T5)

The Windows submenu implements Space w h/v/s/c/w, with root Space hjkl or cursor
keys for directional focus. A bounded binary tree owns rectangles and split axes;
each leaf mounts a distinct text view. Views keep independent caret, selection,
scroll and keyboard state while buffers own shared content and undo history.
Closing a pane preserves its buffer and keeps the final pane open. Buffer
replacement affects the current pane; killing a buffer rebinds affected leaves
without dropping the layout. Hidden view/tree slots are reused.

Space w w captures its originating pane, opens the picker, preflights available
space before opening a selection and creates a pane only on success. Cancellation,
stale candidates and failed opens leave the tree intact. The original file opener
keeps its existing destination. The renderer offsets Unicode composite glyphs,
clips panes, dims inactive status backgrounds and draws only the active caret.
Status paths below the startup folder are relative, preserving filename visibility.
Messages and overlays remain global.

Initial policy: equal splits with one-cell dividers; 12 columns by 4 rows minimum;
at most 16 panes; automatic orientation compares width with twice the height,
falling back to the other axis when necessary. Focus requires perpendicular
overlap, then prefers the nearest facing edge, physical centre and stable slot.
Tiny terminals show only the focused pane, retaining minimum virtual geometry;
enlarging restores the tree. See design §28 for the complete policy.

Continuation v4 stores the bounded preorder tree and restores focus via the active
view. It rejects malformed kinds, duplicate/out-of-range leaf views and excessive
depth/node counts. Versions 1–3 recover as a single pane, then upgrade on checkpoint.
Native tests exercise geometry, axis fallback, bounds/reuse, independent views,
buffer deletion/rebinding, continuation corruption and Unicode/caret rendering.
The two new PTY groups exercise shared edits/undo, focus, closing, restored layouts,
resizes and transactional picker cancellation/failure/success. Existing migration
coverage now also includes v3.

Verification: **166 native tests** (54 ME across 19 modules + 112 imported),
formatting/type checking, Python compilation, diff checks, and **40 debug and
40 release PTY groups**. A rendered three-pane preview was inspected. The final
relative-status-path refinement also passes native and focused debug/release pane
checks. Nerd fix `8f62716b` repairs nested untyped numeric operand inference, exposed
by the native pane status assertion; its full gate passed 75 stages with two
platform skips. It is backed up on the fix branch and `remove-linux-libc`, and
installed directly from `~/nerd` on that libc branch. No external runtime
dependencies were introduced. ME installation follows commit/push using `just install`, with both pane groups rerun on the
installed executable.

## Verification

This section records the original MS1 baseline; the latest T3d/T4/T5 evidence is
above.

### Headless

`just check`, `just format`, Python tooling compilation and `just test` have
passed. All **43 project-authored named tests are colocated across 16 source
modules**, with many assertions and all 1,093 official Unicode vectors in the
marked test section of `src/characters.n`. All 24 test helper functions and
additional test-only imports live in bare `test { ... }` sections. The 17 former
standalone Nerd test files have been removed.

`just test` uses the single `main.n` root: **155 tests passed**, comprising 43 ME
tests and 112 imported library tests, discovered once rather than repeated per
test program. Inventory comparison verified that all 29 original named tests
remain discoverable exactly once, and all 53 moved test/helper bodies were
preserved before formatting. Unicode regeneration and a second formatting pass
are byte-idempotent. The release executable is byte-identical to the pre-migration
build, confirming no production-code or test-only-code leakage.

### Real terminal integration

`python3 tests/terminal.py --binary _bin/me` and the equivalent release command
passed all **33 scenario groups**, including buffer lifecycle, gutter styling,
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
    after restart; legacy v1/v2 snapshots retain history and upgrade to v3.
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
26. Home-relative dotfile opening/Tab completion and retained buffer history;
    ambiguous live filtering, bare-home/nested directory completion and all save
    forms including completion; spaces/quotes/variables kept literal, explicit
    cwd tilde paths, named-user-like literal filenames and symlink/`..` resolution.
    Native tests cover missing/relative HOME, root/trailing separators and raw
    non-UTF-8 home/suffix bytes, plus safe completion of literal tilde entries.
27. Enhanced cursor press/release pairs move once in every direction; repeat
    events still move. Home/End, Shift selections, delete releases and prompt
    editing use real CSI reports. Diagnostic traces retain cursor repeat/release;
    native editor checks cover counts and release-free message scrolling.
28. Large buffer popup, MRU/current-first order, previous-buffer default, direct
    Enter acceptance, Escape caret preservation, ordered-letter/case-insensitive
    filtering, zero-result Enter/deletion, cursor actions, resize/page scrolling,
    dirty-close refusal and enhanced Ctrl+W associated-text handoff.
29. Buffer access order survives continuation and selects the previous buffer
    after restart. Native checks reject duplicate access IDs and remap close IDs.
30. Full Unicode case folding (ß and sigma), raw/control-byte filename identity
    and safe popup rendering. Native UI checks cover opaque composite clipping,
    Unicode query glyphs and tiny/zero terminal geometry.
31. Multiple CLI files load into buffers while displaying the first successful
    argument. Existing aliases reuse buffers; missing paths remain unwritten.
    Explicit +paths retain recovered work; plain paths reset. Continue after open
    failures; cover spaces, home expansion, raw bytes and unknown flags.
32. Plain CLI files replace an old unnamed snapshot with exactly the requested
    buffers; bare startup restores; +files append/reuse and focus the first path.
    Validate mixed modes, literal leading plus, all-failure erasure, owned-snapshot
    removal failure and terminal restoration. Recovered all-failed +opens stay open.
33. Right-hand preview follows highlighted buffers, not active/disk content.
    Include unsaved text, cancellation/no switching, resize hiding/restoring,
    no-match clearing and unchanged disk bytes. Native tests cover Unicode/tab
    clipping and invariant view selections/MRU across preview paints.

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

## Nerd fixes — fifteen completed

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
| `5535aaf9` | Preserve empty-string quotes at the formatter wrap boundary |
| `46c711eb` | Accept slice-assignment CST targets and retain structured formatting |
| `30b09d20` | Preserve long source test labels in the fallback formatter |
| `7dc86d12` | Keep recursive/default-call parameter bindings out of caller locals |

Fixes are committed and pushed on their own `agent` branches. With Matt's explicit
approval, local Nerd `main` was merged with the active Linux libc-removal work in
a dedicated worktree. The combined gate passed **75 tests, 0 failures, 2 platform
skips**. Integration `c80d7775` preserves both lines of work and updates the new
Linux native-link call to pass the existing referenced-library policy argument.

The shared `~/nerd` checkout remains on **`remove-linux-libc` at `c80d7775`**;
`just install` runs directly there to install the compiler and matching modules.
The integration is pushed to `agent/integrate/me-file-picker` and
`agent/remove-linux-libc`. Local Nerd `main` includes it; **remote main has not
been advanced**. ME's private `.env` compiler/module override is removed: ordinary
`just` commands now use installed `nerd`. Completed clean worktrees and merged
local temporary branches are removed after retention and process checks.

The subsections below retain the installation evidence at the time of each fix.
Where they mention an earlier private compiler or pending integration, the current
installed status above supersedes that historical split.

### Picker-triggered formatter fixes

Nerd `5535aaf9` preserves an empty string even when its quotes do not fit the
remaining wrap column. The old segment loop emitted nothing for zero-length text,
including function-signature probes, deleting an empty default argument in the
new picker. `empty-string-boundary.f` reproduces the invalid output and checks
retained quotes. Full gate **72 passed, 2 platform skips**, then format/direct
install passed; the commit was immediately pushed to its fix branch and retained
on local `main`.

Nerd `46c711eb` allows `CK_Slice` assignment targets in the CST parser, matching
existing executable slice-copy syntax. Otherwise the entire module silently used
basic token formatting. The existing slice fixture's input is preserved with its
new structured-format expectation, plus an additional bounded/open-ended case.
The full gate passed (**72 passed, 2 platform skips**), as did the final focused
suite and complete frontend rerun (**386 passed, 9 skips**). Formatting and direct
install passed, the commit was pushed immediately and retained on local `main`.

Both direct installs used unchanged active libc-removal `174a4576`, not a silent
branch switch/merge. ME's private compiler contains both fixes. Both clean,
completed worktrees/local temporary branches were removed after commit retention
and process checks. Canonical formatting now reaches slice-copy code in ME's
existing buffer/document/codec/replacement/terminal modules too; native and PTY
regressions cover the formatted sources. No local syntax workaround was added.

### CSI key-action library fix

Nerd `40a30f21` fixes traditional CSI cursor/Home/End/tilde reports losing their
press/repeat/release action subparameter. The parser now shares CSI-u action
extraction; missing action remains a legacy press. Its new native regression
fails on the old parser and passes with the fix (109 terminal/imported tests).
ME's actual-key reproducer inserted at column two instead of one before the fix;
all four directions, repeats, selection, deletion and prompt movement are covered.
ME also guards ordinary UI handlers against decoded releases, while `:keys`
continues to show them. No ME escape-parsing workaround was introduced.

Full Nerd gate: **72 passed, 0 failed, 2 platform skips**; formatting/native rerun
and required direct `~/nerd just install` passed. The user-installed checkout is
still unchanged libc-removal `174a4576`; the fix is pushed on its agent branch,
retained on local `main` and included in ME's private compiler/modules. Integration
into the other agent's branch remains coordinated work. The clean completed
worktree is removed after retaining the commit and checking active processes.

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

- No mouse, desktop clipboard integration, repeat
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

### T4 compiler regressions

`30b09d20` fixes fallback formatting of long test labels; structured formatting
already preserved them. `7dc86d12` fixes LLVM lowering that rebound recursive
callee parameters into the caller, causing incorrect values and release-mode
SSA dominance failures. Omitted defaults now use temporary binding tables;
explicit calls do not seed default bindings. Dense regressions cover recursion,
conditional string slices and dependent defaults.

Both fixes passed the full Nerd gate (72 passed, 0 failed, 2 platform skips),
formatting and the required `just install` directly in `~/nerd`. They are backed
up on `agent/fix/format-fallback-test-label` and
`agent/fix/me-file-picker-toolchain`; local Nerd main was then `7dc86d12`. Remote main
has not been advanced. At those direct installations the shared checkout was on
`remove-linux-libc` at `174a4576`. Matt then authorised integration with that
branch. The combined integration
`c80d7775` passed 75 tests with 2 platform skips and is installed directly from
`~/nerd` on `remove-linux-libc`, with matching modules.


### T5 compiler regression: nested numeric operand widths

The final pane-status native assertion uses `22 * 80 + x`, with `x: usize`.
Nerd accepted it but emitted an i32 product as an operand of an i64 addition.
Fix `8f62716b` re-infers whole untyped operands from their concrete sibling's
numeric type, retaining nested operation widths and literal validation. Its
regression covers indexing, both operand orders, wide products, comparisons,
signed/narrow integers and floats, including LLVM and C output.

The full Nerd gate passed **75 stages, zero failures and two platform skips**;
formatting and the focused regression passed. The fix was committed/pushed on
`agent/fix/literal-expression-width`, fast-forwarded into local `main` and the
existing `remove-linux-libc` checkout, and pushed to remote `remove-linux-libc`.
Remote Nerd `main` retains its separate history; no force push or unrelated merge
was performed. Required installation runs directly in `~/nerd` on that libc
branch at `8f62716b`, with matching installed modules. The completed fix worktree and local temporary
branch were removed after verifying clean state, retained commits and no users. ME retains the original assertion without a
compiler workaround.
