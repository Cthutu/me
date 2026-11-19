# ME design

This document records the initial design discussion. **Agreed** items reflect
explicit agreement in that discussion. **Proposed** items are recommendations
still subject to discussion. Examples illustrate possibilities, not promised
first-release scope.

## 1. Identity and goals — agreed

- Name: **ME**, or **Matt's Editor**.
- A text-based terminal editor, implemented in **Nerd**.
- Primarily for developing Nerd programs, but not restricted to Nerd source.
- Use the standard library for terminal interaction, specifically `std.term`.
- Use a standard Nerd development environment supported by `just` recipes.
- Discuss the design thoroughly before implementing the editor.
- Modal interaction, but not a requirement to reproduce Vim.
- Start with selected Vim-inspired editing commands, not Vim compatibility.
  Movement uses cursor keys only; do not plan `h`/`j`/`k`/`l` movement bindings.
- Fast startup and responsive editing are architectural priorities.
- Support panes, independent views, shared buffers, transformed presentation, and
  popups, including global file-navigation popups.

## 2. Architectural principles — agreed

1. Buffers, views, panes, commands, and keybindings are separate concepts.
2. A keyboard state machine interprets input and emits command invocations.
3. Views determine interaction, commands, keybindings, and presentation.
4. Panes are layout devices, not document or interaction owners.
5. Buffers hold content and can represent more than text files.
6. Multiple independent views can reference the same buffer.
7. Commands have explicit targets: a view or the workspace.
8. Keyboard parsing does not calculate document byte ranges; views resolve
   semantic editing requests against their content and state.
9. Keep editing logic testable without a live terminal.

## 3. Terminology — agreed

- **Buffer:** shared underlying content.
- **View:** an interaction and presentation of a buffer.
- **Pane:** a layout surface within the workspace's split layout.
- **Popup:** a temporary surface above the pane layout, mounting a view.
- **Interaction state:** modal keyboard behaviour, such as Normal, Insert,
  Select, or an operator-pending substate.
- **Facet:** a composable specialisation of a view, analogous in purpose to
  Emacs modes, without overloading the term "mode".
- **Workspace:** manages buffers, views, surfaces, focus, and shared services.

Distinguish a buffer's content kind, a view's fundamental interaction kind, and
facets that specialise that view. A popup is not a facet or a buffer kind.

## 4. Entity model — agreed

```text
Workspace
  ├── Buffers
  ├── Views → reference buffers
  ├── Pane layout tree
  │     └── Panes → mounted views
  └── Overlay stack
        └── Popups → mounted views
```

These are independently managed entities, not a chain of exclusive ownership.

### Buffers

A text buffer owns text, revisions, concrete edits, shared undo history, optional
file association, and saved/modified state. Other buffer kinds can have different
content-specific operations and history policies.

Possible non-text buffers include structured diagnostics, directory entries,
repository status, image data, and debugger state. Do not force all content into
text or require an oversized universal buffer interface.

### Views

A view references a buffer and owns interaction and presentation state:

- Cursor, selections, navigation, and scrolling where applicable.
- Interaction state and keyboard-machine context.
- Active facets and effective keybindings.
- Folding, wrapping, filters, grouping, and other presentation choices.
- Rendering and translation between buffer and displayed positions.

Two views of one text buffer have independent cursors and scrolling but share
content and modification history.

Examples of view kinds: text editing, image inspection, navigable lists, and diff
comparison. Compatibility between views, facets, and buffers should be explicit.

### Panes and lifetime

Panes receive layout rectangles and mount views. They do not implement editing.
Changing a split should not reconstruct a view. Closing a pane need not destroy
its view; destroying a view need not discard its buffer. Exact retention and
closing policies remain to be specified.

Initial agreed direction: one active view per pane and a view mounted in at most
one surface at a time. Displaying one buffer in two places creates two views.

Use a split tree initially: leaves are panes; internal nodes describe horizontal
or vertical splits and proportions. A general docking system is not required.

## 5. Input and commands — agreed architecture

```text
std.term event
  → normalised key/text event
  → focused surface's view input context
  → keyboard state machine
  → command invocation
  → explicit view/workspace target
  → content operation or workspace operation
```

The keyboard machinery is reusable infrastructure; its active state belongs to
the view/input context. Views can retain different interaction states.

The state machine can represent counts, partial key sequences, pending operators,
cancellation, and eventually register prefixes or ambiguous-sequence timeouts.
These are possible capabilities, not all required for the first milestone.

Separate:

1. Input grammar: operators, motions, counts, prefixes, cancellation.
2. Bindings: keys mapped to grammar actions or direct commands.
3. Context: view kind, interaction state, active facets, temporary input context.

Illustrative initial bindings:

| Input | Semantic command |
| --- | --- |
| Left arrow | Move left, cancelling selection |
| Down arrow | Move down, cancelling selection |
| `dw` | Delete using forward-word motion |
| `i` | Enter Insert state |
| Character input in Insert | Insert text |

For `dw`, the keyboard system emits a semantic delete-plus-motion invocation.
The text view resolves cursor/selection/word behaviour into a concrete range;
the buffer applies an edit transaction. The parser does not know byte offsets.

Vertical navigation can mean displayed-row movement in text, selection movement
in a list, or panning in an image. Reuse genuine common intents without forcing
all views into an excessively abstract universal command vocabulary.

Workspace commands include splitting/focusing panes, opening files, closing
views, and quitting. Unsupported view commands must fail safely. Prefer explicit
scope to broadcasting until a handler accepts a command.

### Policies still proposed

- Cancel incomplete sequences/counts when focus changes, but preserve persistent
  interaction state.
- Deterministic keymap precedence, initially considering temporary input context,
  view-local bindings, facet bindings, view-kind defaults, workspace defaults.
- Make conflicts inspectable and support explicit unbinding.
- Resolve effective keymaps when context changes, not on every keypress.

The command schema, motion semantics, routing details, and transaction API are
not yet designed.

## 6. Facets — agreed direction

Facets can add substantial behaviour, not merely syntax colours:

- Commands and keybindings.
- Rendering decorations and transformed presentation.
- Indentation and language behaviour.
- Lifecycle participation and language-service integration.

Examples: Nerd development, Org-like outlining, Git status, whitespace display,
search highlighting, and read-only behaviour.

Keep access and responsibilities bounded; do not replace explicit subsystem
contracts with unrestricted callbacks.

Facets declare required capabilities. A Nerd facet needs text capabilities;
other facets may need structured repository content or image data.

Shared content-derived work belongs outside individual view instances where
appropriate. Two views of one Nerd buffer should not create duplicate language
servers or independent copies of document analysis. A view facet can expose a
shared language service.

### Org-like example

