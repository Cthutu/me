#!/bin/bash

# Script to run clang-tidy and clang-format on all source files

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
    echo "Checking $file with clang-tidy..."
    clang-tidy "$file" -p=.
done

# Run clang-format on each file
FORMAT_ISSUES=0
for file in $C_FILES; do
    echo "Checking $file formatting..."
    if ! clang-format -style=file "$file" | diff -u "$file" -; then
        echo "❌ Formatting issues in $file"
        FORMAT_ISSUES=1
    fi
done

# Check if --fix option was provided
if [[ "$1" == "--fix" ]]; then
    echo "Fixing formatting issues..."
    for file in $C_FILES; do
        clang-format -i -style=file "$file"
    done
    echo "✅ Formatting fixed"
elif [[ $FORMAT_ISSUES -eq 1 ]]; then
    echo "💡 Run './lint.sh --fix' to fix formatting issues"
fi

echo "Linting complete!"
