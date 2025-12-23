# Issue: docai-api Uvicorn Command Error

## What Happened
docai-api container fails with:
```
Error: No such command 'uvicorn'.
```

## Root Cause
The Dockerfile has `ENTRYPOINT ["python3", "-m", "src.main"]` which is the CLI application. When docker-compose.yml specifies:
```yaml
command: ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8080"]
```

It tries to run `python3 -m src.main uvicorn src.api:app ...` which fails because the CLI doesn't have a 'uvicorn' command.

## Resolution
Override the entrypoint in docker-compose.yml for the docai-api service to run uvicorn directly.

Change:
```yaml
command: ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8080"]
```

To:
```yaml
entrypoint: ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8080"]
```

Or keep command and remove the Dockerfile entrypoint for the API container.
