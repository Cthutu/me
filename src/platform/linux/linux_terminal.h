#pragma once

#include "common/types.h"
#include "platform/interface/platform.h"

// Terminal capabilities
typedef struct {
    bool supports_256_colours;
    bool supports_true_colour;
    bool supports_mouse;
    bool supports_focus_events;
} TerminalCapabilities;

// Terminal initialization
void linux_terminal_init(void);

// Terminal shutdown
void linux_terminal_shutdown(void);

// Terminal operations
void linux_terminal_enable_raw_mode(void);
void linux_terminal_disable_raw_mode(void);
void linux_terminal_get_size(i32* width, i32* height);
void linux_terminal_clear_screen(void);
void linux_terminal_setup_alternate_screen(void);
void linux_terminal_restore_main_screen(void);
void linux_terminal_set_cursor_position(i32 pos_x, i32 pos_y);
void linux_terminal_cursor_hide(void);
void linux_terminal_cursor_show(void);
void linux_terminal_check_resize(PlatformState* state);
void linux_terminal_detect_capabilities(TerminalCapabilities* capabilities);
void linux_terminal_render_buffer(u8* char_buffer,
                                  u8* colour_buffer,
                                  i32 width,
                                  i32 height);

// Input handling
u8 linux_terminal_read_input(bool* ctrl_pressed,
                             bool* alt_pressed,
                             bool* shift_pressed);

// Signal handling
void linux_setup_signal_handlers(void);
bool linux_is_exit_requested(void);
