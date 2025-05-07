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

// Boolean type is now provided by stdbool.h
// No need to define our own

// Platform detection macros
#if defined(PLATFORM_LINUX)
#    define ME_PLATFORM_LINUX 1
#else
#    define ME_PLATFORM_LINUX 0
#endif

#if defined(PLATFORM_MACOS)
#    define ME_PLATFORM_MACOS 1
#else
#    define ME_PLATFORM_MACOS 0
#endif

#if defined(PLATFORM_WINDOWS)
#    define ME_PLATFORM_WINDOWS 1
#else
#    define ME_PLATFORM_WINDOWS 0
#endif