A text buffer stores source; a text view with an outlining facet adds heading
navigation, folding, task operations, and concealed/rendered markup. Fold state
is view-local. Parsed outline structure can be shared and cached by revision.

### Git-interface example

A structured repository-status buffer feeds a list view with Git actions. Stage,
unstage, refresh, and similar commands request service operations rather than
pretending to be ordinary text edits. Results update the shared buffer. Diffs can
use specialised views. An interface can use multiple cooperating buffers/views.

These examples establish architectural capability, not initial implementation
commitments.

## 7. Transformed presentation — agreed

Views may:

- Fold content.
- Conceal or visually replace source markup.
- Insert virtual rows.
- Show non-editable annotations.
- Present structured content without treating it as file text.

Maintain a view-owned mapping between buffer positions and displayed positions.
Cursor placement, mouse hit-testing, navigation, and popup anchoring must use
that mapping. Do not assume a document line equals a screen row.

Text coordinates must distinguish byte offsets, logical positions, and terminal
cell columns. Tabs, wide Unicode characters, combining characters, and LSP
position encodings need explicit treatment. Initial Unicode guarantees remain
open; avoid baking byte-equals-character assumptions into public contracts.

Shared edits require anchors or an equivalent tracked-position model so cursors,
selections, bookmarks, and diagnostic ranges remain meaningful across changes.
Anchor behaviour and text storage representation remain undecided.

## 8. Popups — required and proposed design

**Required:** support popups, including global overlays across panes for file
navigation. Popups should participate in the same decoupled view architecture.

**Proposed detailed model:** a popup is another surface mounting a view, with
placement, preferred dimensions, anchor, input-capture policy, dismissal policy,
and overlay-stack order.

### Placement scopes

- Workspace-relative: file picker, command palette, buffer switcher, workspace
  search, confirmation.
- View-anchored: completion, hover, signature help, contextual actions.

Anchoring is separate from clipping. A cursor-anchored popup may extend beyond
its source pane but must fit within the terminal. Start with preferred placement,
flipping when needed, and constraining to available space.

### Input and focus proposals

- Capturing popups take input, e.g. a file picker.
- Non-capturing popups show information without stealing focus.
- Cooperative popups, such as completion, work with the owning text view.
- Rendering order and keyboard focus are related but not identical.
- Closing restores the previous valid focus target and preserves underlying
  view state; partial input sequences must not leak between contexts.
- Escape is interpreted by the active context, not an unconditional global
  dismiss action.
- Support a small overlay stack, including confirmation above a picker.

### Global file navigation

A service discovers candidates, a structured picker buffer holds results, and a
picker view manages query interaction, selection, scrolling, and commands. The
global popup supplies placement, not filesystem behaviour.

Capture the originating pane or explicit destination before transferring focus.
Accepting a path opens/reuses a buffer, creates/selects a view, mounts it in the
destination, dismisses the picker, and restores focus. Validate destination IDs
if entities may have disappeared. Future commands can open in a new split.

Show the picker promptly; discover/filter results without blocking input;
ignore stale query results and cancel outstanding work on dismissal. Begin with
simple directory navigation if appropriate; indexing and fuzzy matching can
come later.

## 9. Performance — agreed goals, proposed mechanisms

Fast startup and editing are requirements. Proposed constraints:

- Draw the first useful frame without waiting for LSP or project-wide scanning.
- Start services lazily.
- Keep expensive analysis/subprocess work out of terminal input callbacks.
- Use one main input/presentation loop, including popups.
- Render visible content and update affected indexes/caches incrementally.
- Use `std.term` dirty-cell presentation; do not build another terminal renderer.
- Prefer stable IDs, typed arguments, compact command IDs, reusable scratch
  storage, revision-based caches, and explicit lifetimes.
- Decoupling must not imply per-keypress heap allocation or string dispatch.
- Measure startup-to-first-frame, input-to-present latency, and representative
  editing workloads before setting quantitative budgets.

A threading/asynchronous-service model has not yet been selected.

## 10. Nerd foundation — initial research

This section records the initial investigation. Current implementation and
verification are tracked in [ms1-progress.md](ms1-progress.md).

Research references in the local `~/nerd` checkout:

- `docs/stdlib-term.md`
- `docs/idiomatic-nerd.md`
- `docs/learn/23-Building-and-Configuring-Programs.md`
- `docs/lsp.md`
- `README.md`, `Justfile`, and `mods/std/term/term.n`

Documented `std.term` facilities include raw input, alternate-screen management,
ordered key/Unicode/mouse events, enhanced keyboard reporting with fallback,
input/presentation hooks, terminal dimensions, clipped framebuffer drawing, and
dirty-cell presentation. Normal loop exit restores terminal state; abnormal exit
behaviour still needs verification.

Nerd has an existing `nerd lsp` server. Prefer an eventual LSP client/service to
embedding compiler internals. Potential features include diagnostics, completion,
navigation, semantic tokens, and code actions. Initial integration scope is open.

Still investigate paste boundaries, clipboard support, Unicode/grapheme editing,
subprocess communication, resizing, and failure recovery before promising exact
behaviour.

## 11. Project environment

**Agreed:** standard Nerd project with `just` recipes.

**Proposed recipes:**

| Recipe | Purpose |
| --- | --- |
| `just build` | Debug executable under `_bin/` |
| `just run [args…]` | Build/run ME |
| `just release` | Optimised executable |
| `just check` | Compiler checking without linking |
| `just test` | Headless core tests |
| `just format` | Nerd source formatting |
| `just clean` | Remove this project's generated outputs |

Use installed `nerd` by default and allow explicit compiler/library overrides for
working against a checkout. Do not require a hard-coded `~/nerd` absolute path.
Follow Nerd idioms and underscore-prefixed generated output directories.

`nerd init` offers a standard scaffold, including `main.n`, `Justfile`, VS Code
configuration, `.gitignore`, and an initial Git commit. Decide how to use/adapt it
before running it. No scaffold, repository, or initial commit has been created.

## 12. Editing experiments, undo, and repeat — agreed

### Selection-first exploration

Explore selection-first editing incrementally in a working playground rather
than adopting Helix wholesale or fixing the entire keymap in advance. Try one
feature at a time; experimental bindings are welcome and can change in response
to hands-on feedback. The user does not currently recall specific Helix choices
to avoid, so do not invent a list of objections.

Latest clarification supersedes the earlier statement that cursor movement
always enlarges selections:

- In Normal state, ordinary cursor movement cancels the selection. Normal-state
  movement does not extend it automatically.
- In Insert state, ordinary arrows move the caret; Shift+arrows extend selection.
- Explicit selection commands can choose units such as words. Exact behaviour
  of `w` when starting inside a word remains to be explored.
