#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <termios.h>
#include <unistd.h>

#include "linux_terminal.h"

// Global state
static struct termios       original_termios;
static TerminalCapabilities terminal_capabilities;
static volatile bool        exit_requested = false; // Signal handler flag

// Signal handling
static void signal_handler(int sig)
{
    UNUSED(sig); // Explicitly mark parameter as unused
    // Set exit flag to true
    exit_requested = true;
}

void linux_setup_signal_handlers(void)
{
    // Set up handlers for common termination signals
    signal(SIGTERM, signal_handler);
    signal(SIGINT, signal_handler);
    signal(SIGHUP, signal_handler);
    signal(SIGQUIT, signal_handler);
}

bool linux_is_exit_requested(void) { return exit_requested; }

void linux_terminal_init(void)
{
    // Initialize terminal
    linux_terminal_enable_raw_mode();
    linux_terminal_setup_alternate_screen();
    linux_terminal_clear_screen();
    linux_terminal_cursor_hide();

    // Set up signal handlers
    linux_setup_signal_handlers();

    // Detect terminal capabilities
    linux_terminal_detect_capabilities(&terminal_capabilities);
}

void linux_terminal_shutdown(void)
{
    // Restore terminal
    linux_terminal_cursor_show();
    linux_terminal_restore_main_screen();
    linux_terminal_disable_raw_mode();
}

void linux_terminal_enable_raw_mode(void)
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

void linux_terminal_disable_raw_mode(void)
{
    // Restore original terminal settings
    tcsetattr(STDIN_FILENO, TCSAFLUSH, &original_termios);
}

void linux_terminal_get_size(i32* width, i32* height)
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

void linux_terminal_clear_screen(void)
{
    // Clear screen and position cursor at top-left
    write(STDOUT_FILENO, "\x1b[2J\x1b[H", 7);
}

void linux_terminal_setup_alternate_screen(void)
{
    // Switch to alternate screen buffer
    write(STDOUT_FILENO, "\x1b[?1049h", 8);
}

void linux_terminal_restore_main_screen(void)
{
    // Switch back to main screen buffer
    write(STDOUT_FILENO, "\x1b[?1049l", 8);
}

void linux_terminal_set_cursor_position(i32 x, i32 y)
{
    // Set cursor position (1-based coordinates in VT100 sequences)
    char buf[32];
    snprintf(buf, sizeof(buf), "\x1b[%d;%dH", y + 1, x + 1);
    write(STDOUT_FILENO, buf, strlen(buf));
}

void linux_terminal_cursor_hide(void)
{
    // Hide the cursor
    write(STDOUT_FILENO, "\x1b[?25l", 6);
}

void linux_terminal_cursor_show(void)
{
    // Show the cursor
    write(STDOUT_FILENO, "\x1b[?25h", 6);
}

void linux_terminal_detect_capabilities(TerminalCapabilities* capabilities)
{
    // Default to conservative capabilities
    capabilities->supports_256_colours  = false;
    capabilities->supports_true_colour  = false;
    capabilities->supports_mouse        = false;
    capabilities->supports_focus_events = false;

    // Check environment variables for terminal type
    const char* term                    = getenv("TERM");
    const char* colorterm               = getenv("COLORTERM");

    // Basic terminal capability detection based on env vars
    if (term) {
        if (strstr(term, "256color") || strstr(term, "256colour")) {
            capabilities->supports_256_colours = true;
        }

        if (strstr(term, "xterm") || strstr(term, "screen") ||
            strstr(term, "tmux")) {
            capabilities->supports_mouse = true;
        }
    }

    if (colorterm) {
        if (strstr(colorterm, "truecolor") || strstr(colorterm, "24bit")) {
            capabilities->supports_true_colour = true;
        }
    }
}

u8 linux_terminal_read_input(bool* ctrl_pressed,
                             bool* alt_pressed,
                             bool* shift_pressed)
{
    // This is a simplistic version that will be expanded in the Input handling
    // commit It doesn't track modifier keys yet
    u8 c = 0;
    if (read(STDIN_FILENO, &c, 1) == 1) {
        // For now, we're not setting any modifier keys
        *ctrl_pressed  = false;
        *alt_pressed   = false;
        *shift_pressed = false;
        return c;
    }
    return 0;
}

void linux_terminal_check_resize(PlatformState* state)
{
    // Get current terminal dimensions
    i32 new_width, new_height;
    linux_terminal_get_size(&new_width, &new_height);

    // Check if dimensions changed
    if (new_width != state->terminal_width ||
        new_height != state->terminal_height) {

        // Free old buffers
        if (state->char_buffer) {
            free(state->char_buffer);
        }
        if (state->color_buffer) {
            free(state->color_buffer);
        }

        // Update dimensions
        state->terminal_width  = new_width;
        state->terminal_height = new_height;

        // Reallocate buffers
        u64 buffer_size =
            (u64)state->terminal_width * (u64)state->terminal_height;
        state->char_buffer  = malloc(buffer_size);
        state->color_buffer = malloc(buffer_size);

        // Initialize new buffers
        memset(state->char_buffer, ' ', buffer_size);
        memset(state->color_buffer, 0, buffer_size);
    }
}

void linux_terminal_render_buffer(u8* char_buffer,
                                  u8* colour_buffer,
                                  i32 width,
                                  i32 height)
{
    // Color buffer is not used in the current implementation
    UNUSED(colour_buffer);

    // Position cursor at the top left
    linux_terminal_set_cursor_position(0, 0);

    // Create a buffer for each line
    char* line_buffer = malloc(width + 1);
    if (!line_buffer) {
        return;
    }

    // Render each line
    for (i32 y = 0; y < height; y++) {
        // Copy characters for this line to the buffer
        for (i32 x = 0; x < width; x++) {
            u64 pos        = (u64)y * (u64)width + (u64)x;
            line_buffer[x] = char_buffer[pos];
        }
        line_buffer[width] = '\0';

        // Position cursor at the beginning of this line
        linux_terminal_set_cursor_position(0, y);

        // Write the line
        write(STDOUT_FILENO, line_buffer, width);
    }

    free(line_buffer);
}
