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
  Movement uses cursor keys and Normal `h`/`j`/`k`/`l` for left/down/up/right.
  The later HJKL decision supersedes the original cursor-keys-only policy.
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
- **Facet:** a composable specialisation of a view. The original terminology
  compared facets with Emacs modes. The later file-type mode decision (§35)
  introduces modes explicitly; Normal/Insert remain interaction states.
- **File-type mode:** a customisable system selected for a file type that
  determines LSP, formatting, syntax highlighting, indentation and related
  file-type behaviour. Its relationship with composable view facets is to be
  specified in the future modes milestone.
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

### Multiple-file CLI — agreed and implemented

`me file1 file2` starts fresh, loading only those distinct files, without an
extra unnamed buffer, and displaying the first successful path. Plain filenames
and explicit `-r` erase the old snapshot after acquiring its exclusive lock,
before attempting opens, even if all opens fail. Erasure failure is fatal; a
second instance never deletes another process's snapshot. Fresh work checkpoints
normally thereafter. This deliberately supersedes the old failed-reset retention.

Bare `me` restores continuation. `me +file1 +file2` explicitly restores it before
adding/focusing files, reusing identity/view/history and keeping unrelated work.
Strip exactly one `+` before normal home/byte-safe path resolution; `./+name`
is a literal fresh filename, `++name` an appended literal-plus filename. Reject
bare `+`, mixed plain/+ paths and `-r`/+ paths before touching continuation.

Open in argument order, then refocus the first successful view. Workspace access
tracking records real focus changes; picker order is still MRU, not argument
order. Missing paths remain unwritten until explicit save. Report failures and
try later arguments; if all fail, keep explicitly restored buffers or exit 2 if
none remain. Unknown flags remain errors; no initial-position syntax is added.

### First popup consumer: buffer switcher — agreed and implemented

Normal `,` opens a capturing, workspace-relative popup occupying most of the
terminal. A reusable owning fuzzy-list model keeps IDs, safe labels, annotations,
query/caret, filtered indices, selection and scroll distinct from document text,
view selection and undo. A shared bounded layout and generic renderer overlay
it after the document/status. Opaque popup drawing clips existing complex-glyph
overlays; tiny/resized terminals remain bounded. Search input stays at the top.

Matching is Unicode 16 default full-case-folded codepoint subsequence matching,
not substring-only search or score ranking. Paths retain MRU source order. Start
with the current document first and the second entry selected (first if alone).
Up/Down/Page keys navigate; Enter immediately accepts a valid candidate; no-match
Enter is a no-op; Escape cancels. Letters, commas and digits edit the query,
not Normal commands. Query editing is grapheme-aware and bounded at 4,096 bytes.

Workspace access tracking is separate from document/view array order. All focus
paths update it. Continuation v3 adds validated unique document IDs in access
order; v1/v2 imports preserve content/history and seed restored-active-first order.
Popup/query state is transient. A read-only right-hand preview follows the
highlighted document's current in-memory text, including unsaved edits, from the
first line. It clips by grapheme/display width, expands tabs, and shares safe
Unicode rendering without I/O or mutations of view/history/MRU. No selection
clears it. Keep the top query full-width; hide preview on narrow/short terminals
and give the list the full width. This first consumer does not yet implement the
proposed overlay stack, asynchronous discovery or pane destinations.

Outside popups, Ctrl+W closes the focused pane, retaining its buffer and all
other panes' buffers and navigation state. It enters Normal, including from
Insert, and keeps the final pane open. Unsaved work is retained. This supersedes
the original active-buffer deletion binding (T5b).

Ctrl+W removes the highlighted buffer when the buffer picker is open, only when saved. No matches means no action. Keep the picker
open after success or refusal, retaining query/caret and selecting the same result
row, clamped to the last remaining row. Rebuild candidate IDs/annotations/preview
after removal; an empty result set stays open. Closing another buffer preserves
the active buffer.
Unsaved/new/missing work errors without writing/discarding it; explicit `:kill!`
remains the force path. Closing the active buffer focuses MRU surviving work or
creates a fresh empty buffer. Picker Ctrl+W enters Normal on both
success/failure; legacy `:kill` retains its existing empty-buffer Insert behaviour.
Key/text suppression follows the input stream across view changes/destruction,
so an associated Enter/Ctrl+W text event cannot affect the destination buffer.

