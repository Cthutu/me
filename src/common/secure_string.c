#include <errno.h>
#include <stdarg.h>
#include <stdio.h> // For vsnprintf
#include <string.h>

/**
 * Secure implementation of snprintf that follows C11 Annex K guidelines
 */
int snprintf_s(char* buffer, size_t buffer_size, const char* format, ...)
{
    /* Safety checks */
    if (buffer == nullptr || format == nullptr || buffer_size == 0) {
        // NOLINTNEXTLINE(misc-include-cleaner)
        errno = EINVAL;
        return -1;
    }

    /* Use standard vsnprintf with buffer size checking */
    va_list args;
    va_start(args, format);

    // NOLINTNEXTLINE(clang-analyzer-security.insecureAPI.DeprecatedOrUnsafeBufferHandling)
    int result = vsnprintf(buffer, buffer_size, format, args);

    va_end(args);

    /* Ensure null-termination */
    if (result >= 0 && (size_t)result < buffer_size) {
        buffer[result] = '\0';
    } else if (buffer_size > 0) {
        buffer[buffer_size - 1] = '\0';
    }

    return result;
}

/**
 * Secure implementation of memcpy that follows C11 Annex K guidelines
 */
void* memcpy_s(void*       destination,
               size_t      dest_size,
               const void* source,
               size_t      count)
{
    /* Safety checks */
    if (destination == nullptr || source == nullptr || count > dest_size) {
        errno = EINVAL;
        return nullptr;
    }

    // NOLINTNEXTLINE(clang-analyzer-security.insecureAPI.DeprecatedOrUnsafeBufferHandling)
    return memcpy(destination, source, count);
}

/**
 * Secure implementation of memset that follows C11 Annex K guidelines
 */
void* memset_s(void* destination, size_t dest_size, int value, size_t count)
{
    /* Safety checks */
    if (destination == nullptr || count > dest_size) {
        errno = EINVAL;
        return nullptr;
    }

    /* Use standard memset with size checking */
    // NOLINTNEXTLINE(clang-analyzer-security.insecureAPI.DeprecatedOrUnsafeBufferHandling)
    return memset(destination, value, count);
}
