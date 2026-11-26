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
- Cursor keys remain available; the later agreed Normal `h`/`j`/`k`/`l`
  bindings add left/down/up/right movement with counts. These are literal in
  Insert/prompts; `q` replaces `l` for line selection.
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
- Plain CLI filenames now erase continuation and open only the requested files:
  `me file1 file2` has two distinct buffers, no extra unnamed one, showing file1.
  Erase after taking the lock and before opens, even if they all fail. `-r` also
  erases; second instances cannot touch the owner's snapshot. Erase failure is fatal.
- Bare `me` restores. Explicit `me +file1 +file2` restores then adds/reuses files,
  preserving other buffers/history/view state and showing the first successful
  path. Continue after open failures; keep restored buffers or exit 2 if none.
  Reject mixed plain/+ and `-r`/+ modes before touching snapshots; bare `+` errors.
  `./+name` is a literal fresh path; `++name` adds a literal leading-plus path.
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
- Keep `//` from document start and `??` from document end. The user clarified
  that origin prefixes are not ambiguous: parse them before replacement fields.
  `/old/new` and `//old/new` replace all; optional `/c` confirms with Y/N/A/Escape.
  Escape literal forward-query slashes. `:replace` and `g` are removed.

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

- Adopt experimental Normal bindings: `y` copy, `x` cut, `v` paste, `q` line,
  `w` whole word; `c` changes selection.
- Yank preserves selection; cut leaves caret at deletion point; characterwise
  paste replaces selection or inserts at caret, as one undo operation.
- `q` includes the line ending; `w` inside a word selects the whole word.
- Preserve characterwise/linewise clipboard metadata so `v` can distinguish them.

1. Linewise paste without selection inserts below the current line (settled).
   How should it behave with an existing characterwise/linewise selection?
2. Repeated `w`/`q` extend selection (settled); `<num>w` selects from the first
   word's beginning through the last word's end. Define count behaviour on
   existing selections and support for counts on other commands.
   `<num>q` is also supported. Ctrl+D duplicates below, moves to the duplicate
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
- Ctrl+H/L mirror Ctrl+Left/Right word movement; Ctrl+J/K mirror Ctrl+Down/Up
  scroll-only movement. Enhanced reports distinguish these aliases from legacy
  Backspace/Enter bytes. Counts, Shift and interaction-state preservation follow
  the existing arrow paths; paired text and release events must not act twice.
- Default paragraphs are non-blank runs separated by blank/whitespace-only lines.
- Scroll-only navigation can leave the caret off-screen. Caret movement or text
  insertion reveals it again. Normal numeric-prefix entry and opening/typing in
  the `:` prompt do not snap back; executed navigation reveals its destination.
- Settled: Normal counts apply to arrows and HJKL (`12` then Down or `12j`
  moves 12 document lines); `:120` goes to absolute line 120; relative gutter numbers are measured
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

1. CLI no-argument/nonexistent-path policies are settled above. Multiple paths
   are now agreed and implemented: separate buffers, first successful path
   displayed. Initial-position arguments remain unimplemented. MS1 opens files
   via the command line, not an interactive file picker; panes are not required.
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
- Broader repeat scopes and named macros. T6's first implementation policies for
  corrections, redo, state/selection, failure messages and session storage are
  documented in design §32.
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


## Toolchain crash investigation

A later native-suite crash during the search-origin correction was reproduced
under GDB and AddressSanitizer: generic-method inference reallocated the local
binding table while inference retained a pointer into the old allocation. Nerd
`98883071` retains indices and reacquires rows across recursive inference, with a
local-table-growth regression. Its full gate passed (72 passed, 2 platform skips),
and the complete ME suite passed with the fixed compiler. This explains the new
crash; the earlier intermittent undo-caret crash may have shared this cause, but
that historical run has no diagnostic proof. Logs remain under `_tmp/`.

The fix is retained on local Nerd `main` and its pushed agent branch. Direct
`~/nerd just install` succeeded from the unchanged `remove-linux-libc` checkout
`174a4576` at that stage. Matt later authorised merging validated ME fixes into
that branch; integration `c80d7775` passed the combined gate and is installed
from `~/nerd` on `remove-linux-libc`. Ordinary ME builds use installed Nerd.


