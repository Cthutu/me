#pragma once

#include "../interface/platform.h"

// Initialize the Linux platform
PlatformState* linux_platform_init(void);

// Shutdown the Linux platform
void linux_platform_shutdown(PlatformState* state);

// Get the Linux platform interface
const PlatformInterface* linux_get_platform_interface(void);
