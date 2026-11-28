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
interaction is agreed and implemented; T4/T4a/T4b, T5/T5a and T6 are complete. T2's filename
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
leader shows its known-key menu after one second. Other roots, toggles and
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

### T4b — Sliding Space menu overlay — done

- Show the Space menu as a styled overlay sliding up from the bottom, retaining
  the one-second delay and immediate Space Space action.
- Preserve underlying views/messages and mask native/composite text underneath.
- Prepare declarative grouped sequences, path headings and parent navigation.
- Space b d remains an illustrative proposal, explicitly not an active binding.
- Verified formatting/checking, 162 native tests (50 ME + 112 imported), all 38
  debug and 38 release PTY groups, Python compilation and diff checks. A rendered
  PTY preview was visually checked; release installation uses `just install`.
- Follow-up: reduce the menu delay to one second. Native checks cover the
  999/1,000 ms boundary; focused debug overlay/file-picker and release overlay
  checks verify the updated timing.


### T5 — Split-pane UI — done

- Support pane creation, focus and closing, with independent views of shared text.
- Keep shared buffer history and semantic position adjustment across views.
- Space w opens the Windows submenu: h splits side by side; v above/below;
  s chooses the longest axis, accounting for terminal cell proportions; c closes
  the current pane; w picks a file before automatic splitting.
- Space h/j/k/l or Space plus cursor keys focus the corresponding neighbour.
  Stay put when none exists; do not wrap.
- h/v/s share the current buffer with a new independent view and focus it.
- Closing a pane keeps its buffer open. Keep the last pane rather than quitting.
- Space w w creates/focuses a pane only after a successful file selection/open;
  cancellation or failure preserves the layout. Space Space stays as it is.
- Document initial ratios, minimum sizes, neighbour ties and resize policy while
  implementing. See design §28 and questions for the agreed scope.
- Implemented as a bounded split tree with one view per leaf and global overlays.
  Continuation v4 retains tree/focus/views; versions 1–3 migrate to a single pane.
  Buffer deletion rebinds affected panes without collapsing the layout.
- Initial policy: equal splits, one-cell dividers, 12 columns by 4 rows minimum,
  at most 16 panes. Small terminals retain the tree and show the focused pane.
  Directional ties use facing-edge distance, physical centre and stable slot.
- Verified 166 native tests (54 ME + 112 imported), all 40 debug and 40 release
  PTY groups, format/type checking, Python compilation, diff checks and a rendered
  three-pane preview. The final relative-status-path refinement has native and
  focused debug/release pane coverage. Required release installation follows
  commit/push, with both pane groups checked against the installed executable.

### T5a — Pane feedback, split naming and terminal exit — done

- Brighten the focused pane background, including blank space and composite glyphs.
- Correct Space w h to side by side and Space w v to above/below. Retain automatic
  orientation and existing layouts; make menu/help descriptions unambiguous.
- Fix queued/delayed terminal reports reaching the shell on exit, in Nerd std.term.
  Verify normal, forced and signal exits with clean subsequent shell input.
- Nerd terminal cleanup `68c2f47d` and assertion-value fix `2b3f6987` each passed
  the full 77-stage gate with two platform skips. Both are pushed on their fix
  branches and remove-linux-libc, integrated into local main and installed directly
  in ~/nerd on remove-linux-libc. Completed worktrees/local branches are removed.
- ME verification: 166 native tests, all 41 debug and 41 release terminal groups,
  formatting/type checking/idempotence, Python compilation and diff checks passed.
  A rendered preview was visually checked. Required ME installation follows
  commit/push, with installed exit/pane/leader smoke checks.

### T5b — Ctrl+W closes the focused pane — done

- Ordinary Ctrl+W uses pane closing rather than buffer deletion. Collapse only
  the focused pane, retaining buffers and unsaved work; keep the last pane open.
- Preserve other panes' buffer identities and navigation, including shared views.
- Retain selected-buffer deletion/refusal inside the buffer popup and :kill[!].
- Regression coverage includes three distinct buffers, shared/unsaved buffers,
  legacy control bytes, enhanced reports, ignored releases and paired text.
- Verification: 167 native tests (55 ME + 112 imported), all 42 debug PTY groups
  and all eight release pane/buffer-picker groups passed. Formatting is
  idempotent; type checking, Python compilation and diff checks passed. The final
  prompt-cancellation preservation also passed native and focused release checks.
