# ME — Matt's Editor

ME is a modal Linux terminal editor written in **Nerd**, using `std.term`.
MS1 is implemented and debug/release regression-tested, providing precise,
Notepad-level text editing with persistent continuation,
shared buffer history, and independent view state. MS2 adds split panes and a
file picker with cancellable discovery under the startup folder. Facets and
language services remain future work.

## Build and run

Requires Linux with procfs mounted, Nerd with the fixes listed in [MS1 progress](docs/ms1-progress.md),
`just`, and an interactive terminal. Python 3 is needed for developer tooling,
not for the editor at runtime. No external terminal library is used.

```sh
just build
just run [filename ...]
just release                  # _bin/me-release
just install                  # release build → ~/.local/bin/me
just check
just test                     # nerd test main.n: colocated native tests
just test-terminal            # real PTY integration checks
just test-all
just format
just clean
```

`just install` creates `~/.local/bin` if needed and installs the release binary
as `me`. Ensure `~/.local/bin` is on your `PATH`; no root privileges are needed.

Recipe aliases: `b` → build, `r` → run, `rel` → release, `c` → check,
`t` → test, `tt` → test-terminal, `ta` → test-all, and `f` → format.
Aliases accept the same arguments as their full names, e.g. `just r README.md`.

Native tests live beside their implementations in `src/*.n` as named
`test "description" { ... }` sections. Helpers and test-only imports live in
bare `test { ... }` sections; normal editor builds exclude them. `just test`
runs `nerd test main.n`, discovering imported-module tests once. A focused run,
for example `nerd test main.n --filter src.editor`, selects the editor tests.
The 1,093 generated Unicode conformance vectors occupy a marked test section in
`src/characters.n`; `just unicode` regenerates it without changing handwritten
code or tests. The separate `tests/terminal.py` runner exercises real processes
and terminal input on debug/release executables.

Builds use the installed `nerd` and its matching installed modules. Generated
outputs live in `_bin`, `_obj` and `_tmp`; `just clean` removes those outputs.
See [toolchain status](docs/ms1-progress.md) for compiler fixes and validation.

```sh
NERD=/path/to/nerd NERD_LIB_PATH=/path/to/mods just build
_bin/me --help
_bin/me [-r] [filename ...]
_bin/me [+filename ...]
```

| Invocation | Startup behaviour |
| --- | --- |
| `me` | Restore this folder's snapshot, or open one empty buffer if none exists |
| `me file1 file2` | Erase the old snapshot, load only those files, display `file1` |
| `me +file1 +file2` | Restore the snapshot, add/reuse those files, display `file1` |
| `me -r` | Erase the snapshot and open one fresh empty buffer |

**Plain filenames and `-r` discard the previous continuation without confirmation,
including unsaved recovered work.** The snapshot is erased after taking the
folder's continuation lock, before opening any files, even if every open fails.
A second instance that cannot take the lock never touches the owner's snapshot.
Failure to erase an owned snapshot is fatal rather than silently resuming it.
Normal quit/checkpointing records the new workspace as usual.

`me file1 file2` creates exactly two buffers for distinct files, with no extra
unnamed buffer. Open the Normal `,` picker to switch. Repeated paths/inode aliases
reuse a buffer. `+filename` retains existing view/history and unrelated recovered
buffers. A nonexistent path stays a named, unwritten buffer until explicit save.

Failed paths report errors without stopping later arguments. The first successful
path is displayed; if all fail, `+filename` keeps recovered buffers open, whereas
fresh startup exits with status 2 when no buffers remain. Do not mix plain and
`+` filenames, or `-r` and `+` filenames: these combinations fail before changing
continuation. Bare `+` is an error. Use `./+name` for a literal leading-plus fresh
filename, or `++name` to add it to continuation. Prefix leading `-` paths with
`./`; unknown options remain errors.

## Editing

Empty buffers start in **Insert**, non-empty files in **Normal**, including
recovered documents. Text input
in Insert replaces a selection, if present. Escape returns to Normal without
throwing the selection away. Normal movement cancels selection; Shift movement
extends it in either state. Normal `h`/`j`/`k`/`l` also move left/down/up/right;
these letters remain literal text in Insert and prompts.

