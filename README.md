# Matt's Editor

I believe that every programmer should write his own editor, in the same way
that every Jedi should build his own lightsabre (the main tool of use).

This repository contains all the code for my editor. Initially, it is
written in C, but later it will be rewritten in my own language.

## Project Structure

The project follows a platform-agnostic architecture with clear separation between:

1. **Core Editor Logic**: Platform-independent code that handles editing functionality
2. **Platform Layer**: Platform-specific code that interfaces with the operating system
3. **Common Utilities**: Shared types and utilities used across the project

## Development Phases

The development is divided into several phases:

### Phase 1: Terminal Handling
- Terminal initialization and configuration
- Screen buffer and efficient rendering
- Input processing
- Cursor control

### Phase 2: Text Buffer Management
- Implement text storage and editing
- Cursor movement within text
- File loading and saving
- Viewport and scrolling

### Phase 3: Modal Editing
- Modal editing system (normal, insert, command modes)
- Keybindings and commands
- Text operations

### Future Phases
- Advanced editing features
- Configuration system
- Plugin architecture

## Building and Running

### Prerequisites
- GCC or Clang compiler with C23 support
- Make

### Compiling
```bash
make
```

### Running
```bash
make run
```

### Cleaning Build Files
```bash
make clean
```

## Design Principles

1. No external dependencies beyond standard libraries
2. Clear separation between platform-specific and platform-agnostic code
3. Efficient terminal I/O through state tracking and minimal updates
4. Pure update loop with explicit input and output through platform interface

## License

This project is personal and not yet licensed for distribution.
