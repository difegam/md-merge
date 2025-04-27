set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]
set dotenv-load := true

# Available recipes
_default:
    @just --list --unsorted --list-prefix "    > " --justfile {{justfile()}}

# 🏃🏽‍♂️‍➡️ Run pre-commit hooks manually
[group('dev-tools')]
pre-commit-check:
    @echo "Running pre-commit hooks on all files"
    @pre-commit run --all-files