| Keys | Action |
| --- | --- |
| Cursor keys | Grapheme/line navigation |
| `h` / `j` / `k` / `l` | Normal-only left / down / up / right; same movement as arrows |
| Ctrl+Left/Right or Ctrl+H/L | Word movement |
| Home / End | First non-whitespace, then line start / line end |
| Ctrl+Home/End | Document edges |
| Page Up/Down | Visible-page movement |
| Ctrl+Page Up/Down | Paragraph movement |
| Ctrl+Up/Down or Ctrl+K/J | Scroll without moving the caret |
| `i` | Insert, preserving selection |
| `a` / `A` | Insert after character / at line end |
| `I` | Insert at first non-whitespace |
| `o` / `O` | New line below / above; no automatic indentation |
| `w` / `q` | Select whole word / line; repeats extend |
| `y` / `x` / `v` | Copy / cut / paste using the internal typed clipboard |
| `c` | Delete selection and enter Insert; no selection just enters Insert |
| `d` | Delete an existing selection immediately; otherwise begin pending `dd` |
| `dd` / `3dd` | Delete the current line / three lines; retain Normal and clipboard |
| Backspace | Insert: delete backwards or delete selection; Normal: delete selection only |
| Ctrl+Backspace | Insert: delete selection or previous word; Normal: delete selection only; preserve mode |
| Ctrl+D | Duplicate selected lines below (keeping the copy selected), or the current line at the same display column; clear character selections; one undo |
| Ctrl+Z / Ctrl+R | Undo / redo |
| Ctrl+S | Save active document; unnamed opens `:w ` |
| Ctrl+N | New unnamed buffer in the current pane; enter Insert |
| Normal `[` / `]` / `.` | Start recording / finish recording / replay |
| Ctrl+G | Cancel unfinished recording; preserve edits and previous macro |
| `,` | Normal-only buffer picker; Enter switches, Escape cancels |
| Normal Space Space / `:files` | Open files; hold after the first Space for the key menu |
| Space w h / v / s | Split side by side / above/below / automatically |
| Space w c | Close the pane, keeping its buffer; keep the last pane open |
| Space w w | Pick a file, then open it in a new automatic split |
| Space h/j/k/l or Space + cursor key | Focus the neighbouring pane without wrapping |
| Ctrl+W | Close the current pane; in the buffer picker, remove the highlighted saved buffer |

Only `i` preserves selection on Insert entry; other entry commands clear it.
Ctrl-bound editing commands enter Normal even on failure/no-op; Ctrl+N starts
a fresh unnamed buffer in Insert, retaining all existing work. Ctrl navigation
preserves state. Each terminal character event, deletion, paste and duplicate is its own
undo operation. Undo/redo clears selection and restores the operation's before/after
caret, rather than replaying subsequent navigation. Older history without caret
hints falls back to the start of the affected edit.

Normal `[` starts a repeat recording; perform edits/navigation, leave Insert with
Escape, then `]` finishes. The active pane shows `REC`. `.` runs the completed
sequence from the current caret/selection. Brackets and dots remain text in Insert.
For example, `[iHello`, Escape, `]` records insertion of `Hello`; moving elsewhere
and pressing `.` inserts it there.

Recording retains ordinary per-operation undo. Undo removes its edit and the
subsequent navigation from the recipe; redo reinstates that edit and its preceding
positioning. Undo cannot cross the recording's start. A new edit discards the
undone branch. Playback is one undo/redo unit, including after restart. On failure,
completed edits stay in one undoable unit and the message identifies the step.

The first version records current-buffer editing, selection, navigation and mode
changes. Copy/cut/paste use the current internal clipboard. Search, file commands,
saving, buffer/pane changes and Space commands are refused while recording; finish
with `]` first. Navigation/editing uses the destination buffer's normal policies,
including line endings. Final state/selection follows the recorded commands.
There is one completed recording per running session, reusable in another buffer;
it is not saved in continuation. Starting a new recording retains the previous
one until a recording finishes. `[]` clears the completed macro. Ctrl+G cancels
the draft in Normal or Insert, keeping edits, interaction state and the previous
macro. Quitting also cancels the draft; `:q`, `:q!` and `:wq` retain their usual
save/discard behaviour. Other `:` commands remain unavailable during recording
until the agreed command-playback follow-up. Nested recording/replay and counted
record/replay commands are unsupported; `.` has no implicit last-change action.
Recordings are bounded to 4,096 actions (including a reserved final Escape) and
1 MiB of typed text. External changes to the recording buffer cancel the draft.

