# Technology Stack

## Core Technologies

- **Python 3.x**: Primary language (version specified in `.python-version`)
- **atproto**: Bluesky AT Protocol client library (v0.0.65)
- **python-dotenv**: Environment variable management (dev dependency)

## Build System

- **pyproject.toml**: Modern Python packaging with pip-installable setup
- **Virtual environments**: `.venv` for dependency isolation

## Environment Management

- **Environment variables**: Configuration via `.env` files
- **CI/CD**: GitHub Actions for automated execution
- **Secrets management**: GitHub repository secrets and variables

## Code Quality Tools

- **Black**: Code formatter for consistent style
- **Ruff**: Fast Python linter with auto-fix capabilities
- **MyPy**: Static type checker for type safety

## Common Commands

### Development Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv

# Activate environment
# macOS/Linux: source .venv/bin/activate
# Windows: .venv\Scripts\activate

# Install for development (includes dotenv)
pip install -e .[dev]

# Install for production
pip install -e .
```

### Code Quality

```bash
# Run all quality checks with auto-fix
./scripts/check-code.sh

# Individual tools
black .                    # Format code
ruff check --fix .         # Lint with auto-fix
mypy .                     # Type check
```

### Running the Application

```bash
# Basic run (dry mode by default)
python main.py

# Run with custom environment variables
LOG_LEVEL=DEBUG DRY_RUN=false DAYS_AGO=30 python main.py

# Environment-specific runs
DRY_RUN=false python main.py  # Actually delete content
LOG_LEVEL=WARNING python main.py  # Quiet mode
```

### Configuration

```bash
# Setup environment file
cp .env.sample .env
# Edit .env with your credentials
```

## Dependencies

- Minimal dependency footprint for reliability
- Production dependencies kept separate from development tools
- Version pinning for reproducible builds
