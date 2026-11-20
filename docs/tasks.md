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
- Further Enter executes the command; editing dismisses the list.
- The same path completion works for `:w`, `:w!` and `:ww`.
- Implementation choices: case-sensitive byte-prefix matches, deterministic
  byte ordering, dotfiles only when the current component starts with a dot,
  accessible symlink targets, and explicit no-match/directory errors.
- Paths after the first separator are literal (including whitespace); no shell
  quoting or expansion. Presentation sanitises controls/invalid UTF-8 without
  changing the underlying filename bytes.
- Synchronous discovery is capped at 65,536 entries and 4,096 matches; exceeding
  either bound reports an error instead of pretending partial results are complete.

Verification: 25 project native tests across 17 files and all 18 PTY scenario
 groups on both debug and release builds passed, including actual Tab events,
 list selection/cancellation, unsaved-buffer reuse, byte-safe paths and resize.

No split panes, generic command palette or language services are bundled into T2.

## Agreed MS2 queue — not started

The following tasks were explicitly accepted after T1/T2. This is the intended
sequence, not a claim that interaction details are settled or code exists.
T2 uses the existing message area, not a separate popup layer. The shared MS2
popup foundation remains queued; no one-off popup infrastructure was introduced.

### T3 — Shared popup/picker infrastructure and buffer switcher

- Build the shared popup/picker foundation, first exercised by a buffer switcher.
- Keep input/focus, query, candidate selection and dismissal separate from buffers.
- Choose bindings and exact accept/cancel behaviour before implementation.

### T4 — File picker

- Discover and filter file candidates without blocking normal input.
- Support cancellation and opening/focusing a selected file.
- Settle discovery roots, matching, hidden/ignored files and symlink policies.
- Reuse T3; retain Linux filename fidelity and validate stale candidates.

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
