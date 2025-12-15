#!/bin/bash

# Bluesky Delete - Code Quality Script
# Runs black, ruff, and mypy on all Python files

set -e  # Exit on any error

echo "🔧 Running code quality checks..."
echo "=================================="

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "❌ Error: Not in a virtual environment"
    echo "   Please activate your virtual environment first:"
    echo "   macOS/Linux: source .venv/bin/activate"
    echo "   Windows: .venv\\Scripts\\activate"
    echo ""
    exit 1
fi

# Find all Python files
PYTHON_FILES=$(find . -name "*.py" -not -path "./.venv/*" -not -path "./build/*" -not -path "./__pycache__/*")

if [[ -z "$PYTHON_FILES" ]]; then
    echo "❌ No Python files found"
    exit 1
fi

echo "📁 Found Python files:"
echo "$PYTHON_FILES"
echo ""

# Run Black (formatter) - Always auto-fixes
echo "🎨 Running Black (code formatter)..."
black $PYTHON_FILES
echo "✅ Black: Code formatting applied"
echo ""

# Run Ruff (linter) - Auto-fix what's possible
echo "🔍 Running Ruff (linter with auto-fix)..."
ruff check --fix $PYTHON_FILES
echo ""

# Run Ruff again to show remaining issues
echo "🔍 Checking for remaining Ruff issues..."
if ruff check $PYTHON_FILES; then
    echo "✅ Ruff: No remaining linting issues"
else
    echo "⚠️  Ruff: Some issues require manual fixing (see above)"
fi
echo ""

# Run MyPy (type checker)
echo "🔬 Running MyPy (type checker)..."
if mypy $PYTHON_FILES; then
    echo "✅ MyPy: No type errors found"
else
    echo "❌ MyPy: Type errors found (see above)"
    exit 1
fi
echo ""

echo "🎉 All code quality checks completed successfully!"
echo "=================================="