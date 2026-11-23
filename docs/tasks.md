# Agreed tasks

This list backs the single PanelCraft task panel. Only explicit agreements become
tasks; optional ideas and open interaction choices remain labelled as such.

## T0 — Replace the ME panels — completed

Removed the previous progress, design and feature panels. Created one agreed-task
tracker. Detailed design and verification evidence remain in repository documents.

## T1 — Improve mode and status readability — completed

- Normal state: green cursor and green status bar.
- Insert state: red cursor and red status bar, signalling editing danger.
- Use a clearer UTF-8 status presentation without requiring a special font.
- Retain textual mode labels, file/modified/conflict/persistence information,
  position and buffer identity. Keep narrow terminals and resizing safe.
- Validated native cell contrast, mode colours, narrow warnings and layouts;
  real PTY output includes both palettes, UTF-8 markers and complex-glyph RGB.
- Full verification: 23 project native tests across 16 files and 16 PTY scenario
  groups on both debug and release builds. Committed/pushed as `02b938d` and
  installed; installed-binary presentation smoke passed.

## T2 — Open files with filename completion — completed

- Add `:e <path>` to open an existing file or create a new file-backed buffer.
- Reuse/focus an already-open file rather than duplicate its buffer.
- Do not discard other unsaved buffers; include opened buffers in continuation.
- Tab completes filenames using the folder prefix already typed.
- Retain Linux filename fidelity, including spaces and non-UTF-8 names.

### Agreed interaction and implementation

- User accepted Tab-triggered common-prefix expansion and unique completion;
  directory matches append `/`.
- Ambiguity opens a selectable list in the existing message area, not a live popup.
  Up/Down or further Tab selects, Enter accepts without executing the command,
  and Escape dismisses only the list, retaining the typed path.
- Further Enter executes the command. T2a below refines editing/filtering and
  keeps the input anchored at the bottom.
- The same path completion works for `:w`, `:w!` and `:ww`.
- Implementation choices: case-sensitive byte-prefix matches, deterministic
  byte ordering, dotfiles only when the current component starts with a dot,
  accessible symlink targets, and explicit no-match/directory errors.
- Paths after the first separator preserve bytes (including whitespace); no shell
  quoting or variable expansion. T2g adds leading `~`/`~/` home expansion.
  Presentation sanitises controls/invalid UTF-8 without
  changing the underlying filename bytes.
- Synchronous discovery is capped at 65,536 entries and 4,096 matches; exceeding
  either bound reports an error instead of pretending partial results are complete.

Delivery verification (`c153e0f`): 25 project native tests across 17 files and
all 18 PTY scenario groups on both debug and release passed, including actual Tab
events, list selection/cancellation, unsaved-buffer reuse, byte-safe paths and resize.

No split panes, generic command palette or language services are bundled into T2.

## T2a — Command completion and persistent bottom-anchored filtering — completed

- Tab completes command names before their separating space, including an empty
  command prompt. File commands switch to filename completion after that space.
- Use the same common-prefix, ambiguity-list, selection and accept/cancel rules.
  Completing/accepting a command must never execute it.
- Keep the command-entry line on the terminal's bottom row; show matches above it.
- Once open, keep filtering on typing and deletion, including one/zero matches.
  Do not silently expand the typed query while filtering; Enter accepts a match.
- Backspace can widen results beyond the original prefix. No-match navigation and
  Enter are harmless; Escape still dismisses the list without losing the query.
- Reuse a directory snapshot within the same folder prefix; changing folders
  rebuilds it. Closing/reopening completion refreshes discovery.
- Command-name completion ends when entering unsupported non-file arguments
  (for example, the number in `:buffer N`); numeric argument completion is not
  included. Cursor navigation still dismisses the list.

Verification: 26 project native tests across 17 files and all 20 PTY scenario
groups on both debug and release passed. Native checks also prove snapshot reuse,
fresh discovery on reopening, safe acceptance and no-match handling.


## T2b — Second-slash replace-all and confirmation — completed

- A second unescaped `/` switches forward search into replacement:
  `/old/new` replaces all non-overlapping matches throughout the buffer.
- Remove `:replace` and the `g` option; accept an optional closing slash.
- `/old/new/c` confirms: Y replaces, N skips, A applies all remaining, Escape
  stops while preserving approved edits. One complete/stopped operation is one undo.
- Preserve literal/case-sensitive matching, escaping, BOM/endings and shared-view
  semantic adjustment. Do not search newly inserted replacement text.
- Ordinary `/term` remains search; literal slashes must be escaped. T2c corrects
  the mistaken removal of the existing `//` origin; `??` also remains.
- Preview/cancel/malformed input never edit the document. Checkpoints during
  confirmation already contain a complete grouped history record.