Ctrl+H/L move by word and Ctrl+J/K scroll down/up, matching Ctrl+arrows in
Normal and Insert. Normal counts and Shift selection extension follow the same
rules as the corresponding arrows. These letter shortcuts require enhanced
keyboard reports; key releases are ignored and repeats repeat the movement.
In pickers, Ctrl+J/K select rows and Ctrl+H/L move the query caret, just like
the corresponding modified arrows.

Legacy bytes `0x08` and `0x7f` both mean ordinary Backspace. In Insert it deletes
backwards, or removes the selection; in Normal it removes only a selection and is
otherwise a no-op. Enhanced Ctrl+Backspace retains word deletion in Insert.
Backspace preserves the interaction state so typing can continue in Insert.
Legacy Ctrl+H/Ctrl+Backspace remappings cannot be distinguished from ordinary
Backspace without configuration or enhanced keyboard reporting.

Positive Normal counts prefix arrows, `h`/`j`/`k`/`l`, word/paragraph/page
movement and `w`/`q`. For example, `3j` moves down three lines and `3q` selects
three lines; `qqq` also selects three lines.
A count also prefixes `dd` for line deletion. Pending `d` waits for its second
`d`; Escape cancels, and an invalid continuation cancels with an error.
Unsupported combinations report an error and consume the count. `:120` jumps to
line 120's first non-whitespace; out-of-range lines are clamped. Vertical motion
retains a preferred display-cell column through shorter lines. Intentional
scroll-away is preserved until caret motion or editing reveals it.

In document text, Tab inserts four spaces by default, with a small existing-indentation heuristic.
At leading/trailing whitespace, Backspace removes a matching Tab-sized run of
spaces; elsewhere it removes one grapheme. Existing tabs are never converted.
Words are Unicode letters/decimal digits/underscore; punctuation forms separate
runs. Line selections include their existing ending. Linewise paste without a
selection inserts below; with a selection, paste replaces precisely that range.

## Buffer picker

Press **`,` in Normal** to open a large popup. Its top search bar filters paths
by **case-insensitive ordered subsequence**: `btt` matches `BetaTest.n`. Matching
uses Unicode 16 default full case folding, without accent removal or Unicode
normalisation. Results retain **most-recent-access order**, not fuzzy scores:
current buffer first, then previously accessed buffers. The **second row starts
selected**, so `,<Enter>` switches straight to the previous buffer. With only one
buffer, that row is selected instead.

- **Up/Down** selects; **Page Up/Down** moves by a page. Releases do not move it.
- **Enter** chooses immediately; **Escape** cancels without switching or changing
  the originating buffer's caret/selection. Enter with no matches does nothing.
- Typing edits the query, including Normal-command letters and commas. Backspace,
  Delete, Left/Right and Home/End edit/navigate it; the query is bounded at 4,096
  bytes. The list stays open with one or zero matches.
- `>` marks the current buffer and `*` unsaved work. Startup-folder paths are
  shown relative to it; other paths remain absolute. Display sanitisation never
  changes the underlying filename/identity, including non-UTF-8/control bytes.
- Access order survives continuation; accepting a buffer updates it. Cancelling
  or merely moving the selection does not. Each buffer keeps its own view/history.

**Ctrl+W closes the current pane, keeping its buffer available.** Other panes
retain their buffers, carets and scrolling. Unsaved work is retained; the last
pane stays open. This also works from Insert and enters Normal.

Inside the buffer picker, **Ctrl+W removes the highlighted saved buffer**.
With no matches it does nothing. The picker stays open after a close or refusal,
retaining the query/caret and selecting the same result row (or the last remaining
row). Closing the final match leaves the query open with no matches.
Unsaved/new/missing work reports an error without writing or discarding it.
Closing another buffer preserves the active buffer; closing the active one
focuses the most recent survivor. Closing the last one leaves a fresh empty buffer.
`:kill`/`:kill!` remain available; `:kill!` is explicit discard.
Comma remains literal in Insert and command/search prompts.

A **read-only preview on the right** follows the highlighted buffer without
switching it. It shows the buffer's current text, including unsaved edits, from
the first line; long lines/extra rows are clipped, not wrapped. Tabs and Unicode
use the editor's display widths. No-match queries clear the preview. Narrow or
very short terminals fall back to the full-width list; widening restores preview.
Previewing never changes carets, selections, history or MRU order and does no I/O.

