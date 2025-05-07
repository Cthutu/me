#include "linux_platform.h"
#include "common/secure_string.h" // Include our secure string functions
#include "common/types.h"         // For u64, u8, i32 types
#include "linux_terminal.h"
#include "platform/interface/platform.h" // For PlatformInterface and PlatformState
#include <limits.h>                      // For SIZE_MAX
#include <stdint.h>                      // For SIZE_MAX
#include <stdio.h>
#include <stdlib.h>

// Define a constant for the maximum file size (1GB)
enum FileSizeLimits {
    MAX_FILE_SIZE_GB = 1,
    MAX_FILE_SIZE    = ((1ULL << 30) * MAX_FILE_SIZE_GB)
};

// Memory management
static void* linux_memory_alloc(u64 size) { return malloc(size); }

static void linux_memory_free(void* ptr) { free(ptr); }

// File I/O operations
static bool linux_file_read(const char* path, u8** data, u64* size)
{
    // Basic parameter validation
    if (path == nullptr || data == nullptr || size == nullptr) {
        return false;
    }

    // Open the file
    FILE* file = fopen(path, "rb");
    if (!file) {
        return false;
    }

    // Get file size
    (void)fseek(file, 0, SEEK_END);
    long file_size = ftell(file);
    (void)fseek(file, 0, SEEK_SET);

    // Check for file size errors or size limits
    if (file_size < 0 || (u64)file_size > MAX_FILE_SIZE) {
        (void)fclose(file);
        return false;
    }

    *size = (u64)file_size;

    // Allocate memory (+1 for null terminator)
    *data = (u8*)malloc(*size + 1);
    if (!*data) {
        (void)fclose(file);
        return false;
    }

    // Read the file
    size_t bytes_read = fread(*data, 1, *size, file);
    (void)fclose(file);

    // Check for read errors
    if (bytes_read != *size) {
        free(*data);
        *data = nullptr;
        return false;
    }

    // Null-terminate the buffer (safe because we allocated size+1)
    // NOLINTNEXTLINE(clang-analyzer-security.ArrayBound)
    (*data)[*size] = '\0';

    return true;
}

static bool linux_file_write(const char* path, u8* data, u64 size)
{
    FILE* file = fopen(path, "wb");
    if (!file) {
        return false;
    }

    u64 bytes_written = fwrite(data, 1, size, file);
    (void)fclose(file);

    return bytes_written == size;
}

// Terminal interface wrapper functions
static void linux_terminal_init_wrapper(void) { linux_terminal_init(); }

static void linux_terminal_shutdown_wrapper(void) { linux_terminal_shutdown(); }

static void linux_terminal_render_buffer_wrapper(u8* char_buffer,
                                                 u8* colour_buffer,
                                                 i32 width,
                                                 i32 height)
{
    linux_terminal_render_buffer(char_buffer, colour_buffer, width, height);
}

static u8 linux_terminal_read_input_wrapper(bool* ctrl_pressed,
                                            bool* alt_pressed,
                                            bool* shift_pressed)
{
    return linux_terminal_read_input(ctrl_pressed, alt_pressed, shift_pressed);
}

// Platform interface instance
static const PlatformInterface LINUX_PLATFORM_INTERFACE = {
    .memory_alloc           = linux_memory_alloc,
    .memory_free            = linux_memory_free,
    .file_read              = linux_file_read,
    .file_write             = linux_file_write,
    .terminal_init          = linux_terminal_init_wrapper,
    .terminal_shutdown      = linux_terminal_shutdown_wrapper,
    .terminal_get_size      = linux_terminal_get_size,
    .terminal_render_buffer = linux_terminal_render_buffer_wrapper,
    .terminal_read_input    = linux_terminal_read_input_wrapper,
    .terminal_clear_screen  = linux_terminal_clear_screen,
    .terminal_check_resize  = linux_terminal_check_resize};

// Initialize the Linux platform
PlatformState* linux_platform_init(void)
{
    // Allocate platform state
    PlatformState* state = (PlatformState*)malloc(sizeof(PlatformState));
    if (!state) {
        return nullptr; // Using nullptr for C23 compatibility
    }

    // Get terminal dimensions
    linux_terminal_get_size(&state->terminal_width, &state->terminal_height);

    // Allocate buffers
    u64 buffer_size = (u64)state->terminal_width * (u64)state->terminal_height;
    state->char_buffer  = malloc(buffer_size);
    state->color_buffer = malloc(buffer_size);

    if (!state->char_buffer || !state->color_buffer) {
        // Clean up on failure
        if (state->char_buffer) {
            free(state->char_buffer);
        }
        if (state->color_buffer) {
            free(state->color_buffer);
        }
        free(state);
        return nullptr; // Using nullptr for C23 compatibility
    }

    // Initialize buffers
    SAFE_MEMSET(state->char_buffer, buffer_size, ' ', buffer_size);
    SAFE_MEMSET(state->color_buffer, buffer_size, 0, buffer_size);

    // Set up platform function pointers
    state->memory_alloc  = linux_memory_alloc;
    state->memory_free   = linux_memory_free;
    state->file_read     = linux_file_read;
    state->file_write    = linux_file_write;

    // Initialize input state
    state->ctrl_pressed  = false;
    state->alt_pressed   = false;
    state->shift_pressed = false;
    state->last_char     = 0;

    // Initialize terminal
    linux_terminal_init();

    return state;
}

// Shutdown the Linux platform
void linux_platform_shutdown(PlatformState* state)
{
    if (state) {
        // Free allocated memory
        if (state->char_buffer) {
            free(state->char_buffer);
        }
        if (state->color_buffer) {
            free(state->color_buffer);
        }

        // Free the state itself
        free(state);
    }

    // Shutdown terminal
    linux_terminal_shutdown();
}

// Get the Linux platform interface
const PlatformInterface* linux_get_platform_interface(void)
{
    return &LINUX_PLATFORM_INTERFACE;
}
