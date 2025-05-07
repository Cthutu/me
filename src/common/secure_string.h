#pragma once

#include <stdarg.h>
#include <stdio.h>
#include <string.h>

/*
 * Secure string functions based on C11 Annex K, but implemented
 * for platforms that don't natively support them.
 *
 * These functions provide safety checks to prevent common buffer
 * overflow issues. If C11 Annex K functions become available, this
 * implementation can be conditionally replaced with the native one.
 */

/**
 * Secure implementation of snprintf that follows C11 Annex K guidelines
 *
 * @param buffer      Pointer to the buffer where output is stored
 * @param buffer_size Maximum number of bytes to be written to the buffer
 * @param format      Format string
 * @param ...         Arguments to be formatted
 * @return            Number of characters written, or negative on error
 */
int snprintf_s(char* buffer, size_t buffer_size, const char* format, ...);

/**
 * Secure implementation of memcpy that follows C11 Annex K guidelines
 *
 * @param destination Pointer to the destination array
 * @param dest_size   Size of the destination array
 * @param source      Pointer to the source of data to be copied
 * @param count       Number of bytes to copy
 * @return            Pointer to destination, or nullptr on error
 */
void* memcpy_s(void*       destination,
               size_t      dest_size,
               const void* source,
               size_t      count);

/**
 * Secure implementation of memset that follows C11 Annex K guidelines
 *
 * @param destination Pointer to the destination array
 * @param dest_size   Size of the destination array
 * @param value       Value to be set
 * @param count       Number of bytes to set
 * @return            Pointer to destination, or nullptr on error
 */
void* memset_s(void* destination, size_t dest_size, int value, size_t count);

/*
 * Use SAFE_SNPRINTF macro to clearly document safe usage of snprintf
 * when security linting is a concern
 */
#define SAFE_SNPRINTF(buffer, buffer_size, format, ...)                        \
    do {                                                                       \
        int snprintf_result =                                                  \
            snprintf_s(buffer, buffer_size, format, __VA_ARGS__);              \
        (void)snprintf_result; /* Silence unused result warning */             \
    } while (0)

/*
 * Use SAFE_MEMCPY macro to clearly document safe usage of memcpy
 * when security linting is a concern
 */
#define SAFE_MEMCPY(destination, dest_size, source, count)                     \
    memcpy_s(destination, dest_size, source, count)

/*
 * Use SAFE_MEMSET macro to clearly document safe usage of memset
 * when security linting is a concern
 */
#define SAFE_MEMSET(destination, dest_size, value, count)                      \
    memset_s(destination, dest_size, value, count)