- Implementation safety: other commands are blocked during confirmation; abort
  on unexpected document revision changes. Stop confirmation before saving.
- Verified: 28 project native tests across 17 files and all 22 PTY scenario
  groups on debug and release. Coverage includes partial-history codec/recovery,
  shared views, original-match semantics, skips, stopping, deletion, UTF-8/BOM/
  line endings and single undo/redo. Installed-binary checks run at completion.

## T2c — Retain double-slash search origin — done

- Restore `//term` as forward search from the document beginning; `/term`
  continues from the caret and `??term` remains backward from document end.
- Parse the optional leading origin before looking for replacement separators.
  `//old/new` and `//old/new/c` remain valid replacement forms.
- Preserve escaped literal slashes, remembered terms, preview cancellation and
  undo/confirmation semantics. An origin prefix alone never triggers an edit.
- Verified: 29 native tests and all 23 debug/release PTY groups. A confirmed
  compiler local-table use-after-free was fixed separately in Nerd `98883071`
  before rerunning the complete native suite. Installed checks run at completion.

## T2d — Colocate native tests — done

- Move the maximum number of native tests into source `test` sections, with
  helpers and test-only imports excluded from normal builds.
- All 29 named tests and 24 helpers moved across 14 implementation modules;
  remove all 17 standalone native test files. Cross-layer tests belong in the
  highest relevant module, without reversing production dependencies.
- `just test` runs `nerd test main.n`, discovering imported tests once. Keep real
  terminal/process checks in `tests/terminal.py`.
- Generate all 1,093 Unicode vectors into a marked `src/characters.n` test section,
  preserving handwritten code and tests. Update formatting and contributor docs.
- Verified: all 138 native tests pass (29 ME + 109 imported library tests);
  original ME test inventory is preserved exactly once; generation/formatting
  are idempotent; release binary is byte-identical to the pre-migration build.
  All 23 PTY groups pass on debug and release. Installed help/origin smoke passed;
  installation and smoke are repeated after pushing the completed change.

## T2e — Normal HJKL navigation and q line selection — done

- Add Normal `h`/`j`/`k`/`l` as arrow-equivalent left/down/up/right movement,
  including counts, grapheme boundaries, preferred columns and selection clearing.
- Reassign line selection from `l` to `q`, retaining counts/repeated extension and
  typed linewise clipboard behaviour. Arrow bindings remain available.
- Preserve literal HJKL/q input in Insert and prompts; leave uppercase bindings
  unchanged. Update help, references and native/real-key regressions.
- Verified: 140 native tests (31 ME + 109 imported), all 24 PTY groups on debug
  and release, and formatting idempotence. Installed HJKL/q and help smoke run
  after committing/pushing and installing the release executable.

## T2f — Keyboard diagnostics and std.term negotiation audit — done

- Add `:keys` for capabilities and decoded key/action/modifier/text inspection;
  test Ctrl+H versus Ctrl+Backspace without editing or saving. Escape closes;
  Alt+Page Up/Down scroll. Keep bounded, safe, non-persistent event history.
- Expose actual Kitty flags and probe completion in Nerd; distinguish zero,
  negative and pending replies. Fix partial-flag capability overclaims and fully
  consume private CSI replies. Keep negotiation in `std.term`, not local escapes.
- Add native and actual-protocol PTY regression coverage, command completion and
  docs. Dedicated Nerd worktree/full gates precede toolchain integration.
- Nerd `7cd7e0ec` is pushed and retained on local main; its full gate passed
  (72 passed, 2 platform skips). Required direct `~/nerd just install` passed from
  unchanged libc-removal `174a4576`; coordinated integration there remains pending.
- ME verification: 144 native tests (33 project + 111 imported), all 25 PTY groups
  on debug/release, and focused status/DA/key/resize/scroll checks. Installed checks
  run after push/install. No local protocol implementation was introduced.

## T2g — Home-relative opening, saving and completion — done

- Fix the reported `:e ~/.wezterm.lua` / `:e ~/.we<Tab>` failure: expand a complete
  leading `~`/`~/` from `HOME` consistently in file opening, saving and discovery.
- Keep `~/` in completed prompt paths; bare `~` completes to `~/` first. Preserve
  dotfile rules, live filtering, spaces/non-UTF-8 bytes and Linux symlink/`..`
  semantics. Do not add shell quoting, variables or `~user` lookup.
- Reject missing/non-absolute HOME without changing files/buffers. Keep literal
  leading tilde entries accessible with `./~`; completion adds `./` where needed
  rather than accidentally redirecting a literal cwd entry into the home folder.
- Colocated native regressions cover expansion edge cases and escaped literal
  completion; actual-key PTYs cover the reported dotfile case, buffer reuse,
  filtering, nested directories, all save forms, literal paths and symlink `..`.
