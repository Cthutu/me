#pragma once

#include "../../common/types.h"

// Forward declaration of PlatformState
struct PlatformState;
typedef struct PlatformState PlatformState;

// Platform interface functions that all platforms must implement
typedef struct {
    // Memory management
    void* (*memory_alloc)(u64 size);
    void (*memory_free)(void* ptr);

    // File I/O operations
    bool (*file_read)(const char* path, u8** data, u64* size);
    bool (*file_write)(const char* path, u8* data, u64 size);

    // Terminal operations
    void (*terminal_init)(void);
    void (*terminal_shutdown)(void);
    void (*terminal_get_size)(i32* width, i32* height);
    void (*terminal_render_buffer)(u8* char_buffer,
                                   u8* colour_buffer,
                                   i32 width,
                                   i32 height);
    u8 (*terminal_read_input)(bool* ctrl_pressed,
                              bool* alt_pressed,
                              bool* shift_pressed);
    void (*terminal_clear_screen)(void);
    void (*terminal_check_resize)(PlatformState* state);
} PlatformInterface;

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

// Function to initialize the platform layer
// Returns a pointer to the platform state
PlatformState* platform_init(void);

// Function to shutdown the platform layer
void platform_shutdown(PlatformState* state);