The owning fuzzy-list model, popup layout and renderer are reusable. This first
consumer does not implement asynchronous file discovery, an overlay stack or
split-pane focus routing.

## File picker

**Space Space** in Normal, or **`:files`**, opens a workspace-wide file list
rooted at the editor's startup folder. It opens immediately while discovery runs
separately. Type to filter using the buffer picker's Unicode case-insensitive
ordered subsequence matching, including directory components. Results arrive in
filesystem traversal order, without fuzzy score sorting. Up/Down and Page Up/Down
select; Left/Right/Home/End, Backspace and Delete edit the query.

**Enter** opens the selected existing regular file or focuses its existing buffer,
including inode aliases, without discarding other work. It dismisses the picker
on success; a disappeared/non-regular/unreadable/invalid-content candidate reports
an error and leaves it open. **Escape** cancels discovery and preserves the
originating buffer, caret, selection, scroll and editing mode. Query edits clear
old matches immediately; Enter with no current match does nothing. Ctrl+W has no
action in the file picker. File contents are not previewed during discovery.

Space starts a leader sequence in Normal. After one second, a bordered menu
slides up over the bottom of the editor, with coloured key labels and action
names. The slide takes 180 ms. It overlays the text without resizing the view or
replacing messages. Escape closes it and reveals the editor underneath.
The second Space works immediately, without waiting for the menu. Unknown keys
cancel the sequence without executing an editing command. Spaces remain ordinary
text in Insert and prompts. Enhanced key releases and held-key repeats do not
invoke menu commands. Menu definitions support future nested groups, with path
headings and Backspace to return to the parent. Space w opens the Windows
submenu; directional focus also works directly after Space.

Discovery includes hidden names and files excluded by `.gitignore`; no ignore
rules are applied. Symlinks to files and directories are followed. Each opened
directory's device/inode identity is checked against its current ancestry, so
cycles are skipped while distinct aliases remain discoverable. Links can lead
outside the startup folder. Broken links and special objects are omitted.
Raw Linux filename bytes are retained; only display labels are sanitised.
Opening the picker again starts a fresh scan.

Discovery and filtering use bounded batches. A scan is capped at 32,768 candidates;
unreadable directories or other discovery limits explicitly mark the list
**incomplete** and show an error. Available results remain usable.
Cancellation also works while the discovery helper is blocked; it never waits for
filesystem traversal to finish before returning input to the editor.

## Panes

In Normal, **Space w** opens the Windows submenu. **h** creates panes side by
side; **v** stacks panes above and below; **s** chooses automatically using the
pane's physical proportions (one cell is treated as twice as tall as wide).
The new pane appears below/right, is focused, and shows the same buffer with an
independent caret, selection and scroll position. Edits and undo history are shared.

**Space h/j/k/l**, or **Space** followed by a cursor key, focuses a neighbour.
There is no wrapping at an edge. **Space w c** closes the focused pane without
killing or saving its buffer, even with unsaved work. The final pane stays open.

**Space w w** opens the file picker first. Successful opening creates and focuses
an automatic split for that file; Escape or an open failure preserves the layout.
Space Space opens a file in the current pane. Buffer switching also affects only
the current pane, with an independent view when that buffer is visible elsewhere.

Splits divide available space equally, allowing one cell for a divider. Panes have
a status row and require at least 12 columns by 4 rows; at most 16 panes are open.
A split that cannot fit is refused. Automatic splits try the other orientation
when needed. When resizing leaves too little space, only the focused pane is
shown; enlarging the terminal restores the retained tree. Directional focus uses
that retained geometry. Layout, focus and each view's positions survive continuation.
Status paths inside the startup folder are shown relative to it, keeping filenames
visible in narrow panes. The focused pane has a slightly brighter background
across its text and blank space; other panes keep the darker background. The status bars, shared bottom
messages and popups stay distinct.

## Search and replacement

- `/term` searches forwards; `?term` backwards, literally and case-sensitively.
- `//term` searches forwards from the document beginning; `??term` searches
  backwards from its end. These leading origin prefixes are not replacement
  separators. A later slash can still introduce replacement: `//old/new`.
- Escape literal slashes in forward queries, e.g. `/src\/old` searches for
  `src/old`, and `/\/name` finds `/name`. Use `\\` for a literal backslash.