- Required commit/push and release installation follow verification, with installed
  Ctrl+W pane and selected-buffer popup regression checks.

### T5c — Ctrl+N creates an unnamed buffer — done

- Create/focus a new unnamed buffer in the current pane. Originally entered
  Insert; T17 supersedes that policy with Normal.
- Preserve existing buffers, unsaved work and other panes.
- Support legacy and enhanced reports; ignore releases and suppress paired text.
- Retain normal continuation and popup input scope; reject counts.
- Verified 168 native tests (56 ME + 112 imported), all 43 debug terminal groups,
  the release Ctrl+N scenario, type checking, idempotent formatting, Python
  compilation and diff checks. Required commit/push and release installation
  follow, with the installed new-buffer scenario checked afterwards.

### T6 — Explicit repeat recording and playback — done

- Implement the agreed recording/replay direction in design §12: Normal-state
  `[` starts recording, `]` ends it and `.` replays; brackets remain text in Insert.
- Recording uses normal individual undo units; one replay is one undo unit.
- Preserve the agreed failure policy: retain completed edits as a single undoable
  group and report the failure, rather than automatically rolling them back.
- First scope: current-buffer editing/navigation and one recording per session,
  reusable in another buffer. Capture semantic mode/selection changes, correct
  recipes on undo/redo, refuse file/pane/buffer/Space actions and retain grouped
  history in continuation. Initial policies and bounds are in design §32.
- Verified 176 native tests (64 ME + 112 imported), all 45 debug and 45 release
  terminal groups, and final focused repeat checks on both profiles, including
  count refusal. Formatting is idempotent; type checking, Python compilation
  and diff checks passed. Required commit/push and release installation follow,
  with installed recording/failure PTY scenarios checked afterwards.

Language intelligence, desktop clipboard and configuration are not added to this
queue by implication.


### T7 — Normal d deletes — done

Historical delivery: T8 supersedes unselected single-d behaviour after Matt's
pending-command clarification; selected d remains immediate.

- Bind Normal d to the existing Delete command: selection or one forward grapheme.
- Keep Normal, clipboard contents, ordinary undo/redo and repeat integration.
- Retain literal d in Insert/prompts/pickers and existing Ctrl+D duplication.
- Follow existing Delete behaviour at line endings/EOF and for unsupported counts.
- Verified 177 native tests (65 ME + 112 imported) and the focused Normal d PTY
  scenario on debug/release builds. Coverage includes Unicode graphemes, selected
  text, EOF, clipboard preservation, undo/redo, repeat, literal Insert/prompt text
  and unsupported counts. Formatting/idempotence, type checking, Python compilation
  and diff checks passed. Required commit/push and release installation follow,
  with the installed deletion scenario checked afterwards.


### T8 — Pending d and counted dd line deletion — done

- d immediately deletes an existing selection; otherwise it waits for dd.
- dd deletes the current line; a numeric prefix such as 3dd deletes that many.
- Show pending d/count, allow Escape cancellation, and preserve Insert literals.
- Keep clipboard, one-operation undo, shared views and semantic repeat support.
- See design §34 for cancellation, final-line/BOM/ending and explicit-count policies.
- Verified 180 native tests (68 ME + 112 imported), all 47 debug and 47 release
  terminal groups, plus final focused deletion checks on both profiles for the
  explicit-count/selection refinement. Formatting is idempotent; type checking,
  Python compilation and diff checks passed. Required commit/push and installation
  follow, with installed deletion checks afterwards.

### T9 — Modes M1: foundation and Markdown — in progress

- Introduce customisable systems based on recognised file type.
- Modes determine LSP, formatting, syntax highlighting, indentation and related
  file-type behaviour and provider choices.
- First modes milestone: foundations plus Markdown support as the first mode.
- Add LF/CRLF and recognised file type to the status line.
- Matt requested implementation of Markdown support after activating T9.
- Built-in delivery: case-insensitive .md/.markdown recognition, buffer-owned
  revision-cached source highlighting shared by panes, actual LF/CRLF/MIXED/NONE
  status, Plain Text fallback and two-space Markdown indentation fallback.
  Existing indentation detection and Enter behaviour remain in use.
- Successful save-as and restoration rederive mode; failed/cancelled saves retain
  it. Narrow panes prioritise existing status and warnings over added metadata.
