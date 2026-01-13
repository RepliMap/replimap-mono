# CLI V3 Architecture

This document describes the V3 architecture upgrade for the RepliMap CLI, which transforms it from an "engineer script" into a "production-grade CLI tool".

## Overview

The V3 architecture introduces six core modules:

1. **OutputManager** - Unified output layer with stdout/stderr separation
2. **ConfigManager** - Profile-aware configuration management
3. **StateManager** - Runtime state persistence
4. **ErrorTelemetry** - Structured error handling with reference codes
5. **TelemetryHook** - Usage telemetry placeholder
6. **Parameter System** - Pure data parameter schemas

## Key Architectural Constraints

### Constraint 1: Stdout Hygiene (Zero Tolerance)

In the `replimap/cli/commands/` directory:
- **Prohibited**: `print()`, `console.print()`, `sys.stdout.write()`
- **Required**: `ctx.obj.output.present()` or `ctx.obj.output.log()`

**Reason**: JSON mode stdout must be pure, otherwise CI/CD pipelines that parse JSON output will break.

### Constraint 2: Schema Purity (No Callables)

In `ParameterSchema`:
- **Prohibited**: `choices: Callable`, `default: Callable`, `condition: Callable`
- **Required**: `choices_ref: "aws:regions"` (string references)

**Reason**: Schemas must be JSON serializable for documentation generation and API export.

### Constraint 3: Config/State Separation

- `config.toml`: User explicit settings, can be version controlled
- `state.json`: Program automatic updates, should be `.gitignore`d

## Core Modules

### OutputManager (`replimap/cli/output.py`)

Unified output layer ensuring JSON mode stdout purity.

```python
from replimap.cli.output import OutputManager, OutputFormat

output = OutputManager(format=OutputFormat.JSON, verbose=1)

# Progress/logs go to stderr
output.progress("Scanning...")
output.log("Found 5 VPCs")
output.warn("Rate limited")
output.error("Failed")

# Final output goes to stdout (JSON mode: only ONE write allowed)
output.present({"resources": 42, "status": "complete"})
```

**Key Features**:
- `present()`: Final output to stdout (JSON mode allows only ONE write)
- `log()`, `progress()`, `warn()`, `error()`: All go to stderr
- `spinner()`: Context manager for progress spinners (stderr)
- `prompt()`, `confirm()`, `select()`: Interactive input (stderr prompt, stdin input)

### ConfigManager (`replimap/cli/config.py`)

Profile-aware configuration with priority resolution.

```python
from replimap.cli.config import ConfigManager

config = ConfigManager(
    profile="prod",
    cli_overrides={"region": "us-west-2"}
)

# Resolution priority: CLI > ENV > Profile > Global > Defaults
region = config.get("region")

# Explain where value came from
print(config.explain("region"))
# "region = us-west-2 (from cli)"

# Get all config for a command
scan_config = config.get_all_for_command("scan")
```

**Configuration File Format** (`~/.replimap/config.toml`):
```toml
[global]
region = "us-east-1"
output_format = "terraform"

[profiles.prod]
region = "us-east-1"
output_dir = "./outputs/prod"

[profiles.prod.scan]
parallel_scanners = 8
```

### StateManager (`replimap/cli/state.py`)

Runtime state persistence separate from configuration.

```python
from replimap.cli.state import StateManager

state = StateManager()

# Record scan completion
state.record_scan(
    profile="prod",
    region="us-east-1",
    account_id="123456789",
    duration_seconds=45.2,
    resource_count=150
)

# Get suggested defaults from history
defaults = state.get_suggested_defaults()
# {"profile": "prod", "region": "us-east-1", "vpc_filter": None}
```

**State File** (`~/.replimap/state.json`):
```json
{
  "last_profile": "prod",
  "last_region": "us-east-1",
  "last_scan_time": "2026-01-13T10:30:00Z",
  "cache_exists": true
}
```

### ErrorTelemetry (`replimap/cli/errors.py`)

Structured error handling with reference codes.

```python
from replimap.cli.errors import ErrorTelemetry, ErrorContext, enhanced_cli_error_handler

# Manual capture
context = ErrorContext(command="scan", region="us-east-1", profile="prod")
telemetry = ErrorTelemetry()
ref = telemetry.capture(exception, context)
print(ref.to_display())  # "Error Reference: ERR-EC2-403-A7X9"

# Decorator for commands
@app.command()
@enhanced_cli_error_handler
def scan(ctx: typer.Context):
    ...  # Errors automatically captured with references
```

**Error Reference Format**: `ERR-{SERVICE}-{STATUS}-{HASH}`
- Example: `ERR-EC2-403-A7X9`
- Log file: `~/.replimap/logs/errors/ERR-EC2-403-A7X9_20260113_103000.log`

