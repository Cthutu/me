CC = clang
CFLAGS = -std=c2x -Wall -Wextra -pedantic -Werror -g -I./src
LDFLAGS = 

# Platform detection
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    PLATFORM = linux
    CFLAGS += -D PLATFORM_LINUX
endif
ifeq ($(UNAME_S),Darwin)
    PLATFORM = macos
    CFLAGS += -D PLATFORM_MACOS
endif
ifeq ($(OS),Windows_NT)
    PLATFORM = win32
    CFLAGS += -D PLATFORM_WINDOWS
endif

SRC_DIR = src
BUILD_DIR = _build
BIN_DIR = _bin

# Default build target is debug
TARGET = me
EXEC = $(BIN_DIR)/$(TARGET)

# Source files
CORE_SRC = $(wildcard $(SRC_DIR)/core/*.c)
PLATFORM_SRC = $(wildcard $(SRC_DIR)/platform/$(PLATFORM)_*.c)
PLATFORM_IMPL_SRC = $(wildcard $(SRC_DIR)/platform/$(PLATFORM)/*.c)
COMMON_SRC = $(wildcard $(SRC_DIR)/common/*.c)
ALL_SRC = $(CORE_SRC) $(PLATFORM_SRC) $(PLATFORM_IMPL_SRC) $(COMMON_SRC)

# Object files
OBJS = $(patsubst $(SRC_DIR)/%.c,$(BUILD_DIR)/%.o,$(ALL_SRC))

# Dependency files
DEPS = $(OBJS:.o=.d)

# Directories
DIRS = $(sort $(dir $(OBJS)) $(BIN_DIR))

.PHONY: all clean run

all: $(EXEC)

$(EXEC): $(OBJS) | $(BIN_DIR)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Generate dependencies automatically while compiling
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c | $(DIRS)
	$(CC) $(CFLAGS) -MMD -MP -c -o $@ $<

$(DIRS):
	mkdir -p $@

run: $(EXEC)
	@./$(EXEC)

clean:
	rm -rf $(BUILD_DIR) $(BIN_DIR)

# Include all dependency files
-include $(DEPS)