### Enhanced key actions — agreed

Keyboard commands and ordinary UI handlers execute on press/repeat, never on
release. Diagnostic capture is the exception: `:keys` retains releases for
inspection. This applies to message scrolling as well as buffer/prompt movement.
Nerd's parser must preserve event-type subparameters for traditional CSI cursor,
Home/End and tilde-key encodings, not just CSI-u; a missing event type remains a
legacy press. ME must not infer actions or filter escape-sequence bytes itself.

### Home-relative file paths — agreed

File opening, saving and filename completion expand a complete leading `~` or
`~/` using the process `HOME`. The remainder stays byte-literal, including spaces
and non-UTF-8 bytes. Missing/non-absolute HOME is an error, not a fallback into a
cwd `~` directory. Other tildes, `$HOME` and quotes remain literal; no `~user`
lookup or general shell expansion is introduced. Keep OS symlink/`..` semantics.

Completion resolves the home directory only for discovery; candidates retain
`~/`. Bare `~` completes to `~/` first. Literal cwd entries named `~` are completed
with `./~` to avoid semantic redirection; callers can type this explicitly too.
Shared local path expansion belongs beside the Linux environment/path helpers,
not separately in the prompt, workspace and directory enumerator.

### Keyboard protocol diagnostics — agreed

`:keys` captures keyboard input without editing or saving, showing actual
`std.term` capabilities, Kitty reply flags, query completion and a six-event
bounded decoded trace. Key names, actions, modifiers and numeric character/text
values are safe to render; no terminal-supplied controls are replayed. Escape
closes the view, Alt+Page Up/Down scroll, and reopening clears the trace. The
existing message surface expands while diagnostics are active; this is not the
popup/picker framework. Neither trace nor active mode is persisted.

Capability detection lives in Nerd, not an ME escape-sequence workaround. Partial
Kitty flags must not overclaim reliable held/physical keys. A zero reply differs
from no reply; the following DA reply completes a negative probe. Missing replies
leave legacy fallback pending rather than pretending a timeout proves absence.
Terminal/multiplexer filtering and custom key remappings can still make Ctrl+H
and Ctrl+Backspace indistinguishable. Diagnostics report decoded events, not raw
bytes, and do not claim support detection for every terminal-specific protocol.

## 11. Project environment

**Agreed:** standard Nerd project with `just` recipes.

**Proposed recipes:**

| Recipe | Purpose |
| --- | --- |
| `just build` | Debug executable under `_bin/` |
| `just run [args…]` | Build/run ME |
| `just release` | Optimised executable |
| `just check` | Compiler checking without linking |
| `just test` | `nerd test main.n`, discovering colocated headless tests |
| `just format` | Nerd source formatting |
| `just clean` | Remove this project's generated outputs |

Use installed `nerd` by default and allow explicit compiler/library overrides for
working against a checkout. Do not require a hard-coded `~/nerd` absolute path.
Follow Nerd idioms and underscore-prefixed generated output directories.

Native tests are colocated with their implementation modules in named `test`
sections. Helpers and test-only imports belong in bare `test { ... }` sections,
excluded from normal builds. Cross-layer integration tests live at the highest
relevant layer; do not reverse production dependencies just to colocate a test.
The generated Unicode conformance test occupies a marked section in
`src/characters.n`, maintained by `build/generate_unicode.py`. Real process/PTY
checks remain in Python under `tests/terminal.py`.

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
  sequence, not one internal operation at a time. Redo preserves that
  grouping (delivered under T6).

This explicitly supersedes the earlier proposal to preserve individual undo
boundaries during replay. The same commands can execute as separate history
entries during recording and as a compound history entry during replay.

Proposed mechanism: record semantic command invocations rather than physical
keys or absolute document offsets, and execute playback inside an explicit
buffer history group. That group does not imply UI/input state is buffer-owned.

Do not record undo commands for playback. The agreed direction is for undo
while recording to remove the undone operation from the captured sequence, so
playback reproduces the corrected edit rather than an intermediate mistake plus
an undo. T6's initial correction and history-boundary policies are recorded in
§32 below.

