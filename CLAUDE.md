# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Travian strategy game automation and analysis project built with Python 3.9+. The project uses `uv` for dependency management and includes web scraping capabilities for extracting building and resource data from Travian game knowledge bases.

## Development Commands

### Environment Setup
```bash
make install  # Creates virtual environment and installs pre-commit hooks
uv sync       # Syncs dependencies from uv.lock
```

### Code Quality and Testing
```bash
make check    # Runs pre-commit hooks, linting, and type checking
make test     # Runs pytest with coverage
uv run ruff check    # Manual linting
uv run ty check      # Type checking with ty
```

### Documentation
```bash
make docs-test  # Test documentation build
make docs       # Build and serve documentation with MkDocs
```

### Building
```bash
make build  # Creates wheel file
```

### Pre-commit
```bash
uv run pre-commit run -a  # Run all pre-commit hooks manually
```

## Architecture

### Core Structure
- `src/travian_strategy/` - Main package containing core functionality
- `src/travian_strategy/data_pipeline/scraper.py` - Web scraping module for Travian knowledge base
- `tests/` - Test directory using pytest

### Data Pipeline Components
The scraper module contains classes for extracting data from Travian knowledge bases:
- `Scraper` - Base scraper class using requests and BeautifulSoup
- `ResourcesScraper` - Specialized scraper for building resource costs using Selenium with Firefox
- Supports both headless and visible browser modes for debugging

### Dependencies
Key libraries in use:
- `selenium` + `geckodriver` for dynamic web scraping
- `beautifulsoup4` + `lxml` for HTML parsing
- `pydantic` for data modeling
- `requests` for HTTP requests
- `pyautogui` for automation
- `schedule` for task scheduling

## Development Notes

### Testing
- Uses pytest with coverage reporting
- Coverage config in pyproject.toml
- Tests should be placed in `tests/` directory

### Code Style
- Uses Ruff for linting and formatting (configured in pyproject.toml)
- Line length: 120 characters
- Python 3.9+ target version
- Pre-commit hooks enforce code quality

### Type Checking
- Uses `ty` for static type checking
- Type hints are expected throughout the codebase

### Documentation
- MkDocs with Material theme
- Documentation source in `docs/`
- Docstrings should follow the project's established format (see `foo.py` example)