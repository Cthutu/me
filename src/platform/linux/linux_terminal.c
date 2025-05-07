#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <termios.h>
#include <unistd.h>

#include "common/secure_string.h" // Include our secure string functions
#include "common/types.h"
#include "linux_terminal.h"
#include "platform/interface/platform.h" // For PlatformState

// Constants for terminal dimensions and VT100 sequence lengths
enum TerminalConstants {
    DEFAULT_TERM_WIDTH       = 80,
    DEFAULT_TERM_HEIGHT      = 24,
    VT100_CLEAR_SEQ_LEN      = 7,
    VT100_ALT_SCREEN_ON_LEN  = 8,
    VT100_ALT_SCREEN_OFF_LEN = 8,
    VT100_CURSOR_BUFFER_SIZE = 32,
    VT100_HIDE_CURSOR_LEN    = 6,
    VT100_SHOW_CURSOR_LEN    = 6
};

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
    (void)signal(SIGTERM, signal_handler);
    (void)signal(SIGINT, signal_handler);
    (void)signal(SIGHUP, signal_handler);
    (void)signal(SIGQUIT, signal_handler);
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
    if (tcgetattr(STDIN_FILENO, &original_termios) == -1) {
        // Handle error or just continue with defaults
    }

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
    if (tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw) == -1) {
        // Handle error or just continue
    }
}

void linux_terminal_disable_raw_mode(void)
{
    // Restore original terminal settings
    if (tcsetattr(STDIN_FILENO, TCSAFLUSH, &original_termios) == -1) {
        // Handle error or just continue
    }
}

void linux_terminal_get_size(i32* width, i32* height)
{
    struct winsize win_size;
    // NOLINTNEXTLINE(misc-include-cleaner)
    if (ioctl(STDOUT_FILENO, TIOCGWINSZ, &win_size) == -1 ||
        win_size.ws_col == 0) {
        // Fallback to default size
        *width  = DEFAULT_TERM_WIDTH;
        *height = DEFAULT_TERM_HEIGHT;
    } else {
        *width  = win_size.ws_col;
        *height = win_size.ws_row;
    }
}

void linux_terminal_clear_screen(void)
{
    // Clear screen and position cursor at top-left
    (void)write(STDOUT_FILENO, "\x1b[2J\x1b[H", VT100_CLEAR_SEQ_LEN);
}

void linux_terminal_setup_alternate_screen(void)
{
    // Switch to alternate screen buffer
    (void)write(STDOUT_FILENO, "\x1b[?1049h", VT100_ALT_SCREEN_ON_LEN);
}

void linux_terminal_restore_main_screen(void)
{
    // Switch back to main screen buffer
    (void)write(STDOUT_FILENO, "\x1b[?1049l", VT100_ALT_SCREEN_OFF_LEN);
}

void linux_terminal_set_cursor_position(i32 pos_x, i32 pos_y)
{
    // Set cursor position (1-based coordinates in VT100 sequences)
    char buf[VT100_CURSOR_BUFFER_SIZE];
    SAFE_SNPRINTF(buf, sizeof(buf), "\x1b[%d;%dH", pos_y + 1, pos_x + 1);
    (void)write(STDOUT_FILENO, buf, strlen(buf));
}

void linux_terminal_cursor_hide(void)
{
    // Hide the cursor
    (void)write(STDOUT_FILENO, "\x1b[?25l", VT100_HIDE_CURSOR_LEN);
}

void linux_terminal_cursor_show(void)
{
    // Show the cursor
    (void)write(STDOUT_FILENO, "\x1b[?25h", VT100_SHOW_CURSOR_LEN);
}

void linux_terminal_detect_capabilities(TerminalCapabilities* capabilities)
{
    if (capabilities == nullptr) {
        return;
    }

    // Default to conservative capabilities
    capabilities->supports_256_colours  = false;
    capabilities->supports_true_colour  = false;
    capabilities->supports_mouse        = false;
    capabilities->supports_focus_events = false;

    // Check environment variables for terminal type
    // NOLINTBEGIN(concurrency-mt-unsafe)
    const char* term                    = getenv("TERM");
    const char* colorterm               = getenv("COLORTERM");
    // NOLINTEND(concurrency-mt-unsafe)

    // Basic terminal capability detection based on env vars
    if (term != nullptr) {
        if (strstr(term, "256color") || strstr(term, "256colour")) {
            capabilities->supports_256_colours = true;
        }

        if (strstr(term, "xterm") || strstr(term, "screen") ||
            strstr(term, "tmux")) {
            capabilities->supports_mouse = true;
        }
    }

    if (colorterm != nullptr) {
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
    u8 chr = 0;
    if (read(STDIN_FILENO, &chr, 1) == 1) {
        // For now, we're not setting any modifier keys
        *ctrl_pressed  = false;
        *alt_pressed   = false;
        *shift_pressed = false;
        return chr;
    }
    return 0;
}

void linux_terminal_check_resize(PlatformState* state)
{
    if (state == nullptr) {
        return;
    }

    // Get current terminal dimensions
    i32 new_width  = 0;
    i32 new_height = 0;
    linux_terminal_get_size(&new_width, &new_height);

    // Check if dimensions changed
    if (new_width != state->terminal_width ||
        new_height != state->terminal_height) {

        // Free old buffers
        if (state->char_buffer) {
            free(state->char_buffer);
            state->char_buffer = nullptr;
        }
        if (state->color_buffer) {
            free(state->color_buffer);
            state->color_buffer = nullptr;
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
        if (state->char_buffer && state->color_buffer) {
            SAFE_MEMSET(state->char_buffer, buffer_size, ' ', buffer_size);
            SAFE_MEMSET(state->color_buffer, buffer_size, 0, buffer_size);
        }
    }
}

void linux_terminal_render_buffer(u8* char_buffer,
                                  u8* colour_buffer,
                                  i32 width,
                                  i32 height)
{
    UNUSED(char_buffer);
    UNUSED(colour_buffer);
    UNUSED(width);
    UNUSED(height);

    // Position cursor at the top left
    linux_terminal_set_cursor_position(0, 0);
}
