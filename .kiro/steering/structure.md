# Project Structure

## Root Directory Layout

```
blueskydelete/
├── main.py                 # Single-file application entry point
├── pyproject.toml         # Python project configuration and dependencies
├── .env.sample           # Environment variable template
├── .env                  # Local environment configuration (gitignored)
├── .python-version       # Python version specification
├── README.md             # Comprehensive documentation
├── LICENSE               # Project license
├── .gitignore           # Git ignore patterns
├── .venv/               # Virtual environment (gitignored)
├── __pycache__/         # Python bytecode cache (gitignored)
├── blueskydelete.egg-info/  # Package metadata (generated, gitignored)
├── scripts/
│   └── check-code.sh     # Code quality automation script
└── .github/
    └── workflows/
        ├── cleanup-feed.yml   # Scheduled content cleanup
        └── code-quality.yml   # CI code quality checks
```

## Architecture Patterns

### Single-File Application

- **Monolithic design**: All functionality in `main.py` for simplicity
- **Self-contained**: No complex module structure needed
- **Direct execution**: `python main.py` as primary interface

### Configuration Management

- **Environment-first**: All configuration via environment variables
- **Template-based**: `.env.sample` provides configuration template
- **CI-friendly**: GitHub Actions uses repository secrets/variables

### Code Quality Integration

- **Automated checks**: CI runs Black, Ruff, and MyPy on all PRs
- **Local script**: `./scripts/check-code.sh` for development workflow
- **Consistent tooling**: Same tools used locally and in CI

### Error Handling

- **Fail-fast validation**: Environment validation before execution
- **Graceful degradation**: Continue processing on individual item failures
- **Detailed logging**: Comprehensive error reporting with context

### Safety Patterns

- **Dry run default**: Safe mode unless explicitly disabled
- **Colored output**: Visual distinction between dry run and real operations
- **Batch processing**: Handle large datasets efficiently
- **Early termination**: Stop processing when date threshold reached

## Code Organization Principles

- **Top-down flow**: Main function orchestrates all operations
- **Single responsibility**: Each function has a clear, focused purpose
- **Type hints**: Function signatures include type annotations
- **Docstrings**: Comprehensive documentation for all functions
- **Constants**: Configuration defaults defined at module level
