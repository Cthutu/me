set dotenv-load
set positional-arguments

nerd := env("NERD", "nerd")

default:
    just --list

build:
    mkdir -p _bin
    {{nerd}} build main.n -o _bin/me

run *args: build
    _bin/me "$@"

release:
    mkdir -p _bin
    {{nerd}} build --release main.n -o _bin/me-release

check:
    {{nerd}} check main.n

test:
    {{nerd}} test tests

test-terminal: build
    python3 tests/terminal.py --binary _bin/me

test-all: test test-terminal

format:
    python3 build/format.py --nerd {{nerd}}

unicode:
    python3 build/fetch_unicode.py
    python3 build/generate_unicode.py
    {{nerd}} format src/unicode_data.n
    {{nerd}} format tests/unicode.n

clean:
    rm -rf _bin _obj _tmp