If replay fails partway, keep the partial result as a single undoable group and
report why/where it stopped. Do not automatically roll back its completed edits.
This supersedes the proposed rollback policy.

T6 delivers the first current-buffer editing/navigation implementation, with one
recording per session. Its initial policies for transitions, selections,
corrections, scope and storage are recorded in §32. Named macros, cross-buffer
recording and implicit last-change capture remain outside this task.

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
No-argument, fresh-file and explicit-continuation CLI policies are now specified
in “Multiple-file CLI” above; nonexistent paths stay unwritten until saved.

### MS1 entry and deferred features — agreed

For MS1, deal with command-line support for opening files rather than building
interactive file-navigation popups. Panes and global file pickers are not MS1
requirements; retain the long-term design without implementing them now.
CLI/startup policy is now specified above; save/save-as interaction is specified
below. This does not mean the editor itself is non-interactive.

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
- Use cursor keys for movement in either state, plus `h`/`j`/`k`/`l` in Normal.
  HJKL share arrow movement/count semantics and remain text in Insert/prompts.

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
- `//text`: forward from the start of the document. The user explicitly retained
  this origin prefix alongside replacement; parse it before later separators.
- `??text`: backward from the end of the document.
- A backslash escape permits a literal leading delimiter in the query; exact
  escape parsing, including literal backslashes, still needs specification.
- The first delimiter opens the prompt. A second leading delimiter selects the
  alternate origin. Only a later unescaped `/`, after a non-empty search term,
  selects replacement; escape literal slashes in forward queries.
- Later `n`/`p` operate from the current caret, rather than restarting at the
  explicit search origin.

## 17. Selection-first Normal commands — agreed experimental vocabulary

These are Normal-state commands; their letters remain ordinary text in Insert.
Do not reserve `v` for a separate selection state. The later agreed HJKL
navigation assigns `l` to right movement and moves line selection to `q`.

| Key | Action |
| --- | --- |
| `y` | Yank/copy the selection, preserving it |
| `x` | Cut the selection; leave the caret at the deletion point |
| `v` | Paste, respecting characterwise versus linewise content |
| `c` | Delete selection as one operation, then enter Insert |
| `q` | Select a line, including its line ending when present |
| `w` | Select the whole word containing the caret |

- Characterwise paste replaces an existing selection or inserts at the caret
  when none exists. One paste is one undo operation.
- Preserve whether yanked/cut content is **characterwise or linewise**, not just
  its text. `v` must interpret that distinction. Without a selection, linewise
  paste inserts below the current line. Exact behaviour with an existing
  selection still needs agreement.
- `w` inside a word selects the whole word. Partial-word command forms can come
  later. Whitespace/punctuation classification remains open.
- `q` includes an existing line ending, enabling whole-line cut without leaving
  an extra empty line. On a final unterminated line, never invent a file newline
  just to select it; exact cut/paste boundary handling remains open.
- Repeated `w`/`q` extend the selection by another word/line: `qqq` selects three
  lines. This does not imply a persistent unit cursor model.
- `<num>w` selects that many words, from the beginning of the first word through
  the end of the last, including intervening separators. The first word contains
  the caret when the caret is inside a word. `<num>q` likewise selects that
  many lines. Count handling on existing selections, whitespace starts, and
  numeric prefixes for other commands remain open.
- Word selection treats letters, digits, and underscores as a word, so
  `my_variable` is one word. Punctuation forms separate selectable runs;
  whitespace is skipped when extending to the next word, while remaining inside
  the contiguous selected range. Exact Unicode classification remains open.
- Backspace in Insert deletes backwards, or removes the active selection. In
  Normal it deletes only a selection; without one it leaves text, caret and
  history unchanged. Preserve the interaction state. Existing Tab-space grouping
  and line-join policies apply to Insert deletion.
- Explicit Ctrl+Backspace in Insert deletes the selection, or back to the previous
  Ctrl+Left word boundary (including intervening whitespace), as one undo operation.
  In Normal it deletes only a selection. In prompts it edits the prompt.
