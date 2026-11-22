set dotenv-load
set positional-arguments

nerd := env("NERD", "nerd")

alias b := build
alias r := run
alias rel := release
alias c := check
alias t := test
alias tt := test-terminal
alias ta := test-all
alias f := format

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

install: release
    install -Dm755 _bin/me-release "$HOME/.local/bin/me"

check:
    {{nerd}} check main.n

test:
    {{nerd}} test main.n

test-terminal: build
    python3 tests/terminal.py --binary _bin/me

test-all: test test-terminal

format:
    python3 build/format.py --nerd {{nerd}}

unicode:
    python3 build/fetch_unicode.py
    python3 build/generate_unicode.py
    {{nerd}} format src/unicode_data.n
    {{nerd}} format src/characters.n

clean:
    rm -rf _bin _obj _tmp
