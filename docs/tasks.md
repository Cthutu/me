# Agreed tasks

This list backs the single PanelCraft task panel. Only explicit agreements become
tasks; optional ideas and open interaction choices remain labelled as such.

## T0 — Replace the ME panels — completed

Removed the previous progress, design and feature panels. Created one agreed-task
tracker. Detailed design and verification evidence remain in repository documents.

## T1 — Improve mode and status readability — in progress

- Normal state: green cursor and green status bar.
- Insert state: red cursor and red status bar, signalling editing danger.
- Use a clearer UTF-8 status presentation without requiring a special font.
- Retain textual mode labels, file/modified/conflict/persistence information,
  position and buffer identity. Keep narrow terminals and resizing safe.
- Validate actual terminal output, then commit, push and install.

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

No split panes, generic command palette or language services are implied by T2.
