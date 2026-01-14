"""
Migration utility for legacy JSON graph files to SQLite.

This module provides tools to migrate from the old JSON-based graph
storage to the new SQLite-based UnifiedGraphEngine.

Usage:
    # Migrate a single file
    python -m replimap.core.unified_storage.migrate path/to/graph.json

    # Migrate all graphs in cache directory
    python -m replimap.core.unified_storage.migrate ~/.replimap/cache/graphs/

    # Programmatic usage
    from replimap.core.unified_storage.migrate import migrate_json_to_sqlite
    migrate_json_to_sqlite("graph.json", "graph.db")
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

from .adapter import GraphEngineAdapter
from .base import Edge, Node
from .engine import UnifiedGraphEngine

logger = logging.getLogger(__name__)


def migrate_json_to_sqlite(
    json_path: str | Path,
    sqlite_path: str | Path | None = None,
    delete_json: bool = False,
) -> str:
    """
    Migrate a JSON graph file to SQLite format.

    Args:
        json_path: Path to the source JSON file
        sqlite_path: Path for the output SQLite file. If None, uses
                    same name with .db extension.
        delete_json: If True, delete the JSON file after successful migration

    Returns:
        Path to the created SQLite database

    Raises:
        FileNotFoundError: If the JSON file doesn't exist
        json.JSONDecodeError: If the JSON file is invalid
    """
    json_path = Path(json_path)

    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    if sqlite_path is None:
        sqlite_path = json_path.with_suffix(".db")
    else:
        sqlite_path = Path(sqlite_path)

    logger.info(f"Migrating {json_path} to {sqlite_path}")

    # Load JSON data
    with open(json_path) as f:
        data = json.load(f)

    # Create SQLite database
    engine = UnifiedGraphEngine(db_path=str(sqlite_path))

    try:
        # Convert and add nodes
        nodes_added = 0
        for node_data in data.get("nodes", []):
            node = _convert_node_data(node_data)
            engine.add_node(node)
            nodes_added += 1

        # Convert and add edges
        edges_added = 0
        for edge_data in data.get("edges", []):
            edge = Edge(
                source_id=edge_data["source"],
                target_id=edge_data["target"],
                relation=edge_data.get("relation", "belongs_to"),
            )
            engine.add_edge(edge)
            edges_added += 1

        # Store metadata
        if "version" in data:
            engine.set_metadata("version", data["version"])
        engine.set_metadata("migrated_from", str(json_path))
        engine.set_metadata("original_format", "json")

        logger.info(f"Migration complete: {nodes_added} nodes, {edges_added} edges")

        # Delete JSON if requested
        if delete_json:
            json_path.unlink()
            logger.info(f"Deleted original JSON file: {json_path}")

    finally:
        engine.close()

    return str(sqlite_path)


def migrate_json_to_adapter(
    json_path: str | Path,
    cache_dir: str | Path | None = None,
) -> GraphEngineAdapter:
    """
    Load a JSON graph file into a GraphEngineAdapter.

    This is a convenience function for code migration - it reads a legacy
    JSON file and returns a GraphEngineAdapter that can be used with the
    old API while storing data in SQLite.

    Args:
        json_path: Path to the source JSON file
        cache_dir: Optional cache directory for persistent storage

    Returns:
        GraphEngineAdapter with the loaded data
    """
    json_path = Path(json_path)

    with open(json_path) as f:
        data = json.load(f)

    return GraphEngineAdapter.from_dict(
        data,
        cache_dir=str(cache_dir) if cache_dir else None,
    )


def migrate_cache_directory(
    cache_dir: str | Path,
    delete_json: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Migrate all JSON graph files in a cache directory to SQLite.

    Args:
        cache_dir: Directory containing JSON graph files
        delete_json: If True, delete JSON files after successful migration
        dry_run: If True, only report what would be migrated

    Returns:
        Dictionary with migration statistics
    """
    cache_dir = Path(cache_dir)

    if not cache_dir.exists():
        return {"error": f"Directory not found: {cache_dir}", "migrated": 0}

    json_files = list(cache_dir.glob("*.json"))

    if dry_run:
        return {
            "dry_run": True,
            "files_found": len(json_files),
            "files": [str(f) for f in json_files],
        }

    results = {
        "migrated": 0,
        "failed": 0,
        "skipped": 0,
        "details": [],
    }

    for json_file in json_files:
        sqlite_file = json_file.with_suffix(".db")

        # Skip if SQLite already exists and is newer
        if sqlite_file.exists():
            if sqlite_file.stat().st_mtime > json_file.stat().st_mtime:
                results["skipped"] += 1
                results["details"].append(
                    {
                        "file": str(json_file),
                        "status": "skipped",
                        "reason": "SQLite file is newer",
                    }
                )
                continue

        try:
            migrate_json_to_sqlite(json_file, sqlite_file, delete_json=delete_json)
            results["migrated"] += 1
            results["details"].append(
                {
                    "file": str(json_file),
                    "status": "migrated",
                    "output": str(sqlite_file),
                }
            )
        except Exception as e:
            results["failed"] += 1
            results["details"].append(
                {
                    "file": str(json_file),
                    "status": "failed",
                    "error": str(e),
                }
            )
            logger.error(f"Failed to migrate {json_file}: {e}")

    return results


def _convert_node_data(node_data: dict[str, Any]) -> Node:
    """Convert legacy node dictionary to new Node format."""
    # Handle both old ResourceNode format and direct Node format
    attributes = {}

    # ResourceNode specific fields go into attributes
    if "config" in node_data:
        attributes["config"] = node_data["config"]
    if "tags" in node_data:
        attributes["tags"] = node_data["tags"]
    if "dependencies" in node_data:
        attributes["dependencies"] = node_data["dependencies"]
    if "terraform_name" in node_data:
        attributes["terraform_name"] = node_data["terraform_name"]
    if "original_name" in node_data:
        attributes["original_name"] = node_data["original_name"]
    if "arn" in node_data:
        attributes["arn"] = node_data["arn"]

    return Node(
        id=node_data["id"],
        type=node_data.get("resource_type", node_data.get("type", "unknown")),
        name=node_data.get("original_name", node_data.get("name")),
        region=node_data.get("region"),
        account_id=node_data.get("account_id"),
        attributes=attributes,
        is_phantom=node_data.get("is_phantom", False),
        phantom_reason=node_data.get("phantom_reason"),
    )


def main() -> int:
    """Command-line entry point for migration."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate RepliMap JSON graphs to SQLite format"
    )
    parser.add_argument(
        "path",
        help="Path to JSON file or directory containing JSON files",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete JSON files after successful migration",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without making changes",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(message)s")

    path = Path(args.path)

    if path.is_file():
        # Single file migration
        if args.dry_run:
            print(f"Would migrate: {path}")
            print(f"Output: {path.with_suffix('.db')}")
            return 0

        try:
            output = migrate_json_to_sqlite(path, delete_json=args.delete)
            print(f"Migrated: {path} -> {output}")
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    elif path.is_dir():
        # Directory migration
        results = migrate_cache_directory(
            path,
            delete_json=args.delete,
            dry_run=args.dry_run,
        )

        if args.dry_run:
            print(f"Found {results['files_found']} JSON files:")
            for f in results.get("files", []):
                print(f"  - {f}")
            return 0

        print("Migration complete:")
        print(f"  Migrated: {results['migrated']}")
        print(f"  Failed: {results['failed']}")
        print(f"  Skipped: {results['skipped']}")

        if results["failed"] > 0:
            return 1
        return 0

    else:
        print(f"Error: Path not found: {path}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