- Both legacy `0x08` and `0x7f` are ordinary Backspace. This supersedes the earlier
  legacy-0x08 word-delete interpretation: a terminal sending the same byte for
  plain Backspace and Ctrl+Backspace cannot distinguish them. Use enhanced Ctrl
  reports for word deletion. Diagnostics continue to expose the ambiguity.
- Ctrl+D duplicates the whole line-selection block below itself, retaining the
  copied block as a line selection so duplication can repeat. Without a non-empty
  line selection, duplicate only the caret's current line, clear any character
  selection and move to the copy at the same display column. Either form is one
  undo operation and enters Normal under the Ctrl-command policy.
  Preserve source line endings; prepend a local/inferred ending when duplicating
  an unterminated final line or block.
- Ctrl+command shortcuts apply in both Normal and Insert where appropriate.
- **Save, undo, redo and line duplication leave Insert and execute in Normal**,
  including on failure or a no-op. This supersedes Ctrl+D's earlier state-preservation
  rule. Backspace/word deletion preserve state, superseding their earlier Normal
  transition. Ctrl+N enters Insert; Ctrl+G cancellation preserves the current state.
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
- On undo/redo, the invoking view restores the editing operation's before/after
  caret and clears its selection. Capture these hints only when an edit is made;
  navigation neither rewrites them nor creates history entries. Older/unannotated
  history falls back to the affected edit's start. Other views still track content
  changes through anchors. Persist optional hints in snapshot v2, importing v1
  without losing its document/history.
- Ctrl+Z and Ctrl+R always enter Normal under the agreed Ctrl-command policy,
  including when there is no edit to undo/redo.
- `d`, Ctrl+C/Ctrl+X/Ctrl+V, and no-selection errors were discussed as
  possibilities, not adopted bindings/policies. Do not add aliases speculatively.

## 18. Navigation baseline — agreed

| Keys | Action |
| --- | --- |
| Left/Right | Move one character |
| Up/Down | Move one line, retaining the preferred column |
| Ctrl+Left/Right or Ctrl+H/L | Move by word |
| Home | Move to first non-whitespace; when already there, move to column zero |
| End | Move to line end |
| Ctrl+Home/End | Move to document start/end |
| Page Up/Down | Move by one visible page |
| Ctrl+Page Up/Down | Move by paragraph |
| Ctrl+Up/Down or Ctrl+K/J | Scroll the view by one line |
| Shift + navigation | Extend selection for caret-moving navigation |

- Explicitly agreed Ctrl+H/J/K/L aliases mirror Ctrl+Left/Down/Up/Right:
  H/L move by word; J/K scroll without moving the caret. They preserve Normal
  or Insert, support Normal counts and use existing Shift selection semantics.
  Recognise enhanced physical key/modifier reports, suppress paired text events,
  ignore releases and honour repeats. Legacy `0x08` uses ordinary Backspace and
  legacy newline keeps Enter; explicit Ctrl reports distinguish word deletion.
  In picker popups the same aliases use existing arrow semantics: J/K select
  rows and H/L move the query caret. Paired text remains suppressed there too.
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

- Normal uses a green cursor and status bar; Insert uses red to signal editing
  danger. Improve status readability using UTF-8 presentation, retaining clear
  textual mode labels and file/error/position information.
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

- **Scope and scaffold:** one mounted text view/pane, zero or more CLI filenames,
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
  the agreed contract, as refined by the later second-slash decision: `/old/new`
  replaces all non-overlapping matches in the whole buffer; `/old/new/c` confirms
  using Y/N/A/Escape. Completed/partial approved replacements are one history
  operation, valid at every checkpoint. `:replace` and `g` are removed, but `//`
  forward and `??` backward origins remain; parse origin prefixes before field
  separators. Slash/backslash escapes are lexical, not newline conversion
  syntax; forward literal slash queries must escape them.
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
- **Failure/discard:** plain CLI filenames and `-r` now erase the old snapshot
  before opens, including failures (superseding the original retention policy).
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
- **Mode presentation:** bright green/red caret and mode badge, with a dark
  green/red status background. Dark caret text contrasts with both colours.
  Default Unicode badges are `◆ NORMAL` / `✎ INSERT`, `●` marks modifications,
  and `│` separates details. Below 32 columns, compact `N`/`I` badges leave room
  for warnings. These glyph/palette details remain implementation choices, not
  a requirement for a special font.
