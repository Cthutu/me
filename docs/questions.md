# Continuing the design discussion

See [design.md](design.md) for established decisions. Record conclusions there as
well as updating this agenda.

## Implementation note

MS1 now has a runnable implementation. Remaining questions below include the
historical agenda; implementation choices made during autonomous delivery are
recorded in [design §24](design.md#24-ms1-implementation-choices-not-new-user-agreements)
and the [README](../README.md). Those choices are not retroactively promoted to
new user agreements and remain open to hands-on feedback.

## Latest decisions

- First milestone: functionally equivalent to Notepad in editing; agree the exact
  checklist before treating particular features as commitments.
- Explore selection-first features incrementally, not by copying all of Helix.
- Normal-state ordinary movement cancels selection; it does not extend it.
- Insert-state arrows move the caret; Shift+arrows extend selection.
- Unit-based cursors (character/word/line) are an experiment to consider, not an
  adopted requirement.
- Escape: Insert → Normal, preserving selection; Normal cancels pending input
  first, otherwise collapses selection to its active end.
- Buffer-owned undo; ordinary character insertion is individually undoable.
- Normal-state `[` / `]` delimit repeat recording; brackets remain text in Insert.
- Building a recording preserves single-operation undo. Do not capture undo as
  a replay command; keep the recording consistent with corrected edits.
- `.` playback is one undo unit, including a partial replay that fails. Keep
  completed changes and explain the failure rather than automatically rollback.

## Latest MS1 interaction decisions

- British spelling throughout project-authored material.
- Ctrl+S returns to Normal consistently, including save failure. Preserve edits
  and show the error on failure. For an unnamed buffer, open the `:` prompt
  prefilled with `w `; cancelling leaves the editing view in Normal.
- No automatic indentation for MS1, including Enter and `o`/`O`. Indentation is
  a facet policy.
- Add a `:` prompt with `:q`, `:w`, `:wq`, and `:q!` for saving/quitting.
- Support coloured CLI errors and status-line errors; clear status errors on
  buffer content changes.
- Insert typing replaces selection; Normal letters invoke commands.
- `i` alone preserves selection on Insert entry; `a`, `A`, `I`, `o`, `O` clear it
  before repositioning.
- Cursor keys only for movement: do not plan `h`/`j`/`k`/`l` bindings.
- Tab inserts exactly four spaces by default, not spaces to a tab stop. Facets
  can hook into and redefine handling. A configuration system is wanted later.
- Backspace removes one Tab's inserted spaces as a unit at line beginning/end;
  exact boundaries and provenance rules still need clarification.
- Preserve existing tabs and all unedited file content. No silent rewrites.
- `I` goes to first non-whitespace; its behaviour can be changed later.
- Preserve LF/CRLF and final-newline presence; new files use LF. Never append a
  newline automatically.
- Backspace at line start and Delete at line end join lines; each join is one
  undoable operation.

## Continuation and fidelity updates

- Infer indentation width for existing files heuristically (details open), without
  rewriting content. Four spaces remains the default/fallback.
- Ordinary `:w`/Ctrl+S do not write unchanged existing files; `:ww` forces writing
  and `:w <filename>` writes regardless of modified state.
- Preserve individual mixed line endings; infer a default for inserted endings.
- Continuation stores unsaved/unnamed documents in the user's configuration area,
  restores layout/state, and is scoped by startup folder.
- Ordinary quit preserves unsaved work; `:q!` explicitly drops changes.

## Next: continuation contract

Settled: continuation is required for MS1; checkpoint during editing and on
quit; `:q!` discards unsaved changes in all current-workspace documents. Use
`~/.config/me` with hashed location keys; detailed layout remains proposed.

Also settled:

- Persistence failures remain indicated; normal quit refuses unsafe loss.
- External changes: flag conflict for edited buffers; reload unedited buffers.
- Restore then open/focus CLI paths; `me -r file.n` resets the workspace instead.
- Undo history survives restarts unless reset with `-r`.
- Latest correction: `:q!` removes all unsaved buffers entirely, including
  recovered work. Saved unchanged buffers/layout survive. Disk files are untouched.
- `:kill` refuses unsaved work; `:kill!` forces removal of the active buffer and
  all its views, with surviving-view/empty fallback. Kill is not text-undoable.
- No confirmation for reset; bare `me -r` opens an empty default workspace.

Remaining:

1. Settled: `:q!` removes every unsaved buffer, not just this invocation's edits.
   This supersedes startup/last-save rollback and recovered-work retention.
2. Confirm `:w!` forces both unchanged writes and conflict overwrite; `:ww` only
   forces an unchanged write, without conflict override. No `:ww!` needed.
3. Should failed file opening leave pre-reset recovery state intact? What history
   survives an external reload of an unedited buffer?
4. What checkpoint debounce and maximum loss window are acceptable?
5. What other view state survives, and what happens to transient prompts?
6. Settled: a second process is allowed, starts with a default workspace, and
   does not save snapshots, with a startup warning explaining this. In this
   non-persisting session, `:q` refuses unsaved changes; `:wq` saves and quits
   on success, and `:q!` explicitly abandons changes. Still define `-r` handling
   while another process owns continuation.
7. Settled: `:w`/Ctrl+S save the active document; `:wq` saves all modified
   documents and quits only if every required save succeeds. Unnamed documents
   need filenames; errors/cancellation leave ME open, retaining successful
   earlier writes. Filename-prompt sequencing remains open.
8. Settled: successful `:w <filename>` changes the backing path. Overwriting a
   different existing file requires `:w! <filename>`. Use same-directory
   temporary files and atomic replacement where supported, preserve permissions,
   and follow symbolic links rather than replacing them.

## Next: display and search details

- Settled: horizontal scrolling, initially experimenting with current-line-only
  scrolling; gutter line numbers, relative in Normal and `:` command states.
- No mouse in MS1; further keyboard navigation is to be discussed.
- `/` forward search, `?` backward search; `n`/`p` next/previous matches.
- Adopt `//` from document start and `??` from document end; escape literal
  leading delimiters with backslash.

1. Settled: `n` always forward, `p` always backward; literal case-sensitive
   search with wraparound and incremental preview of all visible matches.
   Enter commits at match start without selection. Escape restores pre-search
   caret/scroll and clears selection; arrows then move from that restored caret.
   Confirm/cancel hide highlights but retain the current term; `n`/`p` resume
   from the actual caret and bring visible-match highlights back.
2. Ordinary movement after `n`/`p` clears selection/highlights without rolling
   back the jump (settled). Should edits also hide passive highlights? Should
   Escape collapse selection and hide highlights at the new position?
3. Settled: `n`/`p` select the active match as an editing selection; other visible
   matches have a different highlight colour. Enter confirmation still removes
   selection. Empty prompt confirmation reuses the remembered term, or reports
   `No previous search`. Repeated `n`/`p` skip the active match (settled).
   `c` deletes selection as one undo operation and enters Insert; subsequent
   characters undo individually. Define `c` with no selection, selection
   direction, and literal-backslash parsing alongside escaped delimiters.
4. Absolute line numbers in Insert, and absolute current line amid relative
   numbers in Normal/command states?
5. When changing active lines, should the former line reset to horizontal offset
   zero? How should the new line reveal the caret?

## Next: selection units and typed paste

- Adopt experimental Normal bindings: `y` copy, `x` cut, `v` paste, `l` line,
  `w` whole word; `c` changes selection.
- Yank preserves selection; cut leaves caret at deletion point; characterwise
  paste replaces selection or inserts at caret, as one undo operation.
- `l` includes the line ending; `w` inside a word selects the whole word.
- Preserve characterwise/linewise clipboard metadata so `v` can distinguish them.

1. Linewise paste without selection inserts below the current line (settled).
   How should it behave with an existing characterwise/linewise selection?
2. Repeated `w`/`l` extend selection (settled); `<num>w` selects from the first
   word's beginning through the last word's end. Define count behaviour on
   existing selections and support for counts on other commands.
   `<num>l` is also supported. Ctrl+D duplicates below, moves to the duplicate
   at the same column and is one undo operation. Latest Ctrl-command policy
   supersedes state preservation: Ctrl+D enters Normal. Define selection handling.
3. Settled: letters/digits/underscores form words, punctuation forms separate
   selectable runs, and extension skips whitespace between units. Define starting
   on whitespace and exact Unicode classification.
4. How should final lines without newline be yanked/cut/pasted without silently
   changing file content?
5. MS1 uses an internal clipboard with characterwise/linewise metadata; system
   integration is deferred. Define no-selection behaviour and clipboard lifetime.
6. Ctrl+Z undo and Ctrl+R redo, both states, with no alternate bindings (settled).
   Navigation is independent of buffer history; invoking caret moves to the edit
   and selection clears (settled). Ctrl+Z/Ctrl+R enter Normal, even on a no-op.
   All Ctrl-bound non-navigation commands enter Normal; Ctrl navigation preserves
   state. Encode this distinction explicitly. Avoid redundant keybindings.

## Navigation baseline updates

- Adopt arrows, Ctrl+Left/Right word movement, smart Home (first non-whitespace,
  then column zero), End to line end, Ctrl+Home/End document edges,
  Page Up/Down visible-page movement, and Shift
  extension for caret navigation. Up/Down retain a preferred column.
- Ctrl+Page Up/Down navigate paragraphs; facets can redefine this, e.g. Nerd
  bindings. Ctrl+Up/Down scroll the view one line. These preserve interaction state.
- Default paragraphs are non-blank runs separated by blank/whitespace-only lines.
- Scroll-only navigation can leave the caret off-screen. Caret movement or text
  insertion reveals it again. Normal numeric-prefix entry and opening/typing in
  the `:` prompt do not snap back; executed navigation reveals its destination.
- Settled: Normal counts apply to arrows (`12` then Down moves 12 document
  lines); `:120` goes to absolute line 120; relative gutter numbers are measured
  from the actual caret line even when off-screen.
- Settled: clamp out-of-range movement; absolute line jumps use first
  non-whitespace. Vertical arrows retain a preferred column through short lines
  and recover it on longer lines, including counted movement.
- Escape cancels counts; commands consume them; unsupported count-command
  combinations report an error and clear them. Define zero/overflow parsing.
- Left/Right, Home/End, jumps, and editing reset preferred column to the resulting
  caret position. Preferred columns use display cells; choose the nearest valid
  text boundary inside a tab/wide character. Define tie-breaking.

## Text fidelity and live external changes

- UTF-8 editable loading with BOM preservation; refuse invalid UTF-8/unsupported
  encodings for now. Prompted conversion may come later.
- Character movement/deletion should use grapheme clusters. Investigate standard
  library support before implementation.
- Unedited buffers should show external changes promptly, not only on save/focus.
  Existing reload-versus-conflict policy stands; watching/polling is undecided.
- Settled: external reload is one undoable operation; undo restores prior content
  and makes it modified relative to disk. Preserve earlier history.
- Settled: external deletion retains visible buffer content, marks the file
  missing, and allows explicit save to recreate it.
- Settled: external reload preserves matching undo history. Reappearance reloads
  unedited buffers and flags conflicts for edited ones.
- Externally deleted documents follow new/unsaved continuation rules: normal
  quit preserves in-memory content, known path, and missing status without
  recreating the original file. `:q!` removes missing-file buffers entirely,
  regardless of recovery origin.
- Discuss detection latency, partial writes, and view-position mapping.

## Next: status and workspace messages

- Each pane has a status bar; commands/messages use a separate workspace bottom
  area. Multi-line messages expand it until dismissed, then it shrinks.
- Avoid the verbose `no continuation` persistent label; choose a compact marker.
- When shrinking view bounds forces a previously visible caret out of view,
  recentre affected views. Do not conflate this with deliberate scroll-away.

1. Settled: maximum message-area height is half the terminal; scroll longer
   output. Define message-scroll bindings and tiny-terminal handling.
2. Settled: automatic sizing is enough for MS1; manual resizing is deferred.
3. Settled: Escape dismisses messages without moving the caret or changing the
   selection. Ordinary editing clears transient messages; ongoing failures remain
   indicated. Define prompt precedence and message-scroll bindings.
4. Settled: preserve intentional scroll-away on resize; recentre only when the
   resize itself forces a previously visible caret out of view.
5. Settled direction: Normal cursor/status green, Insert red, with clearer UTF-8
   status presentation. Current glyphs/palette are implementation choices;
   textual labels and compact warning markers remain visible.

## Buffer contracts and tracked positions

- Buffer interactions use traits and `impl` blocks; no compile-time backend
  substitution framework. Change implementations later by refactoring behind the
  contracts.
- Settled: views own/adjust positions; buffers report concrete edits. Other
  consumers own their tracked ranges; adjustment logic can be shared.
- Prefer declarative, position-explicit edits. No caller-visible gap movement or
  storage cursor. Navigation/reads never reposition a gap. Mutations may move
  it when necessary; deletion may move it to the range start and expand over
  the deleted text. Insertion-only wording is superseded.
- Settled: logical UTF-8 byte offsets represent document positions, excluding
  the gap; they are independent of physical storage indices. Buffer queries
  resolve line/column and grapheme boundaries; views map display cells. Character
  operations remain grapheme-based. Define valid-boundary enforcement.
- Settled: insertion at another view's caret leaves it before inserted text;
  the editing view advances its own caret. Deletion containing another caret
  collapses it to range start. Non-empty selections exclude insertions at either
  outer boundary and include insertions strictly inside; full deletion collapses
  to the deletion point. Apply to ordered bounds, preserving selection direction.
  Empty selections use caret affinity. Exact whole-selection replacement by
  another view selects the replacement text (settled); pure deletion collapses.
  Define partial-overlap replacement semantics.
- Decide exact trait boundaries only after inspecting Nerd's trait facilities.

## Remaining first-milestone scope and selection details

1. Agree CLI behaviour: no argument, nonexistent file path, one versus multiple
   paths, and any initial-position arguments. MS1 opens files via the command
   line, not an interactive file picker; panes are not an MS1 requirement.
2. Agree the Notepad-equivalent checklist: file operations, navigation, selection,
   clipboard, search/replace, undo/redo, and any exclusions. Startup is Insert
   only for an empty buffer, Normal otherwise. Explicit repeat waits until a
   later milestone.
3. Confirm additional Insert-entry positioning for `a`, `A`, `I`, `o`, `O`.
   `I` is settled as first non-whitespace, overridable later. Selection clearing
   is settled for all except `i`, which preserves it.
   When Left/Right cancels selection, collapse to that edge or move one character
   from the active end? What should Up/Down do?
4. Does word selection select the entire containing word or from the caret to its
   end? How should whitespace/punctuation and repeated selection behave?
5. Clipboard expectations: desktop clipboard, internal clipboard, terminal/SSH,
   keyboard copy/paste, and mouse selection?

## Later discussion topics

- Undo cursor restoration and compound-operation boundaries (paste, replacement,
  automatic pairing/indentation).
- Recording corrections, redo, pre-recording undo, replay's final state/selection,
  failure messages, command scope, and repeat storage scope.
- Exact keybindings and interaction states; pending-input display.
- Buffer capabilities, view-kind compatibility, and facet composition contracts.
- Text representation, indexes, revisions, anchors, and memory ownership.
- Anchor affinity on insertion and behaviour when referenced content is deleted.
- Unicode and display mapping, wrapping, folds, concealed text, virtual rows.
- Popup focus/input policies, sizing, placement, and file-navigation workflow.
- Pane/view/buffer lifetime and unsaved-work handling.
- Safe saving, recovery, external changes, and filesystem errors.
- Nerd services: highlighting, indentation, LSP, builds, diagnostics.
- Background work and cancellation without blocking editing.
- Supported platforms/terminals, startup and latency measurements.
- Standard Nerd scaffold, `just` recipes, tests, and first milestone.


## Unconfirmed toolchain follow-up

During the undo-caret work, one full `just test` invocation terminated with
SIGSEGV after the codec suite. The following editor-BOM test passed in isolation,
and a complete rerun passed all 22 project tests. No minimal reproducer or cause
is established; retain `_tmp/undo-core-initial.log` for investigation if it recurs.


## Next: file opening, completion and MS2

Agreed: `:e <path>` with filename Tab completion. The broader MS2 popup/buffer
switcher, file picker, splits and explicit repeat tasks are also accepted; see
`docs/tasks.md`. Their detailed interactions are not automatically settled.

Before T2, choose whether Tab extends the common prefix, cycles matches or opens
a list. The suggested folder-candidate popup remains optional: should it appear
while typing a folder prefix, or only when Tab finds multiple matches? Settle
directory navigation, accept/cancel, no-match, hidden files and byte-safe prompt
presentation before implementation. If a popup is selected, reuse shared picker
infrastructure rather than a disconnected one-off widget.