- Character-, word-, or line-based cursor types were raised as a possible
  experiment, not adopted as an architectural requirement.

Use an anchor and active end to represent directional selections (proposed).
Exact cancellation destination and Normal-state explicit extension bindings
remain open.

Escape behaviour is agreed: in Insert, return to Normal without discarding the
selection; in Normal with pending input, cancel that input first; otherwise,
collapse a selection to its active end.

### Fine-grained buffer undo

Undo history belongs to the buffer, shared across views. Ordinary editing uses
one undo unit per operation: inserting a character is an operation. Do not
implicitly coalesce typing into words, pauses, paragraphs, or Insert sessions.
A semantic action may contain multiple low-level mutations; paste, selection
replacement, automatic paired edits, and indentation boundaries still need
explicit confirmation.

Undo can reverse the latest buffer change regardless of its originating view.
Exact cursor restoration policy remains open; agreeing on buffer ownership did
not separately settle restoration in every view.

### Explicit repeat recording

- In Normal state, `[` begins recording and `]` ends recording.
- In Insert state, brackets remain literal text. Leaving Insert before ending
  recording is acceptable.
- Recorded actions execute normally while the sequence is being built.
- During recording, undo remains single-operation, not sequence-sized.
- `.` replays the completed sequence.
- **One replay is one undo unit:** undo reverses the entire execution of the
  sequence, not one internal operation at a time. Redo should preserve that
  grouping (proposed).

This explicitly supersedes the earlier proposal to preserve individual undo
boundaries during replay. The same commands can execute as separate history
entries during recording and as a compound history entry during replay.

Proposed mechanism: record semantic command invocations rather than physical
keys or absolute document offsets, and execute playback inside an explicit
buffer history group. That group does not imply UI/input state is buffer-owned.

Do not record undo commands for playback. The agreed direction is for undo
while recording to remove the undone operation from the captured sequence, so
playback reproduces the corrected edit rather than an intermediate mistake plus
an undo. Exact mechanics, particularly redo and edits predating recording, still
need definition.

If replay fails partway, keep the partial result as a single undoable group and
report why/where it stopped. Do not automatically roll back its completed edits.
This supersedes the proposed rollback policy.

Still decide: capture of interaction-state transitions; replay's final
selection/state; supported command scopes; nested recording; repeat storage
scope; and whether `.` also supports an implicit last-change sequence.

## 13. First milestone — agreed direction

The first milestone should be **functionally equivalent to Notepad in editing**.
Establish familiar, reliable text editing before implementing the broader modal,
facet, structured-buffer, pane, and popup ambitions. Preserve the architectural
boundaries, but do not treat every long-term feature as a milestone-one promise.

The exact Notepad-equivalent checklist still needs agreement: ordinary typing,
caret movement, selection, replacement/deletion, clipboard operations, undo/redo,
file opening/saving, search, and related details are candidate scope, not yet an
approved feature list. Terminal clipboard support must be investigated.

No decision has been made to abandon modal interaction or selection-first
experiments; they should be introduced incrementally on a solid editing base.
### Startup interaction state — agreed

Start in Insert state only when the initial buffer is empty; start in Normal
state for a non-empty file. Empty means no content, not merely whitespace.
The exact no-argument and nonexistent-path CLI policies remain to be agreed.

### MS1 entry and deferred features — agreed

For MS1, deal with command-line support for opening files rather than building
interactive file-navigation popups. Panes and global file pickers are not MS1
requirements; retain the long-term design without implementing them now.
Exact CLI arguments, save/save-as interaction, and no-file startup behaviour
still need specification. This does not mean the editor itself is non-interactive.

Explicit repeat recording (`[` / `]`) and playback (`.`) can wait for a later
milestone. Their agreed semantics remain part of the long-term design.

## 14. MS1 interaction, commands, and errors — agreed

### Language convention

Use **British spelling everywhere** in project-authored code identifiers,
comments, documentation, UI text, and diagnostics wherever applicable. Preserve
external API names, protocol identifiers, and literal compatibility requirements.

### Saving and command prompt

- Ctrl+S consistently returns the editing view to Normal state, whether saving
  succeeds or fails. On failure, retain all edits and show the status-line error.
- On an unnamed buffer, Ctrl+S transitions the view to Normal and opens the `:`
  prompt prefilled with `w `, ready for a filename. Cancelling the prompt leaves
  the view in Normal. Do not introduce a separate save dialogue.
- `:` opens a command-line prompt.
- Support `:q`, `:w`, `:wq`, and `:q!` (the user's `q!` denotes the command entered
  at the `:` prompt).
- These commands provide the save/discard/cancel workflow rather than requiring
  a separate Save/Discard/Cancel dialogue.
- With continuation (see section 15), ordinary quitting preserves unsaved work
  for restoration rather than requiring a save/discard prompt. `:q!` remains an
  explicit way to remove every unsaved buffer, including recovered work.
- `:w` and Ctrl+S save the active document.
- `:wq` saves all modified documents, then quits only if every required save
  succeeds. Obtain filenames for unnamed documents; cancellation or any save
  failure leaves ME open. Successful writes before a failure remain saved:
  multi-file saving is not atomic. Each successful save updates that document's
  known disk content; later unsaved work is discarded by removing the buffer.
- `:w` and Ctrl+S perform no filesystem write for an unchanged existing buffer.
  Ctrl+S still returns the view to Normal; its save action alone is a no-op.
- Add `:ww` to force writing even when unchanged, without bypassing external
  conflict protection.
- `:w!` explicitly forces a write, including an unchanged buffer, and authorises
  overwriting an external-change conflict. A separate `:ww!` is unnecessary
  (recommended interpretation, awaiting confirmation).
- `:w <filename>` writes regardless of the current buffer's modified state.
  On success, that path becomes the document's backing file; future Ctrl+S uses
  it. Failed writes must not reassign the document's backing path.
- Refuse to overwrite a different existing destination unless explicitly forced
  with `:w! <filename>`.
- A new buffer without an existing backing file still needs a first write even
  if empty.
- Safe writes: write a temporary file in the destination directory, then
  atomically replace the destination where supported, preserving permissions.
  Follow symbolic links and save their targets rather than replacing the links.
  Exact race handling, durability, hard-link behaviour, and metadata guarantees
  remain implementation details to investigate.
- Command cancellation, filename parsing, and remaining argument syntax still
  need specification.

### Errors

- Provide errors rather than silently failing.
- Command-line error output supports ANSI colour escape sequences (referred to
  as colour ASCII codes in discussion).
- Provide an error message in the editor status line.
- Clear/reset the status-line error when buffer content changes. Cursor movement
  is not itself a content change.
- Exact colour auto-detection, redirected-output behaviour, and whether status
  errors are view-, buffer-, or workspace-scoped remain open.
