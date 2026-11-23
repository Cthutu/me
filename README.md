# ME — Matt's Editor

ME is a modal Linux terminal editor written in **Nerd**, using `std.term`.
MS1 is implemented and debug/release regression-tested, providing precise,
Notepad-level text editing with persistent continuation,
shared buffer history, and independent view state. One pane is provided; pane
management, facets and language services are future work.

## Build and run

Requires Linux with procfs mounted, Nerd with the fixes listed in [MS1 progress](docs/ms1-progress.md),
`just`, and an interactive terminal. Python 3 is needed for developer tooling,
not for the editor at runtime. No external terminal library is used.

```sh
just build
just run [filename]
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

The default compiler is installed `nerd`. Override `NERD` and `NERD_LIB_PATH` to
use an isolated compiler/modules pair. An ignored local `.env` currently selects
`_tools/nerd` and `_tools/mods`, containing the tested Nerd fixes; the shared Nerd
checkout remains on the other agent's branch; see
[toolchain status](docs/ms1-progress.md#nerd-fixes--ten-completed) for the distinct
user installation and validated private compiler. Generated outputs live in
`_bin`, `_obj` and `_tmp`; `just clean` leaves compiler overrides alone.

```sh
NERD=/path/to/nerd NERD_LIB_PATH=/path/to/mods just build
_bin/me --help
_bin/me [-r] [filename]
```

No filename restores this startup folder's workspace, or opens an empty buffer.
A filename restores first, then opens/focuses that path. A nonexistent path is a
new named buffer; it is not created until explicitly saved. `-r` starts fresh,
without confirmation; bare `-r` opens an empty buffer. MS1 accepts one CLI path.
A failed reset/open does not overwrite the prior recovery snapshot.

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
| Ctrl+Left/Right | Word movement |
| Home / End | First non-whitespace, then line start / line end |
| Ctrl+Home/End | Document edges |
| Page Up/Down | Visible-page movement |
| Ctrl+Page Up/Down | Paragraph movement |
| Ctrl+Up/Down | Scroll without moving the caret |
| `i` | Insert, preserving selection |
| `a` / `A` | Insert after character / at line end |
| `I` | Insert at first non-whitespace |
| `o` / `O` | New line below / above; no automatic indentation |
| `w` / `q` | Select whole word / line; repeats extend |
| `y` / `x` / `v` | Copy / cut / paste using the internal typed clipboard |
| `c` | Delete selection and enter Insert; no selection just enters Insert |
| Ctrl+Backspace | Delete the selection, or back to the previous Ctrl+Left word boundary; one undo; enter Normal |
| Ctrl+D | Duplicate selected lines below (keeping the copy selected), or the current line at the same display column; clear character selections; one undo |
| Ctrl+Z / Ctrl+R | Undo / redo |
| Ctrl+S | Save active document; unnamed opens `:w ` |

Only `i` preserves selection on Insert entry; other entry commands clear it.
Ctrl-bound editing commands enter Normal even on failure/no-op. Ctrl navigation
preserves state. Each terminal character event, deletion, paste and duplicate is its own
undo operation. Undo/redo clears selection and restores the operation's before/after
caret, rather than replaying subsequent navigation. Older history without caret
hints falls back to the start of the affected edit.

Legacy byte `0x08` (Ctrl+H), used by WezTerm for Ctrl+Backspace, performs
word deletion too. Byte `0x7f` remains ordinary Backspace. Terminals sending
`0x08` for plain Backspace cannot distinguish it from this shortcut without
configuration or enhanced keyboard reporting.

Positive Normal counts prefix arrows, `h`/`j`/`k`/`l`, word/paragraph/page
movement and `w`/`q`. For example, `3j` moves down three lines and `3q` selects
three lines; `qqq` also selects three lines.
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

## Files and continuation

| Command | Behaviour |
| --- | --- |
| `:e path` | Open/create a file-backed buffer, or focus its existing buffer without discarding other work |
| `:w` | Save active document; unchanged existing files are not written |
| `:ww` | Force a write, but do not bypass external conflicts |
| `:w!` | Force writing including conflict overwrite |
| `:w filename` | Write and reassociate; a different existing target needs `!` |
| `:wq` | Save all modified documents and quit only on success |
| `:q` | Quit, checkpointing unsaved/unnamed work and undo history |
| `:q!` | Remove every unsaved buffer, including recovered work, and quit |
| `:buffers` | List retained workspace documents |
| `:buffer N` | Focus a retained document's view in the single pane |
| `:kill` | Kill active buffer and all its views; refuse unsaved work |
| `:kill!` | Kill active buffer and all its views, discarding unsaved work |

### Command and filename completion

Before a command's separating space, **Tab** completes command names. `:bu`
offers `buffer` / `buffers`; Tab at an empty `:`
prompt lists all supported names. Acceptance never executes the command.

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

Paths are literal bytes after the first separating space: spaces need no quotes,
and trailing spaces are significant. There is no shell quoting, tilde or variable
expansion. Matches are case-sensitive, ordered by filename bytes, and hidden
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
maximum two-second interval during continuous edits; normal quit checkpoints
synchronously. Prompts, messages, search and clipboard are transient.

Snapshots now use format v2 to preserve undo/redo caret hints. Existing v1
snapshots are imported without dropping their content or history; the next
checkpoint writes v2. Older ME binaries cannot read the new format.

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
SIGKILL recovery is limited to the last successful checkpoint.

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

MS1 intentionally omits mouse support, desktop clipboard integration, a file
picker, split-pane UI, repeat recording, configuration and language intelligence.
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