- **Terminal bridge:** ordinary cells use `std.term`'s retained framebuffer; a
  bounded local overlay bridges single-codepoint cells to complex graphemes.
  Linux signal descriptors request safe termination without libc handlers.
  Legacy Escape timeout resolution and bracketed-paste events remain investigated
  library gaps, documented in the README rather than silently patched upstream.

This does not settle later facets, split trees, popup composition, repeat
recording, system clipboard, configuration, or language-service APIs.

## 25. Agreed follow-on task queue

- Add `:e <path>` with filename Tab completion, preserving existing buffers and
  reusing already-open files. The user accepted Tab-driven common-prefix/unique
  completion and a selectable ambiguous-match list in the existing message area:
  Up/Down or Tab selects, Enter accepts, Escape dismisses while retaining the
  path. Enter from the ordinary prompt executes the command. Directory matches
  append `/`. The user additionally requested command-name completion, a command
  input anchored at the terminal bottom with matches above, and persistent live
  filtering when typing/deleting in an open list, including one/zero matches.
  A standalone automatically opened folder popup is not part of this implementation.
- The user also agreed the proposed MS2 sequence: shared popup/picker
  infrastructure first exercised by a buffer switcher; then a non-blocking,
  filterable, cancellable file picker; split panes with independent shared-buffer
  views; and explicit repeat recording/playback using section 12's agreed rules.
- Feature scope is agreed, not every binding, matching rule, popup interaction or
  implementation mechanism. Keep unresolved choices explicit before building.
- Track accepted tasks and actual status in `docs/tasks.md` and the single
  agreed-task panel. Do not restore the removed progress/design/feature panels.


## 26. File picker (T4)

T4 implements the agreed non-blocking discovery/filter/open/cancel direction,
using the startup folder and the buffer picker's case-insensitive subsequence
matching. The input and discovery policies below are agreed; pane destinations
are implemented separately in §28. An overlay stack remains future work.

- Normal Space Space and `:files` open the existing generic popup; comma retains
  the buffer list. Space starts a leader sequence with a known-key menu after
  one second, as a bottom overlay (see §27); a second Space works immediately. Escape cancels; unknown keys
  cancel without running an editing command. Insert/prompts retain literal spaces;
  releases and Space repeats do not advance the sequence.
- Search includes relative directory components. Results retain traversal/source
  order; there is no fuzzy score sorting, index, external Git process or library.
- Include hidden and ignored files, as explicitly requested. Follow both file
  and directory symlinks, including targets outside the startup folder. Compare
  device/inode identities of opened directories against the current ancestry
  to stop cycles; distinct non-cyclic aliases are retained. Broken links and
  non-regular objects are omitted.
- Enter revalidates existence/type, then uses normal workspace opening/reuse.
  Success closes the popup and enters Normal. Failure keeps it open with an
  error; merely browsing never reads file contents or changes views/history.
- Escape cancels promptly and preserves the originating interaction state.
  Ctrl+W has no action here. Query editing clears stale matches before another
  Enter can choose them. Reopening starts fresh; empty results remain open.

`src/file_picker.n` owns a Linux child process per scan. The child performs
filesystem traversal and streams NUL-delimited byte paths; the UI owns all
candidate/query/view state. Cancellation closes the pipe and kills the helper,
reaping without a blocking join. A parent-death signal prevents an abandoned
helper after editor termination. Each scan gets a new pipe/storage, so cancelled
results cannot enter a later popup. At most sixteen still-stopping children are
retained; another scan is refused explicitly until they can be reaped.

The parent receives at most 8 KiB and publishes at most 256 paths per simulation
step. Generic `FuzzyPicker` incremental filtering scans at most 512 candidates and stops after 64 KiB
of folded candidate labels per step and restarts on query edits. Buffer filtering remains synchronous and keeps
its existing MRU selection rules. File lists use the full popup width without
filesystem content preview. Existing buffer previews remain unchanged.

Bounds: 32,768 candidates, 64 MiB of path bytes, one million visited entries,
128 directory levels and 4,096-byte paths.
Errors and exceeded limits visibly mark results incomplete instead of implying a
complete scan. Enumeration order is not a stable sorting contract. Revalidation
uses normal Linux pathname operations, not a filesystem transaction against
concurrent writers.


