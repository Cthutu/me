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

## T2 — Open files with filename completion — agreed, not started

- Add `:e <path>` to open an existing file or create a new file-backed buffer.
- Reuse/focus an already-open file rather than duplicate its buffer.
- Do not discard other unsaved buffers; include opened buffers in continuation.
- Tab completes filenames using the folder prefix already typed.
- Retain Linux filename fidelity, including spaces and non-UTF-8 names.

### Choices to settle before T2 implementation

- First Tab: common-prefix expansion, cycling or a candidate list?
- Directory completion and navigation, hidden files, no-match and ambiguous cases.
- **Proposed, not agreed:** a popup listing files in the folder prefix already
  typed. If adopted, decide when it appears and how selection/accept/cancel work.

No split panes, generic command palette or language services are bundled into T2.

## Agreed MS2 queue — not started

The following tasks were explicitly accepted after T1/T2. This is the intended
sequence, not a claim that interaction details are settled or code exists.
If a filename popup is adopted for T2, its shared infrastructure may need to be
pulled forward rather than creating a one-off implementation.

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
