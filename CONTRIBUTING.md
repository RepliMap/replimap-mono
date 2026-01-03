# Contributing to RepliMap

Thank you for your interest in contributing to RepliMap!

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/replimap.git
   cd replimap
   ```
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
4. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Running Tests

```bash
pytest
```

### Code Style

We use `ruff` for linting and formatting:

```bash
ruff check .
ruff format .
```

### Type Checking

```bash
mypy replimap
```

## Pull Request Guidelines

1. Create a feature branch from `main`
2. Make your changes with clear commit messages
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request with a clear description

## Reporting Issues

- **Bug reports**: [GitHub Issues](https://github.com/RepliMap/replimap/issues)
- **Security issues**: [support@replimap.com](mailto:support@replimap.com)

## Questions?

- **General**: [hello@replimap.com](mailto:hello@replimap.com)
- **Discussions**: [GitHub Discussions](https://github.com/RepliMap/replimap/discussions)
