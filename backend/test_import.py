"""Test different import paths for langgraph-checkpoint-postgres"""

import sys

# Try different import paths
import_paths = [
    "langgraph.checkpoint.postgres.aio",
    "langgraph_checkpoint_postgres.aio",
    "langgraph_checkpoint_postgres",
]

for path in import_paths:
    try:
        module = __import__(path, fromlist=["AsyncPostgresSaver"])
        if hasattr(module, "AsyncPostgresSaver"):
            print(f"SUCCESS: {path}")
            print(f"  AsyncPostgresSaver found: {hasattr(module, 'AsyncPostgresSaver')}")
        else:
            print(f"PARTIAL: {path} - module imported but AsyncPostgresSaver not found")
            print(f"  Available attributes: {[x for x in dir(module) if not x.startswith('_')]}")
    except ImportError as e:
        print(f"FAILED: {path} - {e}")
    except Exception as e:
        print(f"ERROR: {path} - {type(e).__name__}: {e}")