## Buffer popup and safe close — settled

- Normal `,` opens a large popup with a top fuzzy query bar. Matching is
  case-insensitive subsequence matching in typed-letter order, using Unicode 16
  default full case folding. This model/layout/renderer is reusable for later lists.
- Buffers stay in MRU order: current first, previous second, with the second row
  initially selected (first for a lone buffer). Enter immediately chooses;
  Escape cancels without switching. Empty results remain open; Enter is a no-op.
- Arrow/page keys move the selection; query editing supports grapheme deletion
  and caret navigation. The query is bounded at 4,096 bytes, not persisted.
- MRU order persists in continuation v3, importing v1/v2 safely. Legacy snapshots
  seed active-first then document order because no prior access order was stored.
- Ctrl+W closes the highlighted picker candidate, otherwise the active saved
  buffer. No matches means no action. Closing another buffer preserves focus.
  Keep the picker open after closing or refusing unsaved work. Retain query/caret
  and the same result row, clamped to the last survivor; no matches stays open.
  No implicit write/discard; closing the active buffer focuses the previous survivor
  or creates a fresh empty one.
  Ctrl+W enters Normal, including failure; literal comma remains in Insert/prompts.
- Right-hand preview follows the highlighted buffer's live unsaved text without
  switching it or changing caret/selection/history/MRU. Display from the top,
  clipped by visible rows/grapheme widths with expanded tabs and safe controls.
  Empty selection clears preview; narrow/short screens hide it in favour of the
  full-width list. Preview is read-only and performs no disk access.
- Asynchronous file discovery, an overlay stack and split routing are later work.

## Enhanced key releases

The reported press/release cursor duplication was reproduced as a Nerd parser
bug: traditional CSI cursor/Home/End/tilde keys lost their action subparameter,
while CSI-u retained it. Decode press/repeat/release uniformly in Nerd. Ordinary
ME handlers ignore decoded releases, including Alt+Page scrolling; diagnostic
capture keeps them visible. Repeats remain intentional navigation events.

## Home-relative paths

The reported `:e ~/.wezterm.lua` and `:e ~/.we<Tab>` failures supersede the original
no-tilde-expansion policy. Leading `~`/`~/` now uses HOME for open/save/completion;
completed paths retain `~/`, with bare `~` Tab adding `/` first. The rest stays
literal: no shell quoting, variables or named-user lookup. `./~` addresses a
literal cwd tilde entry. Missing/non-absolute HOME errors safely; Linux retains
responsibility for symlink and dot-segment resolution.

## Keyboard diagnostics and protocol detection

`:keys` was accepted for inspecting decoded keys and actual terminal capabilities.
Nerd `7cd7e0ec` supplies raw optional Kitty flags and query completion, fixes partial
flag overclaims, and consumes private CSI/DA replies without text leakage. The
view captures without editing/saving; Escape closes and Alt+Page Up/Down scroll.
Legacy `0x08` remains ambiguous; no supported protocol can reverse terminal-level
key remapping. No response is pending, not a timeout-based unsupported verdict.
The audit does not claim raw byte capture, every terminal-specific protocol, or
resolution of the separate Escape-timeout/bracketed-paste gaps.

## Next: file opening, completion and MS2

Agreed: `:e <path>` with filename Tab completion. The broader MS2 popup/buffer
switcher, file picker, splits and explicit repeat tasks are also accepted; see
`docs/tasks.md`. Their detailed interactions are not automatically settled.

T2 interaction settled: Tab completes unique matches/expands common prefixes,
appends directory slashes, and displays ambiguous matches in the existing message
area. Up/Down or Tab selects, Enter accepts without executing, Escape closes the
list while retaining the path. Another Enter executes. No automatically opened
folder popup. The user further agreed command-name completion, bottom-anchored
command entry and keeping an open list filtering while typing/deleting; one or
zero matches do not dismiss it. Same-directory filtering reuses a snapshot.
Current completion choices are documented in `docs/tasks.md`; the broader MS2
picker's roots, matching, discovery and popup contracts remain separate decisions.


