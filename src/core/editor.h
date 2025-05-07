#pragma once

#include "../common/types.h"
#include "../platform/interface/platform.h"

// Commands that editor_main can return to the platform layer
typedef enum {
    EDITOR_CMD_NONE,          // No action needed
    EDITOR_CMD_QUIT,          // Request to quit the application
    EDITOR_CMD_SHELL_COMMAND, // Execute a shell command
                              // Add more commands as needed
} EditorCommand;

// Main editor function that the platform layer calls
EditorCommand editor_main(PlatformState* platform);
