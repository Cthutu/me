#include "editor.h"
#include <stdio.h> // For snprintf

// The main editor function that is called by the platform layer
EditorCommand editor_main(PlatformState* platform)
{
    // This is a minimal implementation for Phase 1, Commit 1
    // It will simply quit when the user presses the ESCAPE key (ASCII 27)

    // TEMPORARY: Display terminal dimensions for resize testing
    char dimension_text[64];
    snprintf(dimension_text,
             sizeof(dimension_text),
             "Terminal size: %d x %d",
             platform->terminal_width,
             platform->terminal_height);

    // Display the text at position 1,1
    u64 text_len = 0;
    while (dimension_text[text_len] && text_len < sizeof(dimension_text)) {
        // Calculate position in buffer (row 1, starting at column 1)
        u64 pos = 1 * (u64)platform->terminal_width + 1 + text_len;

        // Update buffer if within bounds
        if (pos < (u64)(platform->terminal_width * platform->terminal_height)) {
            platform->char_buffer[pos]  = dimension_text[text_len];
            platform->color_buffer[pos] = 7; // White text (standard color)
        }
        text_len++;
    }

    if (platform->last_char == 27) { // ASCII for ESCAPE
        return EDITOR_CMD_QUIT;
    }

    return EDITOR_CMD_NONE;
}