- Typing previews and highlights visible matches, wrapping at document edges.
- Enter keeps the match-start caret without selection/highlights. Escape
  restores the pre-search caret/scroll and clears selection. Arrows cancel the
  preview before moving from that restored position.
- `n` always selects the next match; `p` always selects the previous one. The
  active selection has a different background from passive matches. Repeats
  skip the active occurrence. Ordinary movement/editing clears highlights.
- Confirmed and cancelled terms are remembered; an empty prompt reuses the last
  term. `c`, then typing, can replace the selected occurrence.
- **`/old/new` replaces all non-overlapping occurrences in the whole buffer.**
  An unescaped slash after the search term switches the prompt to replacement,
  after parsing the optional leading `//` origin prefix.
  Press Enter to apply; typing/preview never changes text, and Escape cancels.
  An optional trailing slash is accepted: `/old/new/`. `/old/` deletes all matches.
- **`/old/new/c` confirms each original match:** Y replaces, N skips, A replaces
  all remaining matches, and Escape stops while keeping approved edits.
  Answers are case-insensitive; other input (including save/undo) is ignored
  until confirmation finishes or is stopped. Matches are highlighted/revealed.
- A complete or stopped replacement is **one undo operation**, including approved
  edits checkpointed during confirmation. Ctrl+Z restores the pre-replacement
  caret; redo restores the final caret. Saving still requires Ctrl+S.
- `\/` and `\\` escape slashes/backslashes in either field. Other escapes such as
  `\n` are literal, not newline conversion requests. Empty search terms are
  rejected; replacement text is not recursively searched. Identical old/new
  text reports no change. The `replace` command and `g` flag have been removed.

## Keyboard diagnostics

Run **`:keys`** to inspect the terminal's keyboard reporting. The diagnostic view
shows the actual Kitty flags (including a valid zero reply), whether probing has
completed, and reliable physical-key/release/modifier/associated-text capabilities.
It retains the six most recent decoded key/text events, including key name,
press/repeat/release, modifier bits and Ctrl/Shift/Alt, and decimal character/label
codepoints. These are decoded events, **not a raw byte capture**. Outside
diagnostics, releases do not move the caret or execute commands; held-key repeat
events still work.

Press Ctrl+H, then Ctrl+Backspace. Enhanced input can show `H` and `Backspace`
with Ctrl separately. Legacy byte `0x08` is explicitly labelled ambiguous;
protocol support cannot undo terminal bindings that map both combinations to the
same bytes. The view captures keys without editing/saving. **Escape** closes it;
Alt+Page Up/Down scroll long output, including on narrow terminals. The trace is
bounded in memory, cleared on reopening, and never saved to the workspace.

No Kitty reply before the following Device Attributes reply means the current
terminal/multiplexer path did not acknowledge Kitty reporting. With no response
at all, probing remains pending and input uses conservative legacy capabilities;
we do not infer lack of support from a timeout or `$TERM`. This is Kitty/native
capability reporting, not detection of every terminal-specific protocol.

## Files and continuation

| Command | Behaviour |
| --- | --- |
| `:keys` | Inspect keyboard protocol/capabilities and decoded key events; Escape closes |
| `:files` | Discover/filter files below the startup folder and open a selection |
| `:e path` | Open/create a file-backed buffer, or focus its existing buffer without discarding other work |
| `:w` | Save active document; unchanged existing files are not written |
| `:ww` | Force a write, but do not bypass external conflicts |
| `:w!` | Force writing including conflict overwrite |
| `:w filename` | Write and reassociate; confirm an existing different target with Y/N |
| `:wq` | Save all modified documents and quit only on success |
| `:q` | Quit only when every buffer is saved; checkpoint layout and undo history |
| `:q!` | Remove every unsaved buffer, including recovered work, and quit |
| `:buffers` | List retained workspace documents |
| `:buffer N` | Focus a retained document's view in the single pane |
| `:kill` | Kill active buffer and all its views; refuse unsaved work |
| `:kill!` | Kill active buffer and all its views, discarding unsaved work |

### Command and filename completion

Before a command's separating space, **Tab** completes command names. `:bu`
offers `buffer` / `buffers`; Tab at an empty `:`
prompt lists all supported names. Acceptance never executes the command.