- Configuration/schema, overrides and LSP/formatter providers remain open T9 work;
  this delivery does not complete the whole customisable modes milestone.
- Agreed follow-up: fully optional buffer-owned line metadata and incremental
  Markdown highlighting. Then begin LSP support with Nerd mode (T16).
  Other later modes milestones remain unscoped; macro follow-ups stay queued.
  See design §35 and questions.
- Built-in delivery verified with 187 native tests, all 57 debug terminal groups
  and nine focused release groups, plus final Markdown/lexer regression checks.
  Type checking, idempotent formatting, Python compilation and diff checks passed.
  Required commit/push and release installation follow; detailed evidence is in
  ms1-progress.
- Incremental follow-up delivered: optional typed line metadata, edit-derived
  invalidation, line-relative spans and propagation until lexer state converges.
  Plain Text allocates no cache; panes share analysis. Setext dependencies and
  fences are retained. Document projection/index rebuilding remains linear.
- Verified 189 native tests, all 58 debug terminal groups and 13 focused release
  groups, including full-analysis comparisons through batched edits/history and
  real terminal fence/setext undo. Type checking, idempotent formatting, Python
  compilation and diff checks passed. Required commit/push/install follow, with
  installed Markdown checks afterwards. T16 is the next agreed mode/LSP work.



### T10 — Cancel unfinished recordings — done

- Ctrl+G cancels in Normal or Insert without reverting edits or replacing the
  previous completed macro. Keep the current interaction state.
- Quitting cancels the draft; `:q`, `:q!`, `:wq` and terminal signals preserve
  their ordinary continuation/save/discard behaviour.
- `[]` clears the completed macro. Release and paired text events act once;
  cancellation also clears pending counts/delete commands.
- Verified 181 native tests (69 ME + 112 imported), all 48 debug terminal
  scenarios, release cancellation and both repeat scenarios, idempotent formatting,
  type checking, Python compilation and diff checks. Required commit/push and
  release installation follow, with installed cancellation checked afterwards.

### Agreed bug follow-ups — pending

- Persist completed macros across restarts and record `:` commands for playback;
  quitting must discard the draft and preserve the previous macro.

### T11 — Backspace retains Insert — done

- Ordinary, legacy and Ctrl+Backspace preserve the interaction state, including
  at the start of a buffer or in an empty buffer.
- Preserve existing grapheme/word deletion, selection, history and prompt behaviour.
- Verified typing immediately afterwards, including macro playback and empty-buffer
  no-ops, across ordinary/legacy/enhanced reports and paired release events.
- The new terminal regression fails against the previous installed release.
  All 181 native tests and four focused terminal groups on both debug and release
  passed, including existing word-deletion and repeat checks. Formatting is
  idempotent; type checking, Python compilation and diff checks passed.
  Required commit/push and installation follow, with installed Backspace checked
  afterwards.


### T12 — Backspace selection rules and legacy reports — done

- Insert Backspace deletes backwards or removes the selection; Normal Backspace
  only removes a selection, with no effect on text/caret/history otherwise.
- Legacy 0x08 and 0x7f both mean ordinary Backspace. Explicit Ctrl+Backspace retains
  word deletion in Insert and selection-only deletion in Normal.
- Retain interaction state, selection replacement, history, prompt editing and
  playback; keep the existing Insert Tab-space grouping policy.

- Verified 181 native tests and six focused terminal groups on both debug and
  release (both Backspace groups, word deletion, both repeat groups and Normal
  deletion). The new Normal no-selection regression fails on the previous release.
  Formatting is idempotent; type checking, Python compilation and diff checks
  passed. Required commit/push and installation follow, with installed Backspace
  checked afterwards.


### T13 — Confirm existing save-as targets — done

- :w/:ww to a different existing target show File <file> exists - save? (Y/N).
- Resolve home-relative/relative/absolute paths consistently. Y saves and
  reassociates; N/Escape preserve target and buffer path. Same-inode aliases use
  ordinary save/conflict rules; :w! remains explicit force.
- Revalidate source revision and approved target identity, metadata and bytes.
  Keep confirmation input isolated and resume :wq only after successful approval.
- Verified 181 native tests and six debug plus six release terminal groups,
  including relative/home/absolute paths, spaces, completion, cancellation,
  reassociation, same-inode aliases, symlink retargeting, target/source changes and
  :wq continuation. Type checking, idempotent formatting, Python compilation and
  diff checks passed. Required commit/push and installation follow, with an
  installed confirmation check afterwards.