## 27. Space menu presentation and nested-sequence foundation

The agreed presentation is a bottom overlay which slides upwards after the
one-second leader delay. Terminal row animation uses a 180 ms ease-out
and advances from elapsed monotonic time, without blocking input. The full-width
surface has a separating border, coloured key labels, action names and an Escape
hint. It clips on small terminals and does not resize text views, replace the
message area or change caret/selection/scroll state. Composite graphemes beneath
the surface are masked alongside native cells; dismissal restores the editor.

`src/leader_menu.n` declares entries by the sequence after the initial Space,
label and operation. Sequence keys are printable ASCII; labels may be Unicode.
Both dispatch and visible immediate-child hints use those entries. Group entries
select a prefix; the heading includes the group's label and Backspace returns to
its parent. A group entered before the initial delay reveals its menu immediately;
an already-visible menu updates in place. Fast complete sequences do not wait for
animation. Enhanced key labels without paired text, paired character events,
releases and repeats are handled without duplicate dispatch. Other non-menu keys
cancel and are consumed, so Enter cannot insert a newline beneath the overlay.

The Windows submenu and directional actions are now supplied by §28. Matt explicitly clarified that
Space b d was an example for future nested sequences; it is **not** a binding or
an agreed buffer-deletion task. Future groups/actions require agreement before
adding entries. This menu does not implement a general overlay stack or pane UI.


## 28. Pane controls and behaviour (T5)

Normal Space w opens the Windows submenu. The agreed commands are:

| Sequence | Action |
| --- | --- |
| Space w h | Split horizontally: panes side by side |
| Space w v | Split vertically: panes above and below |
| Space w s | Automatically split along the current pane's longest axis |
| Space w c | Close the current pane, keeping its buffer open |
| Space w w | Open the file picker, then automatically split for the chosen file |
| Space h/j/k/l or Space Left/Down/Up/Right | Focus the neighbouring pane in that direction |

Automatic splitting accounts for terminal cells being taller than they are wide.
The h/v/s commands show the current buffer in both panes and focus the new pane.
The panes have independent caret, selection and scrolling state while sharing the
buffer's edits and undo history. Directional focus stays put when no neighbour
exists; it does not wrap. Closing the last pane leaves it open rather than quitting.
Closing a pane never kills its buffer or implicitly saves/discards its contents.

Space w w opens the picker before changing the layout. Capture its originating
pane as the split destination. After a successful selection/open, create the
automatically oriented pane for that file and focus it. Escape leaves the layout
intact, as does an unsuccessful file open. The existing Space Space file opener
keeps its current behaviour.

Implementation choices (initial policy, not a general configuration interface):

- A binary split tree divides space equally, clamped to child minimum sizes, with
  one-cell dividers. New panes are below/right and receive focus. Closing collapses
  the parent into its surviving sibling and focuses that subtree's first leaf.
- Each pane requires 12 columns and 4 rows, including its own status row. There
  are at most 16 live panes. Explicit splits refuse insufficient space. Automatic
  orientation compares width with twice the height, then tries the other axis if
  needed. Hidden view slots and tree slots are reused.
- Neighbours must overlap on the perpendicular axis. Prefer the nearest facing
  edge, then the nearest physical centre (vertical cell distances count twice),
  then stable tree-slot order. Focus never wraps.
- On an undersized terminal, retain the tree and its minimum virtual geometry,
  show the focused pane across the available editor area, and refuse new splits.
  Resizing back restores all panes; directional focus still uses retained geometry.
- The renderer clips each view within its rectangle, offsets composite Unicode
  glyphs, draws only the active caret, and dims inactive status backgrounds.
  The focused pane uses a slightly brighter background for text, blank cells and
  composite glyphs; inactive panes retain the darker workspace colour.
  Status paths inside the startup folder are relative to that folder.
  Bottom messages, completion, file/buffer popups and leader menus remain global.
- Buffer replacement mounts only in the focused pane; an already-visible view is
  copied rather than mounted twice. Killing a buffer rebinds affected panes to
  independent surviving views and preserves the split tree.