Saving as a different existing file asks `File <file> exists - save? (Y/N)`.
Y saves and associates the buffer with that path; N or Escape cancels without
changing the buffer path or target. Relative, absolute and home-relative paths
follow the same rules. Approval is rejected if the target changes or disappears;
retry after reviewing it. `:ww filename` also asks; `:w! filename` explicitly
forces overwriting. Saving to the current backing file keeps its existing
external-change conflict checks.

After the separating space in `:e`, `:w`, `:w!` and `:ww`, **Tab** completes
the path at the end of the prompt. For example, type `:e src/ter` and press Tab. Relative paths use the
startup folder; absolute paths also work. Unique matches complete immediately;
directories append `/` so you can continue into them.

Ambiguous matches expand their common prefix and open a list in the existing
bottom message area **above the command-entry line, which stays on the terminal's
last row**. **Up/Down** or further **Tab** changes the selected match;
**Enter** accepts it into the prompt **without executing the command**. Press
Enter again to open/save. **Escape** dismisses only the list, retaining your
path; another Escape cancels the prompt. While the list is open, typing and
Backspace keep filtering it, even with one or zero matches. Filtering does not
silently expand your typed query; Enter accepts a valid match, and with no matches
it does nothing. Deletion can widen results again. Moving the prompt caret closes
the list. Entering non-file arguments (such as the number in `:buffer N`) also
ends command-name completion. No-match/directory errors leave files intact.

Paths preserve bytes after the first separating space: spaces need no quotes,
and trailing spaces are significant. A complete leading `~` or `~/` expands from
`HOME` for opening, saving and completion: `:e ~/.we<Tab>` can complete
`~/.wezterm.lua`. Tab after bare `~` adds `/` first. The prompt retains `~/` rather
than substituting the absolute home path. An unset/non-absolute `HOME` produces an
error without creating or saving a file. There is no shell quoting, variable
expansion or `~user` lookup; other tildes are literal. Use `./~` or `./~/file` for
a literal leading tilde filename/directory (completion supplies that prefix when
necessary). Symlinks and `..` remain resolved by Linux, not lexically collapsed.
Matches are case-sensitive, ordered by filename bytes, and hidden
entries appear only when the current component begins with `.`. Accessible
symlink targets are followed for file/directory classification; non-regular
objects and inaccessible/broken links are not suggested. Filenames selected by
completion retain control/non-UTF-8 bytes internally, with safe single-line
presentation. Opening filename completion or changing its directory builds a
bounded synchronous snapshot; subsequent same-directory query filtering uses
that snapshot without more filesystem reads. Close/reopen the list to refresh
changed directory contents. Discovery is capped at 65,536 directory entries and
4,096 matches; an exceeded limit reports an error, not incomplete results.
The future non-blocking file picker is separate work.

### File fidelity

UTF-8 is required for editable **content**. Invalid/unsupported encodings are
refused without rewriting the file. A UTF-8 BOM is retained but hidden/protected
from ordinary editing. Existing tabs, mixed LF/CRLF endings and absent final
newlines are preserved. New endings use a local/majority inference, with LF as
the fallback. There is no formatting, automatic indentation or conversion.
Linux byte filenames are retained exactly and sanitised only for display.
Dot segments are resolved by Linux, not lexically collapsed across symlinks.

Saving uses exclusive same-directory temporaries, file/directory flushing and
atomic replacement. Existing symlinks are followed, not replaced. Ownership,
mode, ACLs and extended attributes are copied; inability to preserve required
metadata fails rather than silently dropping it. A dangling symlink is refused.
Bytes and file identity are rechecked near commit. As with ordinary rename-based
editors, an uncooperative writer still has a final check/rename race; this is not
a transactional filesystem or an advisory lock on other programs.

External files are polled at 250 ms, using two matching metadata samples before
reload (normally about 0.5–0.75 seconds). Unedited content reloads as one undoable
edit, retaining history and updating the known disk content. Edited content
produces a conflict. Deletion retains text/path and marks missing; only an
explicit save recreates it. Reappearance uses the same reload/conflict policy.

Continuation lives in `~/.config/me/<folder-hash>/`, keyed by the startup folder
and verified against its full path. Checkpoints include document content/history,
paths, view positions/scroll/preferred columns and active surface. Startup
normalises interaction state as above; prompts are not resumed. Typing is debounced by 400 ms, with an attempted
maximum two-second interval during continuous edits. `:q` refuses any unsaved
buffer, including hidden and unnamed buffers; use `:wq` to save everything or
`:q!` to discard. A clean quit checkpoints synchronously. Handled signals still
checkpoint unsaved work for recovery. Prompts, messages, search and clipboard are
transient.

