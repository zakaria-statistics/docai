# Issue: Ollama Connection Refused

## What Happened
When adding documents:
```
Error raised by inference endpoint: HTTPConnectionPool(host='host.docker.internal', port=11434):
Max retries exceeded... Connection refused
```

## Root Cause
The Docker container cannot connect to Ollama running on the host machine. Possible causes:
1. **Ollama not running** on host
2. **Ollama not listening** on port 11434
3. **host.docker.internal not resolving** (Linux networking issue)

## Diagnosis
Check if Ollama is running on host:
```bash
# Check if Ollama is running
ps aux | grep ollama

# Check if port 11434 is open
curl http://localhost:11434/api/tags

# Check Ollama models
ollama list
```

## Resolution

### Option 1: Start Ollama on Host
```bash
# Start Ollama service
ollama serve

# Or if using systemd
systemctl start ollama
```

### Option 2: Fix host.docker.internal on Linux
On Linux, `host.docker.internal` may not work. Use host IP instead:

```bash
# Get host IP
ip addr show docker0 | grep inet

# Update docker-compose.yml to use actual host IP
# Change: OLLAMA_BASE_URL=http://host.docker.internal:11434
# To: OLLAMA_BASE_URL=http://172.17.0.1:11434
```

### Option 3: Use Host Network Mode
Add to docker-compose.yml docai service:
```yaml
network_mode: host
```
