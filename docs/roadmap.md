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
- Generated folders (build, bin, etc.) should be prefixed with an underscore (e.g., `_build`, `_bin`)
  to easily distinguish them from source code directories.

## Phases

### [❓] Phase 1 - Terminal management

This phase should handle the terminal by:

- Switching to alternative mode.
- Uses raw mode.
- Reading the terminal size.
- Control the cursor.
- Efficiently render to the terminal using double buffering to determine what
  has changed when the buffer is passed to the `editor_main` function.
- Read the keyboard and map to local characters, but also keep track of "Alt",
  "Shift" and "Ctrl" keys.
- Call into `editor_main` (which will just return the quit command if ESCAPE is
  pressed).

#### Expected Commits for Phase 1:

- [✅] **Project setup**: Initial repository structure, build system, and basic
   platform detection
   - Create Makefile with C23 support
   - Set up initial project directory structure
   - Add `.gitignore` file for build artifacts
   - Create stub README.md

- [ ] **Terminal initialisation**: Implement terminal setup and teardown routines
   - Terminal raw mode implementation
   - Alternative screen buffer handling
   - Signal handling for graceful exit
   - Basic terminal information retrieval (size, capabilities)

- [ ] **Platform layer**: Implement the platform abstraction layer
   - Create platform-specific header files
   - Implement platform detection
   - Set up Linux-specific implementation first
   - Create platform-agnostic interface

- [ ] **Input handling**: Implement keyboard input system
   - Detect and map special keys (arrow keys, function keys)
   - Track modifier keys (Alt, Shift, Ctrl)
   - Convert keyboard events to editor commands
   - Handle UTF-8 input sequences

- [ ] **Screen buffer**: Implement double buffering system
   - Create screen buffer data structure
   - Implement efficient buffer comparison for minimal updates
   - Add cursor positioning functions
   - Basic text rendering functions

- [ ] **Editor main loop**: Create the platform-agnostic main function
   - Initial `editor_main` implementation
   - Simple command interface between platform and editor layers
   - Basic quit on ESCAPE functionality
   - Event processing framework

### [ ] Phase 2 - Advanced drawing commands

The next step is to support advanced drawing commands such as:

- Rendering text (UTF-8 supported) to the buffer.
- Rendering an array of Unicode characters and their colours to the buffer.
- Colour an area of the screen by drawing the colour only leaving the characters
  in the buffer untouched.
- Advanced layout calculations using constraints.

From this we can design immediate mode UI elements such as scroll areas, labels
etc.

#### Expected Commits for Phase 2:

- [ ] **UTF-8 text rendering**: Implement Unicode text support
   - UTF-8 string parsing and validation
   - Unicode character rendering
   - Handle combining characters and variable-width glyphs
   - Basic text measurement functions

- [ ] **Colour support**: Add colour management
   - Define colour palette interface
   - Implement 256-colour and RGB colour support if available
   - Add background and foreground colour functions
   - Colour attribute system (bold, italic, underline, etc.)

- [ ] **Region drawing**: Implement region-based drawing commands
   - Rectangle fill/outline drawing
   - Line drawing (using box-drawing characters)
   - Region colour filling without changing characters
   - Character block manipulation and copying

- [ ] **Layout system**: Implement constraint-based layout engine
   - Layout manager for UI elements
   - Constraint solver for positioning elements
   - Responsive layout support for terminal resizing
   - Layout caching for improved performance

- [ ] **UI elements**: Create basic UI components
   - Labels with formatting
   - Borders and boxes
   - Scrollable regions
   - Status bar implementation

### [ ] Phase 3 - Buffer Management

Implement the core text editing functionality and buffer management system.

#### Expected Commits for Phase 3:

- [ ] **Text buffer structure**: Implement the core data structure for text
   - Efficient text storage with gap buffer or rope implementation
   - Line tracking and management
   - Buffer modification operations (insert, delete, replace)
   - Undo/redo system

- [ ] **File I/O**: Add file reading and writing capabilities
   - File loading and parsing
   - Saving modifications to disk
   - Backup file creation
   - File encoding detection and handling

- [ ] **Cursor and selection**: Implement cursor manipulation
   - Cursor positioning and movement
   - Multiple cursor support
   - Text selection operations
   - Clipboard integration

- [ ] **Text operations**: Implement basic text manipulation commands
   - Word-based movement and operations
   - Line operations (join, split, duplicate)
   - Indentation handling
   - Block operations

- [ ] **Scrolling and viewport**: Implement viewport management
   - Smooth scrolling implementation
   - Viewport tracking relative to buffer
   - Line wrapping options
   - Efficient partial buffer rendering

