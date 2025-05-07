# Matt's Editor - Development Roadmap

This document outlines the development plan for Matt's Editor, a terminal-based,
modal text editor written in C23 with British spelling conventions. The
development is divided into phases, each consisting of several commits that add
specific functionality.

This document will grow and be used to drive the development of the editor.

## Platform modularisation

The design of the codebase will consist of a platform-specific part that calls
into a platform-agnostic part.  The main loop that fetches input from the user
and outputs the results to the terminal will be in the platform layer.  This
main loop will call into the `editor_main` function that is platform-agnostic
with a platform-agnostic struct that details platform state such as terminal
size, buffer for the characters and their colours, input and any platform
interfaces (via function pointers) such as file I/O.  This function should
return a command to relay back information to the platform layer.  Commands
could be:

- Quit the application
- Call a process
- etc.

Each platform's `main` function will therefore be defined in a file named after
the platform, e.g. `linux_main.c`, `win32_main.c` etc.

## Coding style

- All functions shall be named in the style `<module>_<name>`.
- British spelling should be used in any naming (e.g. `colour`, not `color`).
- Use `#pragma once` for header files.
- We should define integer types and call them `i8`, `i16` etc. for signed and
  `u8`, `u16` etc. for unsigned.  Similarly, use `f32` etc. for floats.
- Try to keep memory allocation to a minimum.
- Do not use 3rd party libraries.

## Phases

### Phase 1 - Terminal management

This phase should handle the terminal by:

- Switching to alternative mode.
- Uses raw mode.
- Reading the terminal size.
- Control the cursor.
- Efficiently render to the terminal using double buffering to determine what
  has changed when the buffer is passed to the `editor_main` function.
- Read the keyboard and map to local characters, but also keep track of "alt",
  "shift" and "ctrl" keys.
- Call into `editor_main` (which will just return the quit command if ESCAPE is
  pressed).

Additionally, we will need a build environment that uses `clang`.

### Phase 2 - Advanced drawing commands

The next step is to support advanced drawing commands such as:

- Rendering text (UTF-8 supported) to the buffer.
- Rendering an array of Unicode characters and their colours to the buffer.
- Colour an area of the screen by drawing the colour only leaving the characters
  in the buffer untouched.
- Advanced layout calculations using constraints.

From this we can design immediate mode UI elements such as scroll areas, labels
etc.