- Render interactive errors using `std.term` styling rather than writing raw
  escape sequences into framebuffer text (proposed implementation).

### Insert-state entry and selection

- In Insert state, typing replaces an existing selection.
- In Normal state, letters invoke commands rather than inserting text.
- `i` enters Insert and preserves an existing selection, allowing the next typed
  character to replace it.
- Also support `a`, `A`, `I`, `o`, and `O` as Insert-entry commands.
- Only `i` preserves selection for now, because it does not reposition the
  cursor. `a`, `A`, `I`, `o`, and `O` clear selection before repositioning.
- Proposed Vim-inspired meanings: `a` inserts after the caret; `A` at line end;
  `I` at first non-whitespace (confirmed, with behaviour overridable later);
  `o` opens a line below; `O` opens a line above.
  Exact remaining caret-boundary semantics and undo boundaries still need
  agreement.
- Use cursor keys for movement. Do not bind or plan `h`/`j`/`k`/`l` as movement.

### Indentation — agreed

Start with **no automatic indentation**. Enter and `o`/`O` do not copy leading
whitespace or apply language-aware indentation. Automatic indentation is a facet
policy, not built-in default editing behaviour. Preserve the ability for facets
to contribute it later without implementing it for MS1.

### Tabs, configuration, and line joins — agreed

- By default, Tab inserts **exactly four spaces**, independent of the current
  column; it does not advance to the next tab stop. This is one user operation.
- Facets can hook into Tab handling to redefine its behaviour, including
  conversion to tabs. A concrete hook/composition API has not been designed.
- Backspace should remove the spaces created by one Tab as a unit when in
  leading whitespace or at the end of the line. In the middle of a line it
  removes one space. The leading/trailing examples discussed were confirmed.
  Provenance versus heuristic grouping and intervening-edit behaviour remain
  open.
- Explore a heuristic to infer spaces-per-Tab for existing files. Four remains
  the fallback default; the detector's rules, confidence, facet precedence, and
  how the inferred width affects Backspace are not yet specified. Detection must
  not modify the file.
- Preserve literal tabs already in a file. Their display width remains to be
  specified independently of the four-space insertion default.
- A configuration system is wanted later. Its format, scopes, and initial timing
  are not yet specified; avoid designing an entire system before it is needed.
- Backspace at the start of a line joins it to the previous line. Delete at the
  end joins it to the next line. Each join is one undoable operation.

### File fidelity and line endings — agreed

- **No file should ever change unless explicitly edited by the user.** Do not
  silently normalise, reformat, convert tabs, trim whitespace, or otherwise alter
  content on load or save. Explicit user actions may invoke facet behaviour;
  enabling a facet alone is not permission to rewrite a file.
- Preserve each existing LF/CRLF line ending, including mixed-ending files.
  Use a heuristic to guess the default ending for newly inserted lines; use LF
  for new files. The discussed approach of local line style with an inferred
  file default is acceptable in direction; exact precedence/ties remain open.
  Detection never authorises normalising existing endings.
- Preserve whether the document ends with a newline. Never automatically append
  one: a single-line file without a newline is valid and must remain possible.
- Opening/viewing a file must not modify it. A no-edit save should preserve its
  content exactly; ordinary saving of unchanged existing files performs no
  filesystem write. Explicit `:ww` and `:w <filename>` are exceptions.

## 15. Continuation — required for MS1

ME should support continuation, similar to Sublime Text:

- Users can quit with unsaved documents and retrieve them on the next startup.
- Store unsaved content privately in the user's configuration area, not in the
  document's original file. Include unnamed documents.
- Restore layout and associated editor state.
- Associate continuation state with the folder ME was started in. Starting in a
  different folder gets that folder's independent/default setup, not another
  folder's session. A previously visited folder can restore its own session.
- Ordinary quit should preserve work rather than force the user to save/discard.
- `:q!` removes every buffer with unsaved work entirely and quits, including
  recovered, unnamed, modified file-backed and missing-file buffers. It never
  deletes or reverts backing files. Saved unchanged buffers survive.
- This supersedes all earlier invocation/startup/last-save rollback policies:
  recovered unsaved content has no special protection.
- `:kill` kills the active buffer, refusing unsaved work; `:kill!` forces it.
  Remove all referencing views, preserve surviving order, and mount another
  surviving view or an empty default. Buffer kill is not text-undoable.
- Checkpoint during editing as well as on normal quit, providing crash recovery.
  A short debounced checkpoint is the proposed mechanism; interval and durability
  guarantees remain to be specified. Do not synchronously write each keystroke.
- Continuation is part of **MS1**, not a deferred feature.

This supersedes the earlier proposed conventional `:q` refusal on unsaved work.
Continuation does not write unsaved content into original files and does not
weaken the no-unexpected-file-changes rule.

### Storage direction

Use `~/.config/me` as the configuration/continuation area. The user suggested
hashing file locations to produce storage filenames. Hashes are storage keys,
not encryption; preserve original paths in metadata.

Proposed structure (not yet a committed on-disk format):

```text
~/.config/me/
  workspaces/
    <hash-of-startup-folder>/
      workspace.json
      buffers/
        <document-id>.snapshot
```

Workspace keys derive from startup-folder identity; named documents can derive
IDs from absolute file paths, while unnamed documents need generated IDs. Keep
snapshots workspace-local so different unsaved versions of one file in different
workspaces do not overwrite each other. Use private permissions, atomic writes,
and original-file content fingerprints to detect external changes (proposed).

### Recovery and startup policies — agreed

- If checkpointing fails, show a persistent/reasserted error indication until
  resolved. Ordinary `:q` refuses to exit if unsaved content cannot be safely
  stored; `:q!` is the explicit discard route. This refines the rule that ordinary
  status errors clear on content changes: an ongoing persistence failure must
  not disappear merely because editing continues.
- If a backing file changes externally and the recovered buffer has user edits,
  retain recovered content and flag a conflict. Do not overwrite the external
  version automatically. Explicit conflict-resolution/save commands remain to
  be designed.
- If the buffer has no user edits, reload changed backing-file content rather
  than presenting an unnecessary conflict. How this rebases or invalidates
  restored history/anchors still needs definition.
- `me file.n` restores the startup folder's workspace, then opens or focuses
  `file.n`. Never replace its recovered unsaved content with disk content merely
  because the file appears on the command line.
- `me -r file.n` resets the current folder's workspace instead of restoring it,
  then opens `file.n`. Reset includes discarding restored undo history. No reset
  confirmation. Bare `me -r` starts an empty default workspace. Whether reset
  should become durable only after successful file opening remains proposed.
- Undo history survives ordinary restarts. `-r` starts without restored history.
- Normal quit commits current continuation state. Discarded/killed buffers and
  their histories are omitted from subsequent snapshots.