- Verification: 146 native tests (35 project + 111 imported) and all 26 terminal
  scenarios pass on debug/release. Formatting/checks and Python compilation pass;
  final installed home-path/completion checks run after commit/push/install.

## T2h — Enhanced key releases must not execute commands — done

- Reproduce reported double cursor movement with actual `CSI 1;1:1C` /
  `CSI 1;1:3C` press/release bytes. Fix Nerd's shared CSI parser to retain event
  types for cursor, Home/End and tilde keys, not only CSI-u. Keep legacy presses
  and intentional key repeats working; do not work around parsing in ME.
- Ignore decoded releases before ordinary editor UI handlers, including message
  scrolling, while retaining releases in `:keys` diagnostics.
- Colocated native regressions cover key/action/modifier decoding, navigation
  counts, message scrolling and diagnostic capture. PTYs cover all four cursor
  directions, repeats, Home/End, Shift selections, deletion, prompts and traces.
- Nerd `40a30f21` pushed and retained on local main: full gate 72 passed with
  2 platform skips; formatting, native rerun and direct Nerd install passed from
  unchanged libc-removal `174a4576`. Coordinated integration there is still pending.
- ME: 148 native tests (36 project + 112 imported), all 27 PTY groups on debug and
  release, checks/format idempotence/Python compilation passed. Installed enhanced
  navigation and diagnostic regressions run after commit/push/install.

## Agreed MS2 work

The following tasks were explicitly accepted after T1/T2. T3's detailed
interaction is now agreed and implemented; T4 is in progress; T5–T6 remain queued. T2's filename
completion still uses the existing message area, separate from the reusable popup.

### T3 — Popup/picker foundation, buffer switcher and Ctrl+W — done

- Normal `,` opens a large popup with a reusable top fuzzy-search widget.
- Case-insensitive ordered-letter matching; Unicode 16 default full case folding.
  Keep MRU result order, current first, second row selected initially. Enter chooses.
- Escape cancels; Up/Down/Page keys select/scroll; query edits never edit documents.
  Keep input/focus, query, candidate selection and dismissal separate from buffers.
- Original delivery: Ctrl+W closes the active saved buffer; T3d below adds
  highlighted-row closing. Otherwise show
  an error. No implicit save/discard; retain `:kill!` for explicit forced removal.
- Persist validated MRU order in continuation v3 with v1/v2 import. Keep view IDs,
  history and typed-buffer fidelity independent; preserve literal comma in Insert.
- Fix cross-view associated-text suppression, not just Ctrl+W's immediate case.
- Found/fixed two Nerd formatter issues in dedicated worktrees: empty defaults at
  the wrap boundary and CST slice-assignment targets. Full gates/install/push and
  cleanup follow the compiler policy; no ME syntax workaround.
- Nerd `5535aaf9` / `46c711eb` pushed to their fix branches and retained on local
  main; each full gate passed (72 passed, 2 platform skips). Both direct installs
  passed from unchanged libc-removal `174a4576`; integration there remains pending.
- ME verification: 154 native tests (42 project + 112 imported), all 30 PTY groups
  on debug/release, format/check/Python compilation and Unicode regeneration
  idempotence. Installed picker/recovery/Unicode-byte-path checks follow push/install.

### T3a — Multiple CLI files — done

Initial startup/failed-reset policy below is superseded by T3b; opening multiple
buffers and displaying the first successful argument remains unchanged.

- Accept `me [-r] [filename ...]`: load all paths into buffers and display the
  first successful filename. Keep restored work unless reset was requested.
- Reuse existing buffers/inode aliases and retain history/view state. Keep missing
  files unwritten until explicit save. Continue after individual open failures;
  exit 2 only if no buffers remain, preserving any old recovery snapshot.
- Keep existing option rejection, `-r`, home expansion and byte-safe paths.
- Verification: 154 native tests (42 project + 112 imported); 31 PTY groups on
  debug/release. New CLI checks cover first-file display, picker access, aliases,
  missing files, recovery, partial/all failures, spaces/home/raw bytes and options.
- Installed multi-file CLI regression/help checks follow commit/push/install.

### T3b — Fresh filename startup and opt-in continuation — done

- Plain `me file1 file2` erases the prior snapshot and loads only those buffers,
  no extra unnamed buffer. Display the first successful path.
- Bare `me` restores. Explicit `+filename` restores then adds/reuses files without
  losing other buffers/history/view state. Strip one plus before path expansion.
- Reject plain/+ mixtures, `-r`/+ and bare `+` before touching continuation;
  preserve literal leading-plus paths through `./+name` / `++name` respectively.
- Erase the snapshot before any opens, even if every path fails; erasure failure
  is fatal. `-r` also erases. Hold the continuation lock; second instances must
  never delete the owner's snapshot. Normal checkpointing records new work.