- Continuation v4 stores the tree in bounded preorder with unique leaf view IDs;
  the active view identifies focus. Versions 1–3 import as a single pane. Decoding
  rejects duplicate/out-of-range view IDs, invalid kinds and excessive depth/nodes.

Space b d remains an example only, unrelated to closing a pane.


## 29. Pane feedback and clean terminal exit (T5a)

Matt corrected the directional naming after using T5: Space w h arranges panes
side by side; Space w v stacks them above and below. Automatic splitting retains
its physical-axis policy and existing continuation layouts retain their geometry.
Internal split requests name rows/columns to avoid confusing pane arrangement
with the divider's direction. Menu labels describe the resulting arrangement.

The focused pane is slightly brighter (`#1d2532`) than inactive panes (`#171d27`),
including blank space, ordinary text and deferred composite graphemes. Focus
changes recolour the complete pane; selections, matches and caret accents remain
visible. Global message/popup surfaces keep their own palette.

Terminal shutdown must stop keyboard/mouse reporting before giving the terminal
back to the shell. Nerd's Linux std.term cleanup drains queued and in-flight
reports with a 25 ms quiet period and a 100 ms drain bound, then atomically flushes
unread input when restoring terminal mode. ME uses this library behaviour rather
than a local escape/input workaround. PTY checks retain the slave after normal,
forced and signal exits and verify that fresh shell input has no report prefix.


## 30. Ctrl+W pane closing (T5b)

Route ordinary Ctrl+W through the same pane-close operation as Space w c, rather
than deleting a document and rebinding its views. Preserve the closed pane's
buffer, including unsaved work, and leave other panes' buffers, selections and
scrolling intact. Keep the final pane open. Both legacy control bytes and enhanced
key reports work; paired text and releases cannot close a second pane.
The buffer popup retains its selected-buffer deletion and dirty-buffer refusal;
`:kill[!]` remains explicit buffer deletion.


## 31. New unnamed buffer shortcut (T5c)

Ctrl+N creates and focuses a fresh unnamed buffer in the current pane, entering
Insert. It works from Normal and Insert, retains existing buffers and unsaved
work, and preserves other panes. Cancel an active command/search prompt before
creation. Popups, leader menus and confirmation retain their existing input scope.
Legacy byte 0x0e and enhanced Ctrl+N reports have the same action; ignore releases
and suppress associated text so a single press creates one buffer. Counts are
unsupported and consumed with an error. Each new buffer has its own empty
history; normal continuation includes it.


## 32. Explicit repeat implementation (T6)

Normal [ starts a draft, ] finishes and . replays the completed sequence. Brackets
and dots remain literal Insert text. A REC marker appears in the active pane.
The agreed first scope is editing/navigation in the current buffer with one
completed sequence held for the running editor session, reusable in any buffer.
The draft is bound to its original view/document; external text changes cancel
it. A completed sequence is transient, while its grouped undo history persists
through the normal continuation codec.

Initial delivery policies:

- Capture semantic Command invocations, including modes, movement counts,
  selection extension, indentation, Unicode text, deletion, duplication and
  clipboard operations. Own typed text separately from scratch/input storage.
  Copy/cut/paste use the current internal clipboard; searches, prompts, saves,
  file/buffer/pane operations and Space commands are refused during recording.
- Begin playback from the current caret/selection. Execute the original relative
  commands using the destination document's editing policies and retain the
  resulting state/selection. Do not copy absolute source offsets or source text.
  Escape capture represents actual mode/selection changes, excluding message or
  pending-count dismissal. Playback Escape is independent of transient messages.
- Undo during recording disables the corresponding captured edit and subsequent
  navigation, matching history's restored edit caret. Redo reinstates that edit
  and its preceding positioning. Keep the correction's Normal transition, rather
  than capturing an executable undo/redo command. A fresh edit discards the undone
  recipe branch. Refuse undo before the draft's history boundary and redo outside
  its captured edits. Ordinary recording still uses individual history records.