### T14 — Refuse :q with unsaved changes — withdrawn

Delivered in 14e9410, then withdrawn by Matt after recalling snapshot recovery.
Ordinary :q should checkpoint unsaved work and quit, as it did before T14.

### T15 — Restore snapshot-based :q — done

- Restore ordinary :q checkpointing unsaved/unnamed work before exit.
- Keep refusal on checkpoint failures and for unsafe non-persisting sessions.
- Keep macro draft cancellation, :wq/:q! behaviour and T13's overwrite confirmation.

- Verified 181 native tests and nine focused terminal groups on both debug and
  release, including actual :q recovery, unnamed work, macro cancellation,
  checkpoint failures, non-persisting sessions and overwrite confirmation.
  Type checking, idempotent formatting, Python compilation and diff checks passed.
  Required commit/push and installation follow, with installed recovery and
  confirmation checked afterwards.


### T16 — Nerd mode and LSP support — first delivery complete; further services queued

- Recognise `.n` as Nerd, use detected indentation or a four-space fallback,
  and provide incremental stateful lexical highlighting through an optional
  typed cache shared by panes. Handle comments, strings/triple strings, packed
  integers and nested interpolation without regex matching or source mutation.
- Start the installed `nerd lsp` lazily for named Nerd buffers. Keep bounded,
  non-blocking protocol transport independent of syntax metadata. Synchronise
  opens, full-content changes and closes using document revisions/versions.
- Show current diagnostics in the gutter and wide status line; `:diagnostics`
  displays details and `:lsp-restart` retries failures. Suppress stale results
  across every open Nerd buffer, including dependency edits. Crash/timeout and
  malformed-message handling preserve editing; teardown is bounded and reaped.
- First-delivery defaults and limits are in design §35. Completion, hover,
  navigation and provider/recognition configuration remain later
  scope; T18 adds Nerd formatting on save. This does not select a Markdown provider.
- Three independently reproduced Nerd bugs took priority: indexed compound
  assignments, array-field indices mistaken for box type arguments, and packed
  literals hiding source tests. Dedicated worktrees and complete compiler gates
  precede direct installation from the existing libc-fix branch. Detailed
  evidence and final ME verification are recorded in MS1 progress.
- Verified: 195 native tests, all 62 debug terminal groups and eight focused
  release groups passed. Type checking, formatting idempotence, Python compilation
  and diff checks passed. Commit/push and release installation complete this slice;
  the installed Nerd scenarios and release-binary identity are checked afterwards.

### T17 — Normal initial state, intelligent indentation and character cuts — done

- Always begin new/opened/restored buffers in Normal, including Ctrl+N and
  empty/BOM-only files; merely focusing existing work retains its state.
- Intelligent Enter/o/O indentation: retain whitespace and local line endings,
  add lexical Nerd delimiter rules and Markdown list/quote/task continuation.
  Keep generated edits as single undo units and update shared views.
- `x` without selection cuts one complete grapheme, including indivisible CRLF,
  into the characterwise clipboard. EOF preserves clipboard/history.
- Initial implementation details are in design §36; general mode configuration
  remains open. This supersedes empty-buffer Insert and no-auto-indent policies.
- Verified: 199 native tests (87 ME + 112 imported), all 64 debug terminal
  groups and five focused release groups passed. Type checking, idempotent
  formatting, Python compilation, UTF-8 and diff checks passed. Commit/push and
  release installation complete this slice; installed editing smoke follows.


### T18 — Format Nerd files on save — done

- Run the installed `nerd format` on a private copy before committing all Nerd
  saves, including clean buffers and save-as into `.n`.
- Retain overwrite approval and revalidation, atomic replacement and source edits
  on formatter failure. Keep successful formatting undoable and repair all views.
- Formatting runs outside the terminal loop with a 30-second child deadline,
  isolated standard descriptors and cancellation/timeout termination/reaping.
  Guard revisions/target identity and serialise save-and-quit; see design §37.
- Verified: 201 native tests (89 ME + 112 imported), all 68 debug terminal
  groups and eight focused release groups passed. Nerd picker fixtures now
  expect the formatter's trailing newline; affected/remaining groups passed on
  rerun. Type checking, idempotent formatting, Python compilation, UTF-8 and
  diff checks passed. Required commit/push and installation follow; the panel
  records the final revision and installed smoke results.