- `:q!` preserves surviving layout, removing every unsaved buffer rather than
  resetting it to any earlier content. No recovered/new distinction applies.
- Explicit disk writes are never undone. No backing file is deleted by kill.
- `:kill` and `:kill!` affect only the active buffer, including every view that
  references it. A persisting session checkpoints the removal immediately;
  failure remains indicated and retried. Use an empty fallback if no view survives.

Still to specify:

- Exact persistence format, hashing scheme, and folder/path canonicalisation.
- Checkpoint debounce, maximum data-loss window, and durability guarantees.
- State included: buffers, views, layout, positions, folds, facets, undo history,
  interaction states, and any pending UI/input state.
- CLI reset safeguards and argument details.
- Missing/moved files, explicit conflict resolution, and history handling after
  external reload or deliberate discard.
- Multiple ME processes in the same folder are allowed. One instance owns
  continuation; a further instance starts with a default workspace instead of
  restoring it and does not save snapshots or overwrite continuation state.
  Show a warning at startup explaining that the workspace is already in use
  and this session will not save continuation snapshots. This is a
  non-persisting editor session, not read-only file access.
- Ownership detection/locking, stale-owner recovery, atomic writes, permissions,
  persistence failures, and corrupt state recovery still need specification.
- In a non-persisting session, `:q` refuses to quit while documents have unsaved
  changes. `:wq` saves all modified documents and quits only if every required
  save succeeds; `:q!` explicitly removes all unsaved buffers
  and quits. No continuation state belonging to another instance is changed.
- Still define `-r` when another instance owns continuation and whether ownership
  can transfer.
- Whether transient overlays should ever be restored (not assumed).

Retention of layout does not imply that split-pane UI must be implemented in
MS1; persist the layout actually supported by each milestone.

## 16. MS1 display, navigation, and search

### Agreed

- No soft wrapping by default; use horizontal scrolling.
- Experiment with scrolling **only the current line** horizontally, rather than
  shifting all visible lines. Exact scroll reset and selection rendering rules
  still need definition and hands-on evaluation.
- Show line numbers in a gutter. Use relative line numbers in Normal state and
  while the `:` command prompt is active. Insert-state numbering and the current
  line's number remain to be specified.
- Distinguish the current line number using a brighter colour and a highlighted
  gutter background; other numbers remain muted. This applies in both states.
- No mouse support for MS1. The user has further keyboard-navigation plans;
  do not assume click/drag/wheel support is required yet.
- `/` starts forward search; `?` starts backward search.
- `n` always navigates forward to the next match; `p` always navigates backward,
  independent of whether `/` or `?` initiated the search.
- Start with literal, case-sensitive matching; no regular expressions for MS1.
- Search wraps at document boundaries.
- Preview incrementally as the query changes and highlight all matches visible
  on screen, not just the current match.
- Enter commits the preview position and removes the transient selection.
- Escape restores the pre-search caret and scroll position, leaving no selection.
  Cursor movement does the same cancellation first, then executes ordinary
  movement from that restored position.
- Enter places the caret at the start of the current match and clears selection.
- Cancelling or confirming hides all match highlights but retains the current
  search term. Do not restore an older term merely because a search was cancelled.
  Later `n`/`p` navigation continues from the actual caret, not a stale preview
  position, and brings visible-match highlights back.
- `n`/`p` select the entire active match as an **editing selection**, enabling
  later selection commands such as `c`. Other visible matches use a distinct
  highlight colour and are not editing selections. This supersedes the proposed
  caret-only behaviour for `n`/`p`; Enter confirmation still clears selection.
- Confirming an empty search prompt reuses the remembered term. If none exists,
  show `No previous search`.
- Repeated `n`/`p` move to the next/previous occurrence rather than selecting
  the same active match again.
- Ordinary cursor movement after `n`/`p` clears the editing selection and passive
  highlights, without undoing the search jump. This is distinct from cancelling
  an in-progress search prompt, which restores pre-search position.
- `c` deletes the editing selection and enters Insert. The deletion is one undo
  operation; subsequently inserted characters remain individually undoable.
  Behaviour of `c` without a selection still needs definition.
- Selection direction/active end, highlight dismissal on Escape or edits after
  `n`/`p`, and status indication on wrap still need definition.

### Search origin prefixes — agreed

- `/text`: forward from the current position.
- `?text`: backward from the current position.
- `//text`: forward from the start of the document.
- `??text`: backward from the end of the document.
- A backslash escape permits a literal leading delimiter in the query; exact
  escape parsing, including literal backslashes, still needs specification.
- The first delimiter opens the prompt; a second leading delimiter selects the
  alternate origin without requiring a key-sequence timeout (proposed mechanism).
- Later `n`/`p` operate from the current caret, rather than restarting at the
  explicit search origin.

## 17. Selection-first Normal commands — agreed experimental vocabulary

These are Normal-state commands; their letters remain ordinary text in Insert.
Do not reserve `v` for a separate selection state or `l` for Vim-style movement.

| Key | Action |
| --- | --- |
| `y` | Yank/copy the selection, preserving it |
| `x` | Cut the selection; leave the caret at the deletion point |
| `v` | Paste, respecting characterwise versus linewise content |
| `c` | Delete selection as one operation, then enter Insert |
| `l` | Select a line, including its line ending when present |
| `w` | Select the whole word containing the caret |

- Characterwise paste replaces an existing selection or inserts at the caret
  when none exists. One paste is one undo operation.
- Preserve whether yanked/cut content is **characterwise or linewise**, not just
  its text. `v` must interpret that distinction. Without a selection, linewise
  paste inserts below the current line. Exact behaviour with an existing
  selection still needs agreement.
- `w` inside a word selects the whole word. Partial-word command forms can come
  later. Whitespace/punctuation classification remains open.
- `l` includes an existing line ending, enabling whole-line cut without leaving
  an extra empty line. On a final unterminated line, never invent a file newline
  just to select it; exact cut/paste boundary handling remains open.
- Repeated `w`/`l` extend the selection by another word/line: `lll` selects three
  lines. This does not imply a persistent unit cursor model.
- `<num>w` selects that many words, from the beginning of the first word through
  the end of the last, including intervening separators. The first word contains
  the caret when the caret is inside a word. `<num>l` likewise selects that
  many lines. Count handling on existing selections, whitespace starts, and
  numeric prefixes for other commands remain open.
- Word selection treats letters, digits, and underscores as a word, so
  `my_variable` is one word. Punctuation forms separate selectable runs;
  whitespace is skipped when extending to the next word, while remaining inside
  the contiguous selected range. Exact Unicode classification remains open.