- Nested recording/replay and counts are refused. Starting a draft preserves the
  previous completed sequence; an empty finished draft clears it (`[]`). Ctrl+G
  cancels a draft in either interaction state, preserving edits, state and the
  previous completed sequence. Quitting cancels the draft too, including signal
  handling and :q/:q!/:wq. Failed quit/save attempts still cancel the draft;
  ordinary save/discard policies are unchanged. The command prompt is available
  for these quit commands; recording other : commands is an agreed follow-up.
  There is no implicit last-change capture. Up to 4,096 actions (one reserved for final
  Escape) and 1 MiB of owned typed text bound memory and replay duration.
- Playback executes synchronously in the editor callback with per-edit reports
  adjusting other shared views. Afterwards, collapse the newly appended history
  records into one replacement record spanning the minimal changed byte interval,
  widened to UTF-8 scalar boundaries. Retain invoking caret hints. No storage
  mutation occurs during history grouping, and a navigation-only playback retains
  the redo branch. Existing snapshot versions need no new format.
- Always finish history grouping, including on failure. Return a one-based failing
  step and its reason; completed edits stay as one undo/redo unit. Do not roll back
  completed text or replay clipboard side effects. BOMs and line endings remain
  governed by existing buffer/view rules.

Source: src/repeat.n owns recipes and correction metadata; src/editor.n handles
capture, execution and scope; src/document.n groups history; src/keyboard.n and
src/terminal.n provide bindings and the recording indicator.


## 33. Normal d deletion (T7)

Normal d invokes the existing Delete command: remove the active selection, or
one forward grapheme when there is no selection. Stay in Normal and retain the
internal clipboard. At end of buffer it is harmless; at a line ending it follows
Delete's existing line-joining policy. It is one ordinary undo unit, with existing
shared-view adjustment, recording and grouped playback support. Insert, prompts
and picker queries retain literal d; Ctrl+D retains duplication. Counts use the
existing non-counted command policy. No operator-pending d or dw/dd grammar is
introduced by this alias. The unselected single-d behaviour is superseded by
Matt's later pending-d clarification in §34; immediate selection deletion remains.


## 34. Pending d and counted line deletion (T8)

Matt clarified: d deletes an existing selection immediately. With no selection,
the first d is a pending command; dd deletes the current line and a positive
prefix such as 3dd deletes that many lines, clamped at the end of the buffer.
Show d/3d in the status line while waiting. Escape cancels without edits; invalid
continuations cancel with a message and do not run that key's command. Key
releases do not complete or cancel the prefix. Insert/prompts/picker queries
retain literal d. This supersedes §33's unselected single-d grapheme deletion;
the Delete key retains ordinary forward deletion.

Initial policies: counted dd operates from the caret's line, retains the clipboard
and Normal, and is one edit/undo unit with normal shared-view adjustment. Capture
one semantic DeleteLines(count) operation for recording and replay. Delete complete
line endings; an unterminated final line/trailing empty line also removes its
preceding separator so it disappears as a logical line. Preserve the UTF-8 BOM.
A bare d with an existing selection deletes it immediately; an explicit numeric
prefix starts counted dd even with a selection, using the active caret's line.


## 35. Future file-type mode milestones — agreed direction

Add customisable file-type modes. A mode determines the LSP service, formatter,
syntax highlighting, indentation and related file-type behaviour. These are
file-type systems; Normal/Insert remain interaction states. The earlier choice
to use only the term facet is superseded for this system, while the relationship
with view facets remains a design question.

The first milestone in this programme is **Modes M1: foundation and Markdown**.
This is a new future milestone; it does not rename the completed historical MS1
editor foundation or the delivered MS2 work.

Agreed scope:

- Foundations for recognising a file type, choosing its mode and customising the
  mode's behaviour and provider choices.
- Mode-owned selection/configuration of LSP, formatting, syntax highlighting,
  indentation and related file-type services.
- Markdown as the first supported file-type mode and consumer of that foundation.
- Extra status information, including LF/CRLF line endings and recognised file
  type, while retaining the editor's existing status information.

Before implementation, settle customisation/storage interfaces, file-type
recognition precedence and overrides, mode/facet ownership, provider lifecycle
and concrete providers, the Markdown feature/verification checklist, and status
behaviour for mixed/no line endings or unknown file types. These are open choices,
not implied implementation promises. Later modes milestones are not yet scoped.
This request records future work; it does not implement status or mode services
inside T8's deletion change.
