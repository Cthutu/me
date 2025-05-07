#include "editor.h"
#include "common/secure_string.h" // For secure string functions
#include "common/types.h"
#include "platform/interface/platform.h" // Direct include for PlatformState

// Constants as enums instead of macros
enum EditorConstants {
    TEXT_BUFFER_SIZE = 64,
    COLOR_WHITE      = 7,
    ASCII_ESCAPE     = 27
};

// The main editor function that is called by the platform layer
EditorCommand editor_main(PlatformState* platform)
{
    // This is a minimal implementation for Phase 1, Commit 1
    // It will simply quit when the user presses the ESCAPE key (ASCII 27)

    // TEMPORARY: Display terminal dimensions for resize testing
    char dimension_text[TEXT_BUFFER_SIZE];
    SAFE_SNPRINTF(dimension_text,
                  sizeof(dimension_text),
                  "Terminal size: %d x %d",
                  platform->terminal_width,
                  platform->terminal_height);

    // Display the text at position 1,1
    u64 text_len = 0;
    while (dimension_text[text_len] && text_len < sizeof(dimension_text)) {
        // Calculate position in buffer (row 1, starting at column 1)
        u64 pos = ((u64)1 * (u64)platform->terminal_width) + (u64)1 + text_len;

        // Update buffer if within bounds
        u64 buffer_size =
            (u64)(platform->terminal_width) * (u64)(platform->terminal_height);
        if (pos < buffer_size) {
            platform->char_buffer[pos] = dimension_text[text_len];
            platform->color_buffer[pos] =
                COLOR_WHITE; // White text (standard color)
        }
        text_len++;
    }

    if (platform->last_char == ASCII_ESCAPE) { // ASCII for ESCAPE
        return EDITOR_CMD_QUIT;
    }

    return EDITOR_CMD_NONE;
}
