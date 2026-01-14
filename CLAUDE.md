# Claude Code Guidelines for RepliMap

This document provides guidelines for AI assistants (Claude) working on the RepliMap codebase.

## Project Overview

RepliMap is an AWS Infrastructure Intelligence Engine that scans AWS environments and builds dependency graphs for visualization, cost analysis, security auditing, and infrastructure-as-code generation.

## Pre-Commit Checklist (CI Jobs)

**IMPORTANT**: Always run these commands before commit/push. CI will fail if any of these have errors:

```bash
# 1. Format code (REQUIRED - fixes formatting issues)
uv run ruff format .

# 2. Lint code (REQUIRED - must pass with no errors)
uv run ruff check .

# 3. Run tests with coverage (REQUIRED - must pass)
uv run pytest tests/ -v --cov=replimap --cov-report=xml --cov-report=term
```

### Quick Pre-Commit (for faster iteration)

```bash
# Fast check during development (skip coverage report)
uv run ruff format . && uv run ruff check . && uv run pytest tests/ --ignore=tests/integration/ -x -q
```

### Common CI Failures and Fixes

| Error | Fix |
|-------|-----|
| `ruff format` changes files | Run `uv run ruff format .` and commit the changes |
| `ruff check` shows errors | Fix the linting errors or add `# noqa: XXXX` if intentional |
| Test failures | Fix the failing tests before committing |
| Import sorting | `ruff format .` handles this automatically |

### Minimum Test Coverage Requirements

- All new code must have corresponding tests
- Target: 80%+ coverage for new modules
- Critical paths (CLI commands, storage, scanners) must have 100% happy path coverage
- Coverage report is generated in `coverage.xml` for CI integration

## Architectural Patterns (MUST FOLLOW)

### 1. CLI Framework

**Profile/Region Inheritance Pattern:**
```python
# Global options are captured in main callback and stored in GlobalContext
# Subcommands should read from ctx.obj which contains GlobalContext

# For command groups (like snapshot), the callback should:
# 1. Read from parent GlobalContext
# 2. Merge with local options
# 3. Pass to subcommands via ctx.obj

# Example: snapshot command callback
parent_obj = ctx.parent.obj if ctx.parent else None
if parent_obj and hasattr(parent_obj, "get"):
    global_profile = parent_obj.get("profile")
    global_region = parent_obj.get("region")
ctx.obj["profile"] = profile or global_profile
ctx.obj["region"] = region or global_region
```

**Subcommand Options:**
- Subcommands that need `-p`/`-r` should define their own options for flexibility
- This allows `cmd subcmd -p profile` to work (not just `cmd -p profile subcmd`)

### 2. Unified SQLite Storage

**Always use GraphEngineAdapter, NOT GraphEngine:**
```python
# CORRECT:
from replimap.core.unified_storage import GraphEngineAdapter
graph = GraphEngineAdapter(db_path=":memory:")

# DEPRECATED (shows warning):
from replimap.core import GraphEngine  # Avoid this
```

**Cache Version vs Schema Version:**
- `CACHE_VERSION` ("2.0") - stored in metadata, checked by CacheManager
- `schema_version` (integer 2) - internal SQLite schema version
- After schema migration, cache version metadata must be updated

**Dependency Population:**
- When loading from SQLite cache, dependencies are stored in edges table
- Use `_ensure_dependencies_loaded()` or `_populate_dependencies_from_edges()`
- ResourceNode.dependencies must be populated before returning to callers

### 3. Graph Visualization

**Grouping/Aggregation:**
- GraphBuilder groups by subnet (for EC2 instances)
- SmartAggregator groups by VPC (for other resources)
- DO NOT re-aggregate already-grouped nodes (`is_group=True`)
- Edges must reference group IDs, not individual member IDs

**Edge Building:**
```python
# When resources are grouped, edges should:
# 1. Use group_id as source (not individual resource ID)
# 2. Resolve target to group_id if target was also grouped
# 3. Use _resolve_target() to map individual IDs to group IDs
```

### 4. Async Resource Cleanup

**Always close async clients:**
```python
async def run_detection():
    try:
        return await detector.scan(graph)
    finally:
        await detector.close()  # Always close!
```

### 5. Error Handling

**Use enhanced_cli_error_handler decorator:**
```python
@app.command()
@enhanced_cli_error_handler
def my_command(...):
    ...
```

## Code Style Guidelines

### Imports

```python
# Standard library
from __future__ import annotations
import asyncio
from typing import Any

# Third-party
import typer
from rich.console import Console

# Local
from replimap.core.unified_storage import GraphEngineAdapter
from replimap.cli.errors import enhanced_cli_error_handler
```