Snapshots now use format **v3**, retaining v2 undo/redo caret hints and adding
validated buffer access order. Existing v1/v2 snapshots are imported without
dropping content/history; the next checkpoint upgrades them to v3. Legacy access
order starts with the restored active buffer, followed by document order because
older snapshots did not record recency. Older ME binaries cannot read v3.

`:q!` removes every buffer with unsaved work entirely, including recovered,
unnamed, modified file-backed and missing-file buffers. It does not reset them to
saved contents. Saved unchanged buffers survive; no backing file is deleted or
reverted. The next continuation omits the removed buffers and their history.

`:kill` removes the active buffer only, refusing unsaved work unless `!` is used.
All views of that buffer are removed; affected panes mount another surviving
view. If none remain, an empty default is created. Surviving buffer order is
preserved. Killing is not a text undo operation; backing files remain untouched.
A persisting session checkpoints the removal immediately, reporting failures
and retrying rather than pretending the continuation was updated.

Only one process per startup folder owns continuation. A second starts empty,
warns, and neither reads nor writes snapshots. There, `:q` refuses unsaved work;
`:wq` or explicit `:q!` is required. Recovery/checkpoint failures remain indicated
and unsafe normal quit is refused. A damaged snapshot is retained, not overwritten
by a fallback session. SIGTERM/SIGHUP/SIGINT request a safe checkpoint/exit;
SIGKILL recovery is limited to the last successful checkpoint. Normal quit,
`:q!` and handled-signal shutdowns disable input reporting and clear pending
reports before restoring the terminal to the shell.

## Display, limits and development

The gutter is absolute in Insert, relative in Normal/commands, with an absolute
current line. The current line number is gold on a highlighted gutter background;
other numbers remain muted. Normal uses a **green cursor and status bar**;
Insert uses **red**. The status has contrasting `◆ NORMAL` / `✎ INSERT` badges,
`│`-separated details and a `●` modified marker, using ordinary Unicode rather
than special-font glyphs. Narrow terminals use compact `N` / `I` badges to leave
room for warnings. Cursor text stays dark and legible on either accent colour.
Complex graphemes use the same RGB palette as ordinary cells.

Horizontal scrolling is initially current-line-only. Messages
wrap/grow to half the terminal; Alt+Page Up/Down scroll overflow. Escape dismisses
messages without changing caret/selection. `!C` marks checkpoint failure, `~` a
non-persisting session, `!conflict` and `?missing` backing-file conditions.

MS1 originally omitted the file picker and pane controls delivered above. Mouse
support, desktop clipboard integration, repeat recording, configuration and
language intelligence remain unimplemented.
Enter Insert before pasting from a terminal/desktop: Nerd does not yet expose
bracketed-paste boundaries. In legacy keyboard mode, the current Linux `std.term`
backend rounds its Escape ambiguity timeout to a 100 ms termios tick; enhanced
keyboard terminals can disambiguate Escape. Unicode width follows Unicode 16
with narrow ambiguous characters; terminal/font conventions can still differ.

A small local compositor bridges `std.term`'s single-codepoint cells to full
Unicode graphemes; ordinary cells use the retained framebuffer. Complex glyph
updates arrive on the following simulation step. Document projections/indexes
are cached between edits but currently rebuilt on mutation: this is **not** a
large-file scalability claim.

See [MS1 progress and verification](docs/ms1-progress.md),
[design agreements](docs/design.md), [open design questions](docs/questions.md),
and [standard-library candidates](docs/standard-library-candidates.md).
`python3 build/benchmark.py --binary _bin/me-release` measures PTY delivery latency.
`just unicode` fetches checksum-pinned build inputs and regenerates the Unicode
16 tables and 1,093 official grapheme vectors. Unicode data is covered by
[its own licence](LICENSE-UNICODE.txt).


Future agreed milestone: **Modes M1 — foundation and Markdown**. File-type modes
will determine LSP, formatting, syntax highlighting, indentation and related
behaviour, with customisable provider choices. The first milestone includes the
mode foundation, Markdown support and status-line LF/CRLF/recognised file-type
information. See [design §35](docs/design.md#35-future-file-type-mode-milestones--agreed-direction)
and [agreed tasks](docs/tasks.md); concrete providers and feature details remain
open before implementation.