- Regression PTYs cover old unnamed work, exact buffer counts, bare restoration,
  +path focus/reuse, mixed-mode safety, failed opens/erase and terminal restoration.
  Existing recovery/alias tests now explicitly use +paths when restoration is intended.

### T3c — Right-hand buffer preview — done

- Read-only preview follows the highlighted picker entry without switching buffers.
- Render live in-memory text (including unsaved changes) from the first line,
  clipping rows/long lines with Unicode/grapheme/tab-safe rendering and no I/O.
- Preserve all view selections, history and MRU. No matches clear preview.
- Keep the query full-width; narrow/short screens show only the full-width list.
- Native and PTY checks cover selection changes, unsaved data versus disk,
  cancellation/no switching, empty results, Unicode/tabs/controls and resize.
- T3b/T3c verification: 155 native tests (43 project + 112 imported), all 33 PTY
  groups on debug/release, format/check/Python compilation/idempotence passed.
  Installed startup, CLI, preview/picker and help regressions follow push/install.

### T3d — Close the highlighted buffer from the picker — done

- Ctrl+W closes the highlighted buffer while the list is open; outside it, close
  the active buffer. A query with no matches makes Ctrl+W a no-op.
- Retain unsaved/new/missing-buffer refusal. The picker stays open on success
  or refusal, preserving query/caret and the selected row clamped to remaining
  matches. Rebuild candidate identities and preview after removal; empty results
  remain open. This refines the initial T3d dismissal behaviour.
- Closing another buffer preserves active work; closing the active buffer uses
  the existing MRU fallback, or a fresh empty buffer after the last close.
- Cover legacy/enhanced input, associated text and release suppression, filtering,
  dirty active/selected buffers, retained query/selection and last-buffer fallback.
- Verification: format/check, all 156 native tests, all 34 debug PTY groups,
  all five release buffer-picker PTY groups, Python compilation and diff checks
  passed. Pushed and installed at `b5be63e`; installed selected-close smoke passed.

### T4 — File picker and Space leader — done

- Discover and filter file candidates without blocking normal input.
- Support cancellation and opening/focusing a selected file.
- Settle discovery roots, matching, hidden/ignored files and symlink policies.
- Reuse T3; retain Linux filename fidelity and validate stale candidates.

Agreed delivery: startup-folder root, Unicode case-insensitive subsequence
matching, Normal Space Space/`:files`, all hidden/ignored files included, and
file/directory symlinks followed with ancestry-based cycle detection. The Space
leader shows its known-key menu after two seconds. Other roots, toggles and
previewing unopened contents are separate choices.

Discovery uses a cancellable child and non-blocking pipe; query filtering and
candidate publication advance in bounded simulation batches. Reopening scans
fresh; no-match/stale/error cases retain the popup. Existing buffers are reused,
unsaved work survives cancellation/opening, and Ctrl+W never closes a file row.

Verification: installed Nerd `c80d7775` on `remove-linux-libc`; formatting,
checking, all 159 native tests (47 ME + 112 imported), all 36 debug and 36 release
PTY groups, Python compilation and diff checks passed. Both ME profiles have no
ELF shared-library dependencies or interpreter. Release installation uses
`just install`; the focused installed picker checks cover both new PTY groups.


### T4a — Ctrl+HJKL navigation — done

- Ctrl+H/L mirror Ctrl+Left/Right word movement; Ctrl+J/K mirror Ctrl+Down/Up
  scrolling. Preserve interaction mode and existing count/Shift behaviour.
- Use enhanced key reports; retain ambiguous legacy Backspace/Enter behaviour.
- Suppress associated text and ignore releases while retaining repeats.
- Verified formatting/type checking, 160 native tests (48 ME + 112 imported),
  all 37 debug PTY groups and the focused release Ctrl+HJKL group, plus Python
  compilation and diff checks. Installation uses the tested release build.

### T5 — Split-pane UI

- Support pane creation, focus and closing, with independent views of shared text.
- Keep shared buffer history and semantic position adjustment across views.
- Agree commands/bindings, split directions and sizing before implementation.
- Closing a pane is distinct from killing its buffer.

### T6 — Explicit repeat recording and playback

- Implement the agreed recording/replay direction in design §12: Normal-state
  `[` starts recording, `]` ends it and `.` replays; brackets remain text in Insert.
- Recording uses normal individual undo units; one replay is one undo unit.
- Preserve the agreed failure policy: retain completed edits as a single undoable
  group and report the failure, rather than automatically rolling them back.
- Resolve remaining capture/state/selection, redo, scope and storage choices first.

Language intelligence, desktop clipboard and configuration are not added to this
queue by implication.