- Ctrl+D duplicates the current line below itself and moves the caret to the
  duplicate at the same column. It enters Normal under the Ctrl-command policy.
  The entire duplication is one undo operation. Selection clearing and
  unterminated-line handling still need exact definition.
- Ctrl+command shortcuts apply in both Normal and Insert where appropriate.
- **Ctrl-bound non-navigation commands leave Insert and execute in Normal**,
  including save, undo, redo, and line duplication. Remain in Normal even on
  failure or a no-op. This supersedes Ctrl+D's earlier state-preservation rule.
- Ctrl-modified navigation, such as word movement, preserves the interaction
  state. Classify this explicitly in binding/action metadata rather than
  treating every Ctrl key as an instruction to leave Insert.
- MS1 uses an **internal ME clipboard**, retaining characterwise/linewise
  metadata. System clipboard integration is deferred pending API/terminal
  investigation; persistence of clipboard contents is not yet specified.
- Ctrl+Z is the sole undo binding and Ctrl+R the sole redo binding, available
  in both Normal and Insert. Do not add `u`, Ctrl+Y, or other aliases.
- Avoid redundant keybindings for the same command. This does not remove the
  explicitly agreed Ctrl+S / `:w` shortcut-and-command-prompt access paths.
- Navigation is independent of buffer undo/redo: viewed positions belong to
  views, while undo/redo records document edits. Navigation does not add buffer
  history entries. Any future navigation/jump history is a separate facility.
- On undo/redo, the invoking view's caret moves to the affected edit and its
  selection clears (agreed). Other views track content changes through anchors.
- Ctrl+Z and Ctrl+R always enter Normal under the agreed Ctrl-command policy,
  including when there is no edit to undo/redo.
- `d`, Ctrl+C/Ctrl+X/Ctrl+V, and no-selection errors were discussed as
  possibilities, not adopted bindings/policies. Do not add aliases speculatively.

## 18. Navigation baseline — agreed

| Keys | Action |
| --- | --- |
| Left/Right | Move one character |
| Up/Down | Move one line, retaining the preferred column |
| Ctrl+Left/Right | Move by word |
| Home | Move to first non-whitespace; when already there, move to column zero |
| End | Move to line end |
| Ctrl+Home/End | Move to document start/end |
| Page Up/Down | Move by one visible page |
| Ctrl+Page Up/Down | Move by paragraph |
| Ctrl+Up/Down | Scroll the view by one line |
| Shift + navigation | Extend selection for caret-moving navigation |

- Home uses smart-home behaviour: first non-whitespace, then column zero on
  another press when already at that position. This supersedes the earlier
  absolute-column-zero rule. `I` still enters Insert at first non-whitespace.
  Further presses and whitespace-only-line details remain to be specified.
- Ctrl navigation preserves interaction state, unlike Ctrl editing commands.
- Paragraph navigation is redefinable by facets; the Nerd facet may navigate
  language-level bindings instead. No Nerd-specific implementation is required
  for MS1.
- Default paragraphs are runs of non-blank lines separated by one or more blank
  lines. Whitespace-only lines count as blank. Facets may redefine these units.
- Ctrl+Up/Down scroll without changing the caret's document position, allowing
  it to go off-screen. A subsequent caret movement or text insertion scrolls the
  view as needed to reveal it.
- Typing numeric prefixes in Normal must **not** reveal an off-screen caret;
  leave the scrolled view intact while building a relative-movement count.
  Executing the eventual movement reveals its destination.
- Entering `:` command mode and typing a line-number destination likewise must
  not snap back to the old caret. Reveal the destination on executed navigation.
  A bare line number at the prompt, e.g. `:120` followed by Enter, goes to
  absolute line 120. A Normal numeric prefix followed by an arrow repeats its
  movement; `12` then Down moves down 12 document lines.
- Relative gutter numbers remain measured from the actual caret line, even
  while that caret is off-screen.
- Out-of-range movement clamps to document boundaries; e.g. `:9999` in a
  100-line document goes to line 100. Absolute line jumps place the caret at the
  destination's first non-whitespace character.
- Vertical arrow movement retains a preferred column separately from the
  currently reachable caret column. A short line clamps the caret to its end
  without reducing that preference; a later longer line restores the preferred
  column. This applies to counted vertical arrow movement as well.
- Left/Right, Home/End, explicit jumps, and editing establish a new preferred
  column at the resulting caret position.
- Measure preferred column in display cells, accounting for tabs and wide
  characters, not bytes. If the target falls inside a tab or wide character,
  choose the nearest valid text boundary. Tie-breaking remains unspecified.
- Escape cancels a pending count. A completed command consumes it. Unsupported
  count-command combinations report an error and clear the count, so it never
  leaks into another command. Zero/overflow parsing still needs specification.
- Page overlap, word-motion boundaries, Shift variants of scroll-only actions,
  and reveal behaviour for other non-moving actions remain to be specified.

## 19. Encoding, characters, and external changes

### Agreed

- MS1 editable text is UTF-8. Preserve an existing UTF-8 BOM.
- Refuse unsupported encodings or invalid UTF-8 with a clear error; never
  silently replace undecodable input. A prompted conversion-on-load feature
  may be considered later, but is not required now.
- Caret character movement and character deletion should operate on
  user-perceived characters (grapheme clusters), not individual UTF-8 bytes or
  combining code points. Investigate Nerd facilities and implementation support;
  this requirement must not be silently reduced to code-point editing.
- External changes to an unedited open document should become visible as soon
  as reasonably possible. Save-time/focus-only checking is insufficient as the
  primary detection strategy. Exact watching/polling mechanism is not yet agreed.
- Retain the existing policy: reload unedited buffers; preserve edited content
  and flag conflicts.
- A successful external reload is one undoable buffer operation, not a history
  reset. Undoing it restores the previous content and marks the buffer modified
  relative to disk. Preserve prior history. An unchanged reloaded buffer survives
  `:q!`; one modified afterwards is removed entirely.
- If a backing file is deleted externally, keep the buffer content visible and
  mark the file missing. Do not empty or close the buffer. An explicit save may
  recreate the file; saving must not incorrectly no-op merely because the user
  has not edited the retained content.
- A document whose backing file was deleted follows new/unsaved-document
  continuation rules: normal quit retains its in-memory content for recovery,
  even if the user made no text edits. Preserve its known path and missing-file
  status, and do not silently recreate the file on quit or restoration.
- Missing-file buffers count as unsaved work: `:q!` removes them entirely,
  including recovered content, without recreating or deleting a backing file.
- If the missing file reappears, use ordinary external-change handling: reload
  if there are no user edits; preserve content and flag a conflict otherwise.

### Proposed next discussion

