# Working on ME

## Project and design

ME (Matt's Editor) is a Linux terminal editor written in Nerd. Read
`docs/design.md` for agreed requirements and `docs/questions.md` for unresolved
policies. Keep these documents aligned with decisions; do not promote proposals
to requirements without agreement. Use British spelling throughout
project-authored code, comments, diagnostics, UI, and documentation, preserving
external API/protocol names where required.

Maintain only the single agreed-task PanelCraft panel listed in `docs/dashboard.md`,
backed by `docs/tasks.md`. Do not recreate the removed MS1 progress/design/feature
panels. Track explicitly agreed work, not optional proposals; keep detailed design
and verification evidence in repository documents.

## Nerd implementation

- Use Nerd's standard library, especially `std.term`, rather than another
  terminal framework.
- MS1 is Linux-only. ME/user code must not directly reference libc or introduce
  external-library dependencies. Use Nerd standard-library/syscall facilities.
- Temporary exception: Nerd's existing `nrt.c` runtime dependencies and current
  native toolchain linkage are permitted, so normal Nerd builds/tests may run.
  This is not permission to add direct libc FFI in ME or new library dependencies.
  The user considers libc in compiled Nerd programs a Nerd bug; removing the
  existing runtime dependency is deferred under this explicit exception.
- Read `~/nerd/docs/README.md`, relevant language/reference material, and
  `~/nerd/docs/idiomatic-nerd.md` before implementing unfamiliar constructs.
  Understand and use Nerd's `on`, `for`, and pattern matching naturally.
- Run `nerd format` periodically while editing source, and review the results.
- Prefer declarative, position-explicit interfaces. Buffer implementations use
  traits/`impl` blocks, not a compile-time backend-selection framework.
- Buffer mutations report edits; views own and adjust navigation/selection state.
  Navigation and reads must not reposition a gap buffer's gap.

## Compiler bugs

Confirmed compiler bugs take priority over ME development. Do not work around
compiler bugs here. **Use a dedicated Git worktree of `~/nerd` for all compiler
changes**: another agent is actively changing the main checkout. Do not edit,
reset or build into another agent's checkout. Read the worktree's current README
and applicable instructions and follow its complete workflow. After each fully
validated compiler fix, the user explicitly requires running `just install`
directly in `~/nerd` to update the user-installed compiler and matching modules.
Do not create an installation-only worktree or substitute an isolated install.
Check and report the source checkout's branch/revision; do not silently switch,
reset or merge another agent's branch. Coordinate integration if the validated
fix is not present in that checkout, and coordinate timing if another compiler
installation is active. Once a fix is merged into Nerd's `main`, remove its dedicated
worktree and merged temporary branch. Do not leave completed installation,
review or comparison worktrees behind: the only persistent Nerd checkout should
be `~/nerd`, currently used for libc removal. Before removing an auxiliary
worktree, verify that it is clean, its commits are retained and no process is
using it. Do not remove unmerged work or interfere with another agent's active
checkout. Add regression tests, update relevant
documentation, and follow its validation,
formatting, installation, commit, and push requirements. Do not mistake an
unsupported feature or incorrect ME code for a compiler bug.

## Missing standard-library facilities

Implement recommended missing library functionality locally in ME first. Record
the candidate, rationale, local location, and evaluation status in
`docs/standard-library-candidates.md` for later consideration. Do not introduce
external libraries or automatically modify the standard library for these gaps.

## Task completion and GitHub

After each completed task, run appropriate checks, commit the changes and push
them to the configured GitHub remote, then run `just install` to update
`~/.local/bin/me` with the latest release build. Report the commit/branch and any
push or installation failure. Installation after each task is explicitly
authorised by the user. Never force-push or overwrite unrelated remote history. `origin` is
`git@cthutu.github.com:Cthutu/me.git` (the Cthutu SSH identity), tracking `main`.
The user authorised replacing the legacy GitHub repository with this project;
that replacement is complete. Do not merge the unrelated legacy C tree into
this project. Its local mirror backup is `/home/matt/me-github-backup.git`.

## Development environment

Use a standard Nerd environment with `just` recipes. Prefer underscore-prefixed
generated directories such as `_bin`, `_obj`, and `_tmp`. Keep core editing tests
headless and distinguish terminal integration checks. The runnable entry point
is `main.n`; source lives in `src/`, native tests in `tests/*.n`, PTY checks in
`tests/terminal.py`. Use `just check`, `just test`, `just test-terminal`, and
`just release`. Consult `README.md` and `docs/ms1-progress.md` for current
implementation/verification status; the design documents retain historical
questions and label provisional implementation choices separately.
