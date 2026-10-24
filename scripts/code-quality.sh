#!/bin/bash

set -e

uv run --locked ruff check --fix .
uv run --locked ruff format .
uv run --locked mypy .
