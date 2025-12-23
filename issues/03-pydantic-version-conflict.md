# Issue: Pydantic Version Conflict

## What Happened
Docker build fails with:
```
ERROR: Cannot install -r requirements.txt because these package versions have conflicting dependencies.
The conflict is caused by: The user requested pydantic==2.5.3
```

## Root Cause
After upgrading chromadb (0.5.23) and ollama (0.6.1), these packages require a different pydantic version than the pinned 2.5.3 in requirements.txt.

## Resolution
Loosen pydantic version constraint to allow pip to resolve compatible version automatically.

Change from: `pydantic==2.5.3`
Change to: `pydantic>=2.5.3`

This allows pip to install a compatible version that works with all dependencies.
