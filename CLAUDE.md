# CLAUDE.md

## Architecture

Single-file design in `main.py` is deliberate — do not split into modules.

## Safety Philosophy

Dry-run-by-default is a core design principle. Never change this default.

## Style Conventions

- Google-style docstrings with Args/Returns/Raises sections
- Comments explain "why" not "what"; 72-char limit for comments and docstrings
