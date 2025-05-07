#pragma once

#include "../common/types.h"

// Forward declarations
typedef struct PlatformState PlatformState;

// Commands that editor_main can return to the platform layer
typedef enum {
    EDITOR_CMD_NONE,          // No action needed
    EDITOR_CMD_QUIT,          // Request to quit the application
    EDITOR_CMD_SHELL_COMMAND, // Execute a shell command
                              // Add more commands as needed
} EditorCommand;

// Main editor function that the platform layer calls
EditorCommand editor_main(PlatformState* platform);

// Platform state structure that encapsulates all platform-specific data
// needed by the editor core
struct PlatformState {
    // Terminal information
    i32 terminal_width;
    i32 terminal_height;

    // Screen buffer
    u8* char_buffer;  // Characters to display
    u8* color_buffer; // Color for each character

    // Input state
    bool ctrl_pressed;
    bool alt_pressed;
    bool shift_pressed;
    u8   last_char; // Last character input

    // Platform services (function pointers)
    // These will be implemented differently for each platform
    void* (*memory_alloc)(u64 size);
    void (*memory_free)(void* ptr);
    bool (*file_read)(const char* path, u8** data, u64* size);
    bool (*file_write)(const char* path, u8* data, u64 size);
};