### [ ] Phase 4 - Modal Editing

Implement a unique `<object><verb>` modal editing system that differs from Vim's
traditional approach.

#### Expected Commits for Phase 4:

- [ ] **Mode system**: Create the foundation for modal editing
   - Mode state management
   - Mode transitions and indicators
   - Mode-specific UI elements
   - Command grammar framework for `<object><verb>` paradigm

- [ ] **Selection mode**: Implement object selection system
   - Object identifiers (w for word, p for paragraph, etc.)
   - Object modifiers (i for inner, a for around, etc.)
   - Multiple object selection via counts
   - Selection highlighting and visual feedback

- [ ] **Action mode**: Implement verb operations on selections
   - Action commands applied to current selection
   - Action composition and chaining
   - Register system for storing and retrieving text
   - Macro recording of action sequences

- [ ] **Insert mode**: Implement text insertion mode
   - Character and line insertion
   - Auto-indentation
   - Completion suggestions
   - Smart input features

- [ ] **Command mode**: Add command-line interface
   - Command parsing and execution
   - History navigation
   - Command completion
   - Error reporting and suggestions based on partial commands

### [ ] Phase 5 - Embedded Scheme-like Language

Implement a Scheme-like language that will serve as both the extension mechanism and the implementation language for much of the editor's functionality.

#### Expected Commits for Phase 5:

- [ ] **Language design**: Create the foundation for the Scheme-like language
   - Define syntax and semantics
   - Design the core data types and primitives
   - Create parser for the language
   - Implement evaluation of basic expressions

- [ ] **Bytecode compiler**: Build the compilation system
   - Design bytecode instruction set
   - Implement compiler from parsed expressions to bytecode
   - Create optimisation passes
   - Add error reporting and debugging information

- [ ] **Virtual machine**: Implement the bytecode interpreter
   - Create stack-based VM for executing bytecode
   - Implement garbage collection
   - Add function calling conventions
   - Create mechanism for native function calls

- [ ] **Editor integration**: Expose editor primitives to the language
   - Buffer manipulation functions
   - Text rendering and UI drawing primitives
   - Keyboard and input handling
   - File I/O and system interaction

- [ ] **Standard library**: Create core functions in the language
   - Text manipulation utilities
   - Data structure implementations
   - Editor command functions
   - Extension helpers and utilities

### [ ] Phase 6 - Advanced Features

Add more sophisticated editing capabilities and customisation options, primarily implemented in the Scheme-like language.

#### Expected Commits for Phase 6:

- [ ] **Search and replace**: Implement text finding functionality
   - Regular expression support (in Scheme-like language)
   - Incremental search implementation
   - Search highlighting and visualization
   - Replace with confirmation and pattern matching

- [ ] **Syntax highlighting**: Add language-aware text colouring
   - Lexer/parser framework in the Scheme-like language
   - Language definition system using S-expressions
   - Theme support with dynamic reloading
   - Efficient incremental parsing

- [ ] **Configuration system**: Create user preference management
   - Configuration via Scheme-like language expressions
   - Runtime configuration evaluation and changes
   - User-defined key mappings as Scheme functions
   - Profile management and switching

- [ ] **Split windows**: Implement multiple viewport support
   - Window management via Scheme-like language commands
   - Buffer-to-window assignment functions
   - Focus management and navigation
   - Layout persistence and restoration

### [ ] Phase 7 - Performance and Polishing

Focus on optimisation, robustness, and user experience improvements.

#### Expected Commits for Phase 7:

- [ ] **Performance optimisation**: Improve editor speed
   - Profiling and bottleneck identification in both C and Scheme code
   - Rendering optimisations and caching strategies
   - Virtual machine performance enhancements
   - Memory usage improvements and garbage collector tuning
   - Startup time reduction via precompilation of Scheme code

- [ ] **Error handling**: Enhance robustness
   - Comprehensive error reporting in both languages
   - Recovery mechanisms for VM crashes
   - Crash prevention and logging systems
   - Debugging tools for Scheme language extensions

- [ ] **Documentation**: Create user and developer documentation
   - User manual creation with embedded Scheme examples
   - Language reference for the Scheme dialect
   - API documentation for C primitives
   - Code commenting standards
   - Example configurations and extensions

- [ ] **Platform expansion**: Add support for additional platforms
   - Windows implementation
   - macOS implementation
   - Terminal capability detection and adaptation
   - Platform-specific optimisations
   - VM portability enhancements

- [ ] **Final polish**: Address details and refinements
   - Keyboard shortcut consistency across platforms
   - UI responsiveness improvements
   - Terminal compatibility edge cases
   - Language feature completeness
   - Final user experience improvements