### GlobalContext (`replimap/cli/context.py`)

Unified context integrating all managers.

```python
from replimap.cli.context import GlobalContext, get_context

# In command
@app.command()
def scan(ctx: typer.Context):
    context = get_context(ctx)

    # Access all managers
    output = context.output
    config = context.config
    state = context.state

    # Use context values
    profile = context.profile
    region = context.region
```

## Parameter System

### Schema (`replimap/cli/params/schema.py`)

Pure data parameter definitions - NO CALLABLES.

```python
from replimap.cli.params import Parameter, ParameterGroup, ParameterType

# Define parameter with string references
region_param = Parameter(
    key="region",
    label="AWS Region",
    type=ParameterType.SELECT,
    help_text="AWS region to scan",
    choices_ref="aws:regions",      # NOT: choices=lambda: get_regions()
    default_ref="config:region",    # NOT: default=lambda: get_default()
    cli_flag="--region",
    cli_short="-r",
)

# Create parameter group
SCAN_PARAMETERS = ParameterGroup(
    name="scan",
    description="AWS Infrastructure Scan",
    parameters=[region_param, ...]
)

# Export as JSON (for documentation, API)
schema_json = SCAN_PARAMETERS.to_json()
```

### Registry (`replimap/cli/params/registry.py`)

Resolves string references to actual values.

```python
from replimap.cli.params import ChoiceRegistry

# Built-in providers
regions = ChoiceRegistry.resolve("aws:regions")
profiles = ChoiceRegistry.resolve("aws:profiles")
frameworks = ChoiceRegistry.resolve("audit:frameworks")

# Register custom provider
ChoiceRegistry.register("custom:values", lambda: ["a", "b", "c"])

# Use with caching
values = ChoiceRegistry.resolve("custom:values", use_cache=True)
```

**Built-in Namespaces**:
- `aws:profiles` - Available AWS profiles
- `aws:regions` - Common AWS regions
- `output:formats` - CLI output formats (text, json, table, quiet)
- `output:iac_formats` - IaC formats (terraform, cloudformation, pulumi)
- `audit:frameworks` - Compliance frameworks (CIS, SOC2, PCI-DSS, etc.)
- `audit:severity` - Severity levels (LOW, MEDIUM, HIGH, CRITICAL)

## Migrating Commands to V3

### Before (V2)
```python
from rich.console import Console
console = Console()

@app.command()
def scan(profile: str, region: str):
    console.print("Scanning...")  # Direct stdout pollution
    result = do_scan()
    console.print(f"Found {len(result)} resources")
    print(json.dumps(result))  # Mixed with progress output
```

### After (V3)
```python
from replimap.cli.context import get_context
from replimap.cli.errors import enhanced_cli_error_handler

@app.command()
@enhanced_cli_error_handler
def scan(ctx: typer.Context):
    context = get_context(ctx)
    output = context.output

    output.progress("Scanning...")           # → stderr
    result = do_scan()
    output.log(f"Found {len(result)} resources")  # → stderr
    output.present(result)                   # → stdout (pure JSON in JSON mode)
```

## Testing

### Schema Purity Test
```python
def test_schema_serializable():
    """Ensure schema has no callables."""
    data = SCAN_PARAMETERS.to_dict()
    json_str = json.dumps(data)  # Fails if callable present
    assert json_str is not None
```

### Stdout Hygiene Test
```python
def test_json_output_parseable():
    """Ensure JSON mode produces valid JSON."""
    output = OutputManager(format=OutputFormat.JSON)
    output.present({"test": "data"})

    # stdout should be valid JSON
    data = json.loads(sys.stdout.getvalue())
    assert data["test"] == "data"
```

## Pre-commit Hooks

The following hooks enforce V3 constraints:

1. **no-print-in-commands**: Checks for `print()` in `replimap/cli/commands/`
2. **schema-purity**: Runs schema serialization tests
3. **stdout-hygiene-test**: Runs JSON output tests

Install with:
```bash
pre-commit install
```

## File Structure

```
replimap/cli/
├── output.py           # OutputManager
├── config.py           # ConfigManager
├── state.py            # StateManager
├── errors.py           # ErrorTelemetry
├── telemetry.py        # TelemetryHook
├── context.py          # GlobalContext
└── params/
    ├── __init__.py
    ├── schema.py       # Parameter, ParameterGroup
    ├── registry.py     # ChoiceRegistry
    └── definitions.py  # SCAN_PARAMETERS, etc.

tests/cli/
├── test_output_manager.py
├── test_config_manager.py
├── test_schema_purity.py
└── test_stdout_hygiene.py
```
