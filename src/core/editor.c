#include "editor.h"

// The main editor function that is called by the platform layer
EditorCommand editor_main(PlatformState* platform)
{
    // This is a minimal implementation for Phase 1, Commit 1
    // It will simply quit when the user presses the ESCAPE key (ASCII 27)

    if (platform->last_char == 27) { // ASCII for ESCAPE
        return EDITOR_CMD_QUIT;
    }

    return EDITOR_CMD_NONE;
}
