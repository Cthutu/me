#!/bin/bash

# Script to run clang-tidy on all source files

# Exit on error
set -e

# Print commands as they're executed
set -x

# Make sure the compilation database is up to date
compiledb make clean
compiledb make

# Find all C source and header files
C_FILES=$(find src -name "*.c" -o -name "*.h")

# Run clang-tidy on each file
for file in $C_FILES; do
    echo "Checking $file..."
    clang-tidy "$file" -p=.
done

echo "Linting complete!"