Use directory watching where available and periodic metadata polling as a
fallback, with content verification as needed. Watch parent directories to detect
atomic replacement, not only writes to an old file handle. Avoid blocking the
input loop, avoid partial-write reloads, and do not rewrite the original file.
Debounce/stability checks, latency, missing files, and error policy remain open.

## 20. Status bars and workspace command/message area — agreed

- Each pane has its own status bar, separate from a workspace-wide bottom area.
  Show interaction state, document identity/state, caret position, and pending
  input/counts as appropriate. Exact formatting remains open.
- Do not use the verbose `no continuation` text as a permanent status label;
  it consumes too much space. Keep the required startup warning; a compact
  persistent indicator remains to be chosen.
- Reserve the workspace's bottom line for commands and messages (`:`, search,
  errors, warnings, and other feedback). This refines the earlier status-line
  error requirement: message text belongs in the bottom area; pane status bars
  can retain compact document-state indicators.
- The bottom section grows to fit multi-line messages and shrinks again when
  those messages disappear. It is outside individual panes, not a popup.
- If a layout/available-height change forces a previously visible view caret
  off-screen or outside its view, recentre that view on the caret. Apply this to
  all affected visible views, not just the focused one.
- This resize-induced recentering is distinct from intentional Ctrl+Up/Down
  scrolling: preserve the established ability to scroll away from the caret
  without immediately snapping back. Define precise interaction if the caret
  was already deliberately off-screen before a resize.
- Cap the bottom message area at half the terminal height; allow scrolling for
  longer messages. Exact rounding and minimum usable dimensions remain open.
- If a caret was already intentionally off-screen before resizing, preserve the
  view position rather than recentering. Recentring is triggered only when the
  resize pushes a previously visible caret out of view.
- Automatic content-driven sizing is sufficient for MS1; manual resizing is
  deferred.
- Escape dismisses displayed messages without moving the caret or changing the
  selection. Message dismissal consumes that Escape rather than also applying
  ordinary selection-collapse behaviour.
- Ordinary editing can clear transient messages. Ongoing failures, such as a
  checkpoint failure, remain indicated until resolved; dismissing their message
  does not imply the condition is fixed.
- Message-scroll bindings, exact prompt focus/precedence rules, compact persistent
  failure indicators, and tiny-terminal sizing still need specification.

## 21. Replaceable buffer implementation — agreed direction

- Put buffer interactions behind a trait or traits, using Nerd `impl` blocks.
- Do not introduce compile-time implementation substitution or a generic backend
  selection framework. If storage changes later, refactor the implementation
  behind the contracts.
- Exact trait boundaries, signatures, and dispatch details remain to be designed
  against Nerd's actual facilities.
- Proposed access contracts should not require contiguous text or expose stable
  raw pointers into storage; these would unnecessarily constrain future changes.
- A gap buffer is a candidate, not an agreed storage choice.
- Buffer-owned undo history is agreed. Views own their carets, selection
  anchors, and other navigation positions; buffers report concrete edits so
  views adjust those positions themselves. Other consumers own and update their
  own tracked ranges. Shared adjustment logic is fine; a central buffer-owned
  anchor registry is not the chosen initial model. Navigation is not buffer
  undo history.

### Declarative, position-explicit editing — agreed

- Prefer declarative interfaces: callers describe the edit and its document
  position, not the storage manipulation needed to perform it.
- Insertions include the desired document position. The implementation translates
  that position to physical storage indices and repositions a gap if necessary.
- Do not expose gap movement, a storage cursor, or physical buffer indices as
  prerequisites for editing. Reads, caret movement, selection changes, and view
  scrolling do not reposition gaps.
- If a gap buffer is used, reposition the gap only when an actual mutation
  requires it, including insertion, deletion, or replacement. Do not move it in
  anticipation of editing, during navigation, or during reads. This clarifies
  and supersedes the earlier insertion-only wording.
- Deletion can move the gap to the start of the requested range, then expand
  the gap over the deleted content. Avoid movement when the range is already
  adjacent or another equivalent local adjustment suffices. Storage mechanics
  remain private to the implementation.
- Document positions use **logical UTF-8 byte offsets**, excluding the gap or
  other storage artefacts. They are not physical storage indices, character
  counts, or terminal columns.
- Resolve line/column and grapheme boundaries through buffer queries; views
  handle display-cell mapping. Character movement/deletion still operates on
  whole grapheme clusters, not individual bytes.
- Default cross-view position adjustment: insertion exactly at another view's
  caret leaves it before the inserted text (left affinity). The editing view
  explicitly advances its own caret as required by its command.
- Deletion containing another view's caret collapses it to the deleted range's
  start. Views perform this adjustment from edit notifications; the buffer does
  not own their positions.
- For an existing non-empty selection affected by edits from elsewhere:
  insertion at its range start stays outside (start advances past inserted text);
  insertion at its range end stays outside (end remains before inserted text);
  insertion strictly inside becomes part of the selected range. These rules use
  ordered range boundaries regardless of anchor/active-end direction.
- Deleting the whole selection collapses it to the deletion point. If another
  view replaces exactly the entire selected range with non-empty text, the
  selection follows the replacement text. Treat replacement as one semantic
  edit, not separate notifications whose insertion affinities would exclude it.
- The editing view may explicitly choose its own resulting selection. An empty
  selection uses the caret's left-affinity rule, not opposing endpoint affinities.
- Proposed edit notification: replaced range in the previous revision, inserted
  byte length, and previous/resulting revision IDs. Exact notification/trait
  signatures, valid-boundary enforcement, replacement-boundary semantics, and
  line-index maintenance still need design.

## 22. Implementation and toolchain policy — agreed

- MS1 targets **Linux only**. Use Nerd's standard-library APIs for terminal and
  operating-system interaction where available.
- ME/user code must not directly reference libc or introduce external-library
  dependencies. If low-level functionality is required, investigate Nerd's
  `syscall` facilities and standard-library patterns.
- Explicit temporary exception: existing `nrt.c` runtime dependencies and the
  current native toolchain linkage are allowed. Normal Nerd executable builds
  and tests may proceed. This does not authorise direct libc FFI in ME, new
  external libraries, or expanding the existing runtime dependency.
- The user considers libc involvement in compiled Nerd programs a Nerd bug.
  Removing the existing runtime dependency is deferred under this exception,
  not resolved or accepted as the intended long-term design.
- Respect Nerd idioms, particularly expressive `on`/`for` constructs and pattern
  matching. Read the language documentation and `docs/idiomatic-nerd.md` before
  designing concrete implementations. Do not mechanically translate another
  language's style.
