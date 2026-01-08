# Contributing to E-Commerce Price Scraper

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in Issues
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots if applicable
   - Environment details (OS, Docker version, etc.)

### Suggesting Features

1. Open an issue with the `enhancement` label
2. Describe the feature and its use case
3. Explain why it would be valuable

### Submitting Pull Requests

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Write or update tests
5. Run tests: `make test`
6. Format code: `make format`
7. Lint code: `make lint`
8. Commit with clear messages
9. Push to your fork
10. Create a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/ecommerce-price-scraper.git
cd ecommerce-price-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
make install-dev

# Run tests
make test
```

## Code Standards

### Python Style

- Follow PEP 8
- Use Black for formatting (line length: 88)
- Use meaningful variable names
- Write docstrings for functions and classes

### Testing

- Write tests for new features
- Maintain >80% code coverage
- Use pytest fixtures for common setups
- Mark integration tests appropriately

### Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions/classes
- Comment complex logic
- Update CHANGELOG.md

## Commit Messages

Use clear, descriptive commit messages:

```
feat: Add support for new e-commerce platform
fix: Handle edge case in price extraction
docs: Update installation instructions
test: Add tests for validation pipeline
```

## Questions?

Feel free to open an issue with the `question` label.

Thank you for contributing! 🎉
