#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

#include "../core/editor.h"
#include "linux/linux_platform.h"

extern bool linux_is_exit_requested(void);

int main()
{
    // Initialize the platform
    PlatformState* platform_state = linux_platform_init();
    if (!platform_state) {
        fprintf(stderr, "Failed to initialize platform\n");
        return 1;
    }

    // Get the platform interface
    const PlatformInterface* platform = linux_get_platform_interface();

    // Main loop
    bool running                      = true;
    while (running) {
        // Check for terminal resize
        platform->terminal_check_resize(platform_state);

        // Read input
        platform_state->last_char =
            platform->terminal_read_input(&platform_state->ctrl_pressed,
                                          &platform_state->alt_pressed,
                                          &platform_state->shift_pressed);

        // Call editor main function
        EditorCommand cmd = editor_main(platform_state);

        // Render the buffer
        platform->terminal_render_buffer(platform_state->char_buffer,
                                         platform_state->color_buffer,
                                         platform_state->terminal_width,
                                         platform_state->terminal_height);

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

        // Check if exit was requested by signal handler
        if (linux_is_exit_requested()) {
            running = false;
        }
    }

    // Shutdown the platform
    linux_platform_shutdown(platform_state);

    return 0;
}