- Run `nerd format` periodically during source editing and review its changes.
- **Compiler bugs are top priority.** Do not work around them in ME. Investigate
  and fix confirmed compiler bugs in a **dedicated Git worktree of `~/nerd`**,
  since another agent is working in the main checkout. Do not modify shared
  compiler sources/build/install state without coordination. Follow the
  worktree's current README workflow, tests, documentation, formatting, installation, commit, and
  push requirements. Read the current instructions rather than relying on this
  summary. Distinguish unsupported features from confirmed compiler bugs.
- Recommended missing standard-library functionality should first be implemented
  locally in ME and documented for later evaluation as a standard-library
  addition. Do not automatically upstream it or add an external dependency.
- Track such candidates in [standard-library-candidates.md](standard-library-candidates.md).

## 23. Historical scope agenda

This was the initial agenda. Later agreed sections above supersede settled
items; the current implementation is described separately below.

- Exact initial Vim-like subset and interaction-state transitions.
- Command representation, motions, transaction mechanics, undo cursor policy,
  repeat capture/playback details, redo, and any later named macros.
- Text storage: gap buffer, piece table, or another representation.
- Anchor semantics and shared-view update rules.
- Unicode guarantees, tabs, wrapping, line endings, and invalid file encodings.
- File safety, external changes, recovery, and save policy.
- Facet composition, conflict resolution, and service lifecycle.
- Popup policies, focus restoration, and cooperative completion input.
- File picker search/discovery behaviour and project/workspace boundaries.
- UI defaults: tabs, line numbers, sidebars, status line, mouse behaviour.
- Supported platforms and terminals.
- First usable milestone and measurable performance targets.

Earlier suggestions of a modeless editor or postponing pane architecture have
been superseded by the agreed modal, pane-aware design. A permanent text-storage
choice, full Vim compatibility, and a plugin ABI have not been adopted.

## 24. MS1 implementation choices, not new user agreements

These are provisional answers used to ship the authorised first version. They
are distinguished from the explicit user agreements above and can be refined
through hands-on feedback. See the [README](../README.md) for the working keymap
and command reference, and [MS1 progress](ms1-progress.md) for verified gates.

- **Scope and scaffold:** one mounted text view/pane, zero or one CLI filename,
  no initial-position CLI syntax. Dot-segment resolution is left to Linux so
  symlink/`..` paths select the correct file; existing aliases reuse inode identity.
  A nonexistent path is a new named document,
  created only by explicit save. `just` recipes and compiler/module overrides
  provide the standard environment. No interactive file picker was added.
- **Retained documents:** `:buffers` and `:buffer N` give keyboard access to
  recovered or CLI-opened documents without requiring pane-management UI.
  They do not add movement aliases or change buffer/view ownership.
- **Storage:** the initial backend is a trait-backed gap buffer. Document read
  projections and line indexes are cached across reads and rebuilt on edits.
  Incremental projection/indexing remains future performance work.
- **Unicode:** pinned Unicode 16 UAX #29, East Asian width, emoji, category and
  whitespace data. Ambiguous characters are narrow. Words use Unicode letters,
  decimal digits and underscore; other punctuation/symbols form separate runs.
  Whitespace is Unicode White_Space. A leading UTF-8 BOM remains in byte storage
  and history but the first editable line starts after it; normal view commands
  therefore neither copy nor duplicate the preamble.
- **History/input:** each terminal Unicode character event is an insertion
  operation. Grapheme movement/deletion is separate from terminal event
  granularity. Compound IME/paste-boundary grouping awaits a suitable terminal
  event contract; internal paste and replace-all are single operations.
- **Selection/paste:** ordinary movement starts from the active end and clears
  selection. Copy without selection reports an error and retains the clipboard;
  `c` without selection only enters Insert. Existing-selection paste replaces
  precisely that range, regardless of clipboard type. A final line without an
  ending keeps that content; linewise paste adds only separators required by its
  explicit insertion below another line.
- **Counts/positions:** positive bounded Normal prefixes, with unsupported
  combinations rejected/consumed. Home/End/document edges reject counts.
  Absolute numeric jumps saturate at the document edge, even for huge numbers.
  Display-cell navigation chooses the boundary before a tab/wide character when
  a preferred column falls inside it. There is no wrapping in the text view.
- **Indentation:** Tab-width inference uses a small GCD of leading-space samples,
  only choosing 2–8 spaces with sufficient evidence; otherwise four. Backspace
  groups an exact Tab-sized space suffix at leading/trailing whitespace, without
  historical provenance tracking. No automatic indentation is performed.
- **Search/replace:** literal, case-sensitive search and match selections follow
  the agreed contract. `:replace /old/new/` adds one-occurrence replacement;
  a trailing `g` replaces all non-overlapping matches as one history operation.
  Delimiter/backslash escapes are lexical, not newline conversion syntax.
- **External changes:** 250 ms polling, two stable metadata samples before a
  content read/reload. This is normally 0.5–0.75 seconds, not a hard latency
  guarantee. Ownership/mode/ACLs/xattrs are preserved on save or the save fails.
  A final check/rename race with uncooperative writers cannot be eliminated by
  ordinary Linux rename; no filesystem transaction is claimed.
- **Continuation:** `~/.config/me/<FNV-64-folder-key>/`, full-folder validation,
  a non-blocking flock, checksummed versioned snapshot, byte/history replay
  validation, 400 ms debounce and attempted two-second continuous-edit maximum.
  Positions/selection/scroll/preferred columns survive; startup normalises every
  view to Insert only for empty content, Normal otherwise. Prompts/messages,
  clipboard/search, counts and incomplete commands do not survive.
- **Failure/discard:** failed reset/open leaves the existing snapshot intact.
  A corrupt snapshot disables fallback-session persistence rather than
  overwriting evidence. `:wq` asks unnamed documents in document order, retains
  successful earlier saves, and focuses a later failed document. Killed/discarded
  documents and all referencing views are removed; surviving layout is retained with an empty fallback
  when necessary. A second instance, including `-r`, never touches snapshots.
- **Display:** absolute Insert gutter, relative Normal/command gutter with an
  absolute current line, gold on a highlighted background; other numbers muted; current-line-only horizontal scrolling resets on a
  line change. Wrapped messages grow to half the terminal, with Alt+Page Up/Down
  scrolling. `!C`, `~`, `!conflict`, `?missing` are compact persistent markers.
  Tiny terminals prioritise the message/prompt area. Resize preserves deliberate
  scroll-away and recentres only a previously visible caret forced out.
- **Terminal bridge:** ordinary cells use `std.term`'s retained framebuffer; a
  bounded local overlay bridges single-codepoint cells to complex graphemes.
  Linux signal descriptors request safe termination without libc handlers.
  Legacy Escape timeout resolution and bracketed-paste events remain investigated
  library gaps, documented in the README rather than silently patched upstream.

This does not settle later facets, split trees, popup composition, repeat
recording, system clipboard, configuration, or language-service APIs.