## File picker delivery defaults

T4 uses the startup folder and the existing Unicode subsequence matcher. Matt
agreed to include hidden and ignored files, follow file and directory symlinks
with cycle detection, and introduce a Normal-state Space leader. Space Space
opens files; after one second the first Space shows known keys. `:files` is
also available. Other roots, indexing, file previews and an overlay stack remain separate choices.
The split destination is settled under T5 below. See design §26 and README for details.


## Space menu overlay — settled

- Replace the message-area hint with a bottom overlay, sliding upwards after
  the one-second delay. Improve spacing, border, key labels and headings.
- Preserve the underlying view geometry and messages; cancellation restores them.
- Prepare grouped sequences with menu path headings and parent navigation.
- Space b d was explicitly clarified as an example only. Do not add it, or other
  submenu actions, without agreement. T5 below adds the agreed Windows actions.
- The implementation uses a 180 ms row animation; see design §27 for details.


## Pane controls and picker destination — settled (T5)

Matt agreed to the Windows submenu and root directional focus controls in
design §28: Space w h/v/s split side by side, above/below or automatically;
Space w c closes a pane; Space w w picks a file before automatic splitting.
Space h/j/k/l and Space plus cursor keys focus neighbouring panes.

Splits focus a new independent view of the current shared buffer. Automatic
orientation accounts for terminal cell proportions. Focus does not wrap at an
edge. Closing preserves buffers and keeps the final pane open. File-picker
cancellation/failure preserves the layout; only a successful selection/open
creates and focuses its new pane. Delivered under T5; design §28 records the
initial sizing, minimum dimensions, neighbour ties and resize policies as
implementation choices.


## Pane follow-up corrections (T5a)

Matt clarified that h means a horizontal arrangement (side by side) and v means a
vertical arrangement (above/below), correcting the original T5 mapping. Brighten
the focused pane background to distinguish it, and fix terminal input reports
leaking into the shell on exit. These are agreed fixes, not proposed controls.


## Ctrl+W pane closing (T5b)

The reported pane-closing bug is resolved by using the existing pane-close action
for ordinary Ctrl+W. Buffers remain available, including unsaved work; other panes
retain their contents and navigation. The last pane stays open. Buffer-picker
Ctrl+W still removes its highlighted saved buffer; explicit :kill[!] is unchanged.


## Repeat recording first scope (T6)

Matt accepted current-buffer editing/navigation with one recording per session.
The initial implementation captures relative semantic commands and their mode/
selection effects; undo/redo correct the recipe, while each playback is one undo/
redo unit. File/pane/buffer actions are refused until recording finishes. Design
§32 records the delivery policies and bounds; broader scopes and named macros
remain separate work.


## Pending d and line deletion (T8)

Settled: d immediately deletes an existing selection; without a selection it
waits for a second d. dd deletes a line, and a prefix such as 3dd deletes three.
Design §34 records cancellation, line endings, clipboard and count policies.

## Future file-type modes: first milestone foundation and Markdown

Matt explicitly requested modes that determine LSP, formatting, syntax
highlighting, indentation and related behaviour, with file-type customisation.
The first future modes milestone covers the foundation and Markdown support,
including status LF/CRLF and recognised file type. See design §35.

Open before implementation: recognition and override precedence; customisation
format/storage; mode and facet ownership; provider/service lifecycle and concrete
LSP/formatter/highlighter choices; the initial Markdown feature checklist; status
representation for mixed/no line endings and unknown file types. Further modes
milestones remain unscoped.


## Recording follow-ups — agreed

Ctrl+G cancels the unfinished recording in Normal or Insert, keeping edits,
interaction state and the previous macro. Quitting also cancels the draft.
Finishing an empty draft (`[]`) clears the previous macro.

Still to deliver: persist completed macros across restart, and include `:` commands
in playback. Quit commands execute once and cancel the draft, preserving the
previous completed macro; they must never become playback actions.
