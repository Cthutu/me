#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <termios.h>
#include <unistd.h>

#include "../core/editor.h"

// Global state
static struct termios original_termios;
static PlatformState  platform_state;

// Memory management
static void* linux_memory_alloc(u64 size) { return malloc(size); }

static void linux_memory_free(void* ptr) { free(ptr); }

// File I/O operations
static bool linux_file_read(const char* path, u8** data, u64* size)
{
    FILE* file = fopen(path, "rb");
    if (!file) {
        return false;
    }

    // Get file size
    fseek(file, 0, SEEK_END);
    *size = ftell(file);
    fseek(file, 0, SEEK_SET);

    // Allocate buffer and read file
    *data = (u8*)malloc(*size + 1);
    if (!*data) {
        fclose(file);
        return false;
    }

    u64 bytes_read      = fread(*data, 1, *size, file);
    (*data)[bytes_read] = '\0'; // Null-terminate the buffer
    fclose(file);

    return bytes_read == *size;
}

static bool linux_file_write(const char* path, u8* data, u64 size)
{
    FILE* file = fopen(path, "wb");
    if (!file) {
        return false;
    }

    u64 bytes_written = fwrite(data, 1, size, file);
    fclose(file);

    return bytes_written == size;
}

// Terminal handling
static void terminal_enable_raw_mode()
{
    // Save original terminal settings
    tcgetattr(STDIN_FILENO, &original_termios);

    // Modify terminal settings for raw mode
    struct termios raw = original_termios;
    // Input flags: disable break processing, CR to NL conversion, parity
    // checking, strip high bit, software flow control
    raw.c_iflag &= ~(BRKINT | ICRNL | INPCK | ISTRIP | IXON);
    // Output flags: disable post processing
    raw.c_oflag &= ~(OPOST);
    // Control flags: set 8-bit chars
    raw.c_cflag |= (CS8);
    // Local flags: disable echo, canonical mode, extended input processing,
    // signal chars
    raw.c_lflag &= ~(ECHO | ICANON | IEXTEN | ISIG);
    // Control chars: set return condition after min 0 chars or timeout
    raw.c_cc[VMIN]  = 0;
    raw.c_cc[VTIME] = 1; // 100ms timeout

    // Apply settings
    tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw);
}

static void terminal_disable_raw_mode()
{
    // Restore original terminal settings
    tcsetattr(STDIN_FILENO, TCSAFLUSH, &original_termios);
}

static void terminal_get_size(i32* width, i32* height)
{
    struct winsize ws;
    if (ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws) == -1 || ws.ws_col == 0) {
        // Fallback to default size
        *width  = 80;
        *height = 24;
    } else {
        *width  = ws.ws_col;
        *height = ws.ws_row;
    }
}

static void terminal_clear_screen()
{
    // Clear screen and position cursor at top-left
    write(STDOUT_FILENO, "\x1b[2J\x1b[H", 7);
}

static void terminal_setup_alternate_screen()
{
    // Switch to alternate screen buffer
    write(STDOUT_FILENO, "\x1b[?1049h", 8);
}

static void terminal_restore_main_screen()
{
    // Switch back to main screen buffer
    write(STDOUT_FILENO, "\x1b[?1049l", 8);
}

static void cleanup()
{
    // Free allocated memory
    if (platform_state.char_buffer) {
        free(platform_state.char_buffer);
    }
    if (platform_state.color_buffer) {
        free(platform_state.color_buffer);
    }

    // Restore terminal
    terminal_restore_main_screen();
    terminal_disable_raw_mode();
}

static void setup_platform_state()
{
    // Get terminal dimensions
    terminal_get_size(&platform_state.terminal_width,
                      &platform_state.terminal_height);

    // Allocate buffers
    u64 buffer_size =
        platform_state.terminal_width * platform_state.terminal_height;
    platform_state.char_buffer  = malloc(buffer_size);
    platform_state.color_buffer = malloc(buffer_size);

    // Initialize buffers
    memset(platform_state.char_buffer, ' ', buffer_size);
    memset(platform_state.color_buffer, 0, buffer_size);

    // Set up platform function pointers
    platform_state.memory_alloc  = linux_memory_alloc;
    platform_state.memory_free   = linux_memory_free;
    platform_state.file_read     = linux_file_read;
    platform_state.file_write    = linux_file_write;

    // Initialize input state
    platform_state.ctrl_pressed  = false;
    platform_state.alt_pressed   = false;
    platform_state.shift_pressed = false;
    platform_state.last_char     = 0;
}

static u8 read_key()
{
    // This is a simplistic version that will be expanded later
    // It doesn't track modifier keys yet
    u8 c = 0;
    if (read(STDIN_FILENO, &c, 1) == 1) {
        return c;
    }
    return 0;
}

int main()
{
    // Set up terminal
    terminal_enable_raw_mode();
    terminal_setup_alternate_screen();
    terminal_clear_screen();

    // Set up cleanup handler
    atexit(cleanup);

    // Initialize platform state
    setup_platform_state();

    // Main loop
    bool running = true;
    while (running) {
        // Read input
        platform_state.last_char = read_key();

        // Call editor main function
        EditorCommand cmd        = editor_main(&platform_state);

        // Process command
        switch (cmd) {
        case EDITOR_CMD_QUIT:
            running = false;
            break;
        case EDITOR_CMD_SHELL_COMMAND:
            // Not implemented in Phase 1
            break;
        case EDITOR_CMD_NONE:
        default:
            break;
        }
    }

    return 0;
}
