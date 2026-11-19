# Project dashboard

PanelCraft space: **ME — MS1**

- Space ID: `e2121672-6f18-4599-a95d-b9be2a1cbca6`
- Progress/blockers panel: `9ed8c59b-f5a9-4bfa-8f40-ce491ce5102e`
- Design reference panel: `4cf60f70-c597-4c1f-b0af-6d5ec14f6d5d`
- Feature tracker panel: `865e618a-534f-40a9-ad39-914b745b9924`

Current implementation and verification evidence: [ms1-progress.md](ms1-progress.md).
The runnable debug/release editor, native test suite and isolated-PTY checks are
local; panels summarise their recorded results, not background execution.

Maintain these panels after meaningful project changes. Read the space and its
panel specifications before updates; use its revision for safe writes. They are
hand-maintained summaries, not automatic local-file monitors. Repository design
and source files remain authoritative. Distinguish draft, type-checked, and
runtime-tested work.

## Current build constraint

Investigation found that the installed Nerd toolchain links executable output
against libc, libm, and libgcc. References in `~/nerd`:

- `docs/toolchain.md`, Host runtime requirements.
- `src/compiler/build/back/back.c`, Linux linker command construction.

Resolved for ME development by explicit user exception: existing `nrt.c`
runtime dependencies and native toolchain linkage are temporarily permitted.
Normal Nerd builds/tests may proceed. ME/user code must not directly reference
libc or add external-library dependencies. The user regards libc involvement in
compiled Nerd programs as a Nerd bug, but defers its removal under this exception.
`std.term` using syscalls does not itself remove runtime/linker dependencies.
