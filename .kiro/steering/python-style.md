# Python Style Guide (PEP 8)

## Code Layout

### Indentation

- Use 4 spaces per indentation level
- Never mix tabs and spaces
- Continuation lines should align wrapped elements

### Line Length

- Limit lines to 79 characters for code
- Limit docstrings/comments to 72 characters
- Break long lines using parentheses, not backslashes

### Blank Lines

- Two blank lines around top-level function and class definitions
- One blank line around method definitions inside classes
- Use blank lines sparingly inside functions to indicate logical sections

## Import Organization

```python
# Standard library imports
import os
import sys
from typing import Optional, List

# Third-party imports
import requests
from atproto import Client

# Local application imports
from .utils import helper_function
```

### Import Rules

- Imports should be on separate lines
- Group imports: standard library, third-party, local
- Use absolute imports when possible
- Avoid wildcard imports (`from module import *`)

## Naming Conventions

### Variables and Functions

- Use `snake_case` for variables and functions
- Use descriptive names: `user_count` not `uc`
- Avoid single-letter variables except for short loops

### Constants

- Use `UPPER_CASE_WITH_UNDERSCORES`
- Define at module level

### Classes

- Use `PascalCase` for class names
- Use descriptive names that indicate purpose

### Private Members

- Use single leading underscore for internal use: `_internal_method`
- Use double leading underscore for name mangling: `__private_attr`

## Function and Method Design

### Type Hints

```python
def process_posts(posts: List[dict], days_ago: int = 90) -> int:
    """Process posts older than specified days."""
    pass
```

### Docstrings

```python
def delete_old_content(client: Client, days_ago: int) -> None:
    """
    Delete content older than specified number of days.

    Args:
        client: Authenticated AT Protocol client
        days_ago: Number of days to look back

    Raises:
        ValueError: If days_ago is negative
    """
    pass
```

## Error Handling

### Exception Handling

- Be specific with exception types
- Use `try`/`except` blocks appropriately
- Don't use bare `except:` clauses

```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    return None
```

### Logging

- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Include context in log messages
- Use f-strings for log formatting

## Comments and Documentation

### Inline Comments

- Use sparingly and only when code isn't self-explanatory
- Keep comments up-to-date with code changes
- Write comments that explain "why", not "what"

### Docstrings

- Use triple quotes for all docstrings
- Include Args, Returns, and Raises sections when applicable
- Keep docstrings concise but informative

## Whitespace and Operators

### Operators

- Use spaces around operators: `x = y + z`
- No spaces around `=` in keyword arguments: `func(arg=value)`
- No trailing whitespace

### Commas

- Use trailing commas in multi-line structures
- Space after commas: `[1, 2, 3]`

## Boolean Expressions

### Comparisons

- Use `is` and `is not` for None comparisons
- Use `if sequence:` instead of `if len(sequence) > 0:`
- Use `if not sequence:` instead of `if len(sequence) == 0:`

### Boolean Values

- Don't compare boolean values using `==`
- Use `if condition:` not `if condition == True:`

## Project-Specific Conventions

### Environment Variables

- Use uppercase names with underscores: `DRY_RUN`, `LOG_LEVEL`
- Provide sensible defaults
- Validate environment variables early

### Error Messages

- Include context and suggested actions
- Use consistent formatting across the application
- Log errors with appropriate severity levels

### Configuration

- Keep configuration at the top of files
- Use constants for magic numbers and strings
- Document configuration options clearly
