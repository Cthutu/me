#pragma once

#include <stdbool.h> // C23 provides standard bool type

// Basic integer types with specified sizes
typedef signed char        i8;
typedef short              i16;
typedef int                i32;
typedef long long          i64;
typedef unsigned char      u8;
typedef unsigned short     u16;
typedef unsigned int       u32;
typedef unsigned long long u64;

// Floating point types
typedef float  f32;
typedef double f64;

// Utility macros
#define UNUSED(x) (void)(x) // Explicitly mark parameter as unused

// Boolean type is now provided by stdbool.h
// No need to define our own

// Platform detection using enum instead of macros
enum Platform { ME_LINUX = 0, ME_MACOS = 1, ME_WINDOWS = 2 };

// Platform detection
#if defined(PLATFORM_LINUX)
static const enum Platform CURRENT_PLATFORM = ME_LINUX;
#elif defined(PLATFORM_MACOS)
static const enum Platform CURRENT_PLATFORM = ME_MACOS;
#elif defined(PLATFORM_WINDOWS)
static const enum Platform CURRENT_PLATFORM = ME_WINDOWS;
#else
static const enum Platform CURRENT_PLATFORM = ME_LINUX; // Default to Linux
#endif