### Type Hints

- Use `| None` instead of `Optional[]`
- Use `list[]` instead of `List[]`
- Use `dict[]` instead of `Dict[]`

### Docstrings

```python
def function(param: str) -> bool:
    """
    Short description.

    Args:
        param: Description of param

    Returns:
        Description of return value
    """
```

## Testing Patterns

### Unit Test Structure

```python
class TestMyFeature:
    """Test suite for MyFeature."""

    def test_happy_path(self) -> None:
        """Test normal operation."""
        ...

    def test_error_handling(self) -> None:
        """Test error cases."""
        ...

    def test_edge_cases(self) -> None:
        """Test boundary conditions."""
        ...
```

### CLI Command Tests

```python
# Test pattern for CLI commands (from test_unified_storage_e2e.py)
def test_transfer_command_pattern(self) -> None:
    """Test transfer command uses storage correctly."""
    engine = UnifiedGraphEngine()
    # Add test data...

    # Verify command can:
    # 1. Read from graph
    # 2. Process data
    # 3. Output results
```

### Integration Test Markers

```python
@pytest.mark.integration
def test_aws_integration():
    """Requires AWS credentials."""
    ...
```

## Common Gotchas

### 1. Cache Version Mismatch

If cache is rejected after schema migration, ensure:
```python
# In _load_sqlite, after schema migration:
if schema_version >= 2 and version in (None, "1.0"):
    engine.set_metadata("version", CACHE_VERSION)
```

### 2. Missing Dependencies in Loaded Resources

Resources loaded from SQLite don't have dependencies populated:
```python
# Wrong:
resource = graph.get_resource(id)
for dep in resource.dependencies:  # Empty!

# Right:
resource = graph.get_resource(id)  # Now auto-populates
# Or explicitly:
self._ensure_dependencies_loaded(resource)
```

### 3. Double Aggregation

SmartAggregator must skip already-grouped nodes:
```python
already_grouped = [n for n in type_nodes if n.get("is_group")]
individual_nodes = [n for n in type_nodes if not n.get("is_group")]
# Only aggregate individual_nodes
```

### 4. Typer Subcommand Options

Options after subcommand name go to subcommand, not parent:
```
replimap snapshot -p demo list  # -p goes to snapshot callback
replimap snapshot list -p demo  # -p goes to list command (needs -p option)
```

## Documentation Updates

When making changes:

1. **CHANGELOG.md**: Add entry for user-facing changes
2. **docs/technical-reference.md**: Update for API changes
3. **README.md**: Update if CLI interface changes
4. **Docstrings**: Update affected function/class docs

## CI/CD Requirements

### Pull Request Checklist

- [ ] All tests pass (`uv run pytest tests/ --ignore=tests/integration/`)
- [ ] No linting errors (`uv run ruff check replimap/`)
- [ ] CHANGELOG.md updated (if user-facing change)
- [ ] New tests added for new functionality
- [ ] Existing tests updated if behavior changed

### Commit Message Format

```
type: short description

Longer explanation if needed.

- Bullet points for multiple changes
- Reference issues if applicable
```

Types: `fix`, `feat`, `refactor`, `docs`, `test`, `chore`

## Quick Reference Commands

```bash
# === CI COMMANDS (run before every commit) ===
uv run ruff format .                                    # Format code
uv run ruff check .                                     # Lint code
uv run pytest tests/ -v --cov=replimap --cov-report=xml --cov-report=term  # Tests + coverage

# === DEVELOPMENT COMMANDS ===
# Run all tests (quick, no coverage)
uv run pytest tests/ --ignore=tests/integration/ -x -q

# Run specific test file
uv run pytest tests/test_cache.py -v

# Run specific test
uv run pytest tests/test_cache.py::TestCacheManager::test_save -v

# Check CLI help
uv run replimap --help
uv run replimap <command> --help

# Type checking (optional)
uv run mypy replimap/ --ignore-missing-imports

# === ONE-LINER FOR PRE-COMMIT ===
uv run ruff format . && uv run ruff check . && uv run pytest tests/ -v --cov=replimap --cov-report=xml --cov-report=term
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `replimap/cli/__init__.py` | Main CLI app and global options |
| `replimap/cli/context.py` | GlobalContext for profile/region |
| `replimap/core/unified_storage/` | SQLite-based graph storage |
| `replimap/core/cache_manager.py` | Graph caching layer |
| `replimap/graph/builder.py` | Graph visualization builder |
| `replimap/graph/aggregation.py` | Node aggregation logic |
