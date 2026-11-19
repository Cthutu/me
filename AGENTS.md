# Working on ME

## Project and design

ME (Matt's Editor) is a Linux terminal editor written in Nerd. Read
`docs/design.md` for agreed requirements and `docs/questions.md` for unresolved
policies. Keep these documents aligned with decisions; do not promote proposals
to requirements without agreement. Use British spelling throughout
project-authored code, comments, diagnostics, UI, and documentation, preserving
external API/protocol names where required.

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
reset, build into, or install over shared compiler state without coordination.
Read the worktree's current README and applicable instructions and follow its
complete workflow. Once a fix is merged into Nerd's `main`, remove its dedicated
worktree and merged temporary branch. Do not remove unmerged work or interfere
with another agent's checkout. Add regression tests, update relevant
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
them to the configured GitHub remote. Report the commit/branch or any push
failure. Never force-push or overwrite unrelated remote history. `origin` is
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
