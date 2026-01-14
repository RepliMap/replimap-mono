#!/bin/bash
# sync-config.sh - Sync shared configuration from packages/config to CLI
#
# This script copies the generated Python configuration from the shared
# config package to the CLI's _generated directory.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_ROOT="$(dirname "$SCRIPT_DIR")"
MONO_ROOT="$(dirname "$(dirname "$CLI_ROOT")")"
CONFIG_DIST="$MONO_ROOT/packages/config/dist"
CLI_GENERATED="$CLI_ROOT/replimap/_generated"

echo "Syncing shared configuration to CLI..."
echo "  Source: $CONFIG_DIST"
echo "  Target: $CLI_GENERATED"

# Create _generated directory if it doesn't exist
mkdir -p "$CLI_GENERATED"

# Create __init__.py if it doesn't exist
if [ ! -f "$CLI_GENERATED/__init__.py" ]; then
    echo '"""Auto-generated configuration from packages/config."""' > "$CLI_GENERATED/__init__.py"
fi

# Check if config.py exists in the source
if [ ! -f "$CONFIG_DIST/config.py" ]; then
    echo "Error: $CONFIG_DIST/config.py not found."
    echo "Please run 'pnpm build:config' first to generate the configuration."
    exit 1
fi

# Copy the Python config
cp "$CONFIG_DIST/config.py" "$CLI_GENERATED/config.py"

echo "Configuration synced successfully!"
