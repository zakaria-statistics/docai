# Docker Networking Deep Dive

## Network Fundamentals

### What is Docker Networking?

Docker networking allows containers to communicate with each other and the outside world. Each container can have its own network stack (IP address, routing table, network interfaces).

### Network Drivers

Docker supports several network drivers:

| Driver | Use Case | Isolation |
|--------|----------|-----------|
| **bridge** | Single host, multiple containers | Container-to-container on same host |
| **host** | Container uses host's network | No isolation, shares host IP |
| **none** | No networking | Complete isolation |
| **overlay** | Multi-host (Swarm, Kubernetes) | Cross-host communication |
| **macvlan** | Legacy apps needing MAC address | Direct physical network access |

---

## DocAI Network Architecture

### Network Definition

**File**: `docker-compose.yml`

```yaml
networks:
  docai-network:
    driver: bridge
```

This creates a **user-defined bridge network** named `docai_docai-network`.

### Why User-Defined Bridge?

**Default bridge** vs **User-defined bridge**:

| Feature | Default Bridge | User-Defined Bridge |
|---------|---------------|---------------------|
| **DNS Resolution** | No (use IP or --link) | Yes (use service name) |
| **Container Discovery** | Manual | Automatic |
| **Network Isolation** | All containers can connect | Only containers in same network |
| **Configuration** | Limited | Full control |

### Services on the Network

```yaml
services:
  ollama:
    networks:
      - docai-network

  chromadb:
    networks:
      - docai-network

  docai-api:
    networks:
      - docai-network
```

All services join `docai-network`, enabling communication.

---

## How DNS Resolution Works

### Service Discovery

```
┌─────────────────────────────────────────┐
│     docai-network (172.18.0.0/16)       │
│                                         │
│  ┌─────────────┐   DNS Query:          │
│  │  docai-api  │   "chromadb" → ?      │
│  │ 172.18.0.4  │                        │
│  └──────┬──────┘                        │
│         │                               │
│         └─────► Docker DNS Server       │
│                      │                  │
│                      ▼                  │
│               Returns: 172.18.0.2       │
│                                         │
│  ┌─────────────┐                        │
│  │  chromadb   │◄──── Connection        │
│  │ 172.18.0.2  │                        │
│  └─────────────┘                        │
└─────────────────────────────────────────┘
```

**Key Point**: Containers use **service names** as hostnames, not IP addresses.

### Example from DocAI

**Environment Variable**: `CHROMA_HOST=chromadb`

```python
# src/vector_store/chroma_store.py
client = chromadb.HttpClient(
    host=config.chroma_host,  # "chromadb"
    port=config.chroma_port   # 8000
)
```

**What happens**:
1. Python tries to connect to `chromadb:8000`
2. Container's resolver queries Docker DNS
3. Docker DNS returns ChromaDB container's IP
4. Connection established

---

## Port Mapping

### Internal vs External Ports

```yaml
chromadb:
  ports:
    - "8000:8000"
    #   ▲     ▲
    #   │     └─ Container port (inside network)
    #   └─────── Host port (outside network)
```

### Port Mapping Modes

#### 1. Published Ports (Exposed to Host)

```yaml
docai-api:
  ports:
    - "8080:8080"
```

```
Host Machine (Your Computer)
    │
    │ localhost:8080
    │
    ▼
┌─────────────────────────────┐
│  Docker Port Mapping        │
│  (NAT/iptables rules)       │
└─────────────────────────────┘
    │
    ▼
Container (docai-api)
    │
    │ 0.0.0.0:8080 inside container
    │
    └─► FastAPI listening
```

**Access**:
- From host: `http://localhost:8080`
- From other containers: `http://docai-api:8080`
- From internet: `http://<host-ip>:8080` (if firewall allows)

#### 2. Unpublished Ports (Internal Only)

```yaml
ollama:
  # No ports section - only accessible from network
```

**Access**:
- From other containers: `http://ollama:11434` ✓
- From host: Cannot access ✗
- From internet: Cannot access ✗

**When to use**: Internal services that don't need external access.

---

## Network Isolation

### Security Benefits

```
┌──────────────────────────────────────────┐
│          Docker Host                      │
│                                          │
│  ┌────────────────────┐                  │
│  │  docai-network     │                  │
│  │  (Isolated)        │                  │
│  │                    │                  │
│  │  ┌──────┐ ┌──────┐ │                  │
│  │  │ollama│ │chroma│ │                  │
│  │  └───┬──┘ └──┬───┘ │                  │
│  │      │       │     │                  │
│  │      └───┬───┘     │                  │
│  │          │         │                  │
│  │      ┌───▼───┐     │                  │
│  │      │ API   │     │                  │
│  │      └───────┘     │                  │
│  └────────────────────┘                  │
│                                          │
│  ┌────────────────────┐                  │
│  │  other-network     │                  │
│  │  (Cannot access    │                  │
│  │   docai services)  │                  │
│  │                    │                  │
│  │  ┌──────┐          │                  │
│  │  │ DB   │  ✗       │                  │
│  │  └──────┘          │                  │
│  └────────────────────┘                  │
└──────────────────────────────────────────┘
```

Containers on different networks **cannot** communicate unless explicitly connected.

---

## Inspecting Networks

### View Networks

```bash
# List all networks
docker network ls

# Output:
# NETWORK ID     NAME                  DRIVER
# abc123...      bridge                bridge
# def456...      docai_docai-network   bridge
# ghi789...      host                  host
```

### Inspect Network

```bash
docker network inspect docai_docai-network
```

**Key information**:
- Subnet: `172.18.0.0/16`
- Gateway: `172.18.0.1`
- Connected containers with IPs

### Example Output

```json
{
  "Name": "docai_docai-network",
  "Driver": "bridge",
  "Subnet": "172.18.0.0/16",
  "Gateway": "172.18.0.1",
  "Containers": {
    "abc123": {
      "Name": "docai-ollama",
      "IPv4Address": "172.18.0.2/16"
    },
    "def456": {
      "Name": "docai-chromadb",
      "IPv4Address": "172.18.0.3/16"
    },
    "ghi789": {
      "Name": "docai-api",
      "IPv4Address": "172.18.0.4/16"
    }
  }
}
```

---

## Testing Connectivity

### From Container to Container

```bash
# Enter API container
docker exec -it docai-api sh

# Test connectivity to ChromaDB
curl http://chromadb:8000/api/v1/heartbeat
# Should return: {"nanosecond heartbeat": ...}

# Test DNS resolution
nslookup chromadb
# Should return: Server: 127.0.0.11, Address: 172.18.0.3

# Test connectivity to Ollama
curl http://ollama:11434/api/tags
# Should return: {"models": [...]}
```

### From Host to Container

```bash
# From your computer
curl http://localhost:8080/health    # Works (port published)
curl http://localhost:8000/api/v1/heartbeat  # Works (port published)
curl http://localhost:11434/api/tags # Works (port published)
```

### Troubleshooting

```bash
# If connection fails, check:

# 1. Is container running?
docker ps | grep chromadb

# 2. Is it on the right network?
docker inspect chromadb | grep -A 10 Networks

# 3. Can it be pinged?
docker exec docai-api ping -c 2 chromadb

# 4. Are ports listening?
docker exec chromadb netstat -tlnp | grep 8000
```

---

## Advanced: Multiple Networks

### Use Case: Separate Frontend/Backend

```yaml
networks:
  frontend:
  backend:

services:
  web:
    networks:
      - frontend

  api:
    networks:
      - frontend
      - backend

  database:
    networks:
      - backend
```

**Result**:
- `web` can talk to `api` (both on frontend)
- `api` can talk to `database` (both on backend)
- `web` **cannot** talk to `database` (not on same network)

---

## Network Performance

### Bandwidth

**Container-to-container** (same host):
- Uses kernel networking (veth pairs)
- Near-native performance (~10-20 Gbps)
- Minimal overhead

**Container-to-host**:
- Through port mapping (iptables NAT)
- Slight overhead (~5-10%)

### Latency

**Internal network**: Sub-millisecond (<0.1ms)
**Port-mapped**: 1-2ms overhead

---

## Common Patterns

### 1. Service Dependencies

```yaml
docai-api:
  depends_on:
    chromadb:
      condition: service_healthy
    ollama:
      condition: service_healthy
```

**Why**: Ensures chromadb/ollama are ready before API starts.

### 2. Health Checks

```yaml
chromadb:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
    interval: 30s
    timeout: 10s
    retries: 5
```

**Why**: Docker monitors service health, can restart if unhealthy.

### 3. DNS Aliases

```yaml
chromadb:
  networks:
    docai-network:
      aliases:
        - vector-db
        - chroma
```

**Result**: Accessible via `chromadb`, `vector-db`, or `chroma`.

---

## Security Best Practices

### 1. Minimize Published Ports

**Bad**:
```yaml
chromadb:
  ports:
    - "8000:8000"  # Exposed to internet!
```

**Good**:
```yaml
chromadb:
  # No ports - internal only
```

### 2. Use Internal Networks

```yaml
networks:
  public:
    # Internet-facing
  private:
    internal: true  # No external access
```

### 3. Network Policies

For production, use **overlay networks** with **encryption**:

```yaml
networks:
  encrypted:
    driver: overlay
    driver_opts:
      encrypted: "true"
```

---

## Docker Compose Networking Commands

```bash
# View network details
docker-compose config

# Recreate network
docker-compose down && docker-compose up -d

# Connect running container to network
docker network connect docai_docai-network my-container

# Disconnect container
docker network disconnect docai_docai-network my-container

# Remove unused networks
docker network prune
```

---

## Container-to-Host Communication

### Problem: Accessing Services on Host

Containers run in isolated networks. How do they access services running on the **host machine** (not in containers)?

**Example**: Ollama running on host port 11434. Container needs to connect to it.

---

### Solution 1: host.docker.internal (Recommended)

**What it is**: Special DNS name that resolves to the host's IP address.

```yaml
docai-api:
  environment:
    - OLLAMA_BASE_URL=http://host.docker.internal:11434
  extra_hosts:
    - "host.docker.internal:host-gateway"
```

**How it works**:

```
┌─────────────────────────────────────────┐
│  Container (172.18.0.4)                 │
│                                         │
│  DNS Query: "host.docker.internal"      │
│       ↓                                 │
│  Docker DNS: Returns 172.17.0.1         │
│       ↓                                 │
│  Connect to 172.17.0.1:11434            │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Host Machine (172.17.0.1)              │
│                                         │
│  Ollama listening on 0.0.0.0:11434      │
│  or 127.0.0.1:11434                     │
└─────────────────────────────────────────┘
```

**Requirements**:
- `extra_hosts: - "host.docker.internal:host-gateway"` (Linux)
- Automatically works on Mac/Windows
- Service on host must listen on `0.0.0.0` or Docker bridge IP

**Advantages**:
- ✅ Portable across environments
- ✅ Clear intent (name says "host")
- ✅ Automatic IP resolution

**Disadvantages**:
- ❌ Needs `extra_hosts` on Linux
- ❌ Not available in older Docker versions

---

### Solution 2: Bridge Gateway IP (Direct)

**What it is**: Use the Docker bridge network's gateway IP directly.

```bash
# Find Docker bridge gateway IP
ip addr show docker0 | grep inet
# inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
```

```yaml
docai-api:
  environment:
    - OLLAMA_BASE_URL=http://172.17.0.1:11434
```

**How it works**:

```
Docker Bridge Network (docker0)
    Subnet: 172.17.0.0/16
    Gateway: 172.17.0.1 ← This is the host!

Container (172.17.0.2)
    ↓
    Connect to 172.17.0.1:11434
    ↓
Host (acts as gateway)
    ↓
Ollama listening on 172.17.0.1:11434
```

**Advantages**:
- ✅ Direct, no DNS needed
- ✅ Works in all Docker versions
- ✅ Explicit control

**Disadvantages**:
- ❌ Hardcoded IP (less portable)
- ❌ IP might change if network recreated
- ❌ Different across machines

---

### Solution 3: Host Network Mode (Nuclear Option)

**What it is**: Container uses host's network directly (no isolation).

```yaml
docai-api:
  network_mode: host
  environment:
    - OLLAMA_BASE_URL=http://localhost:11434
```

**How it works**:

```
No container network!
Container shares host's network stack.

Container process sees:
- localhost = host localhost
- 0.0.0.0 = host interfaces
- Same IP as host
```

**Advantages**:
- ✅ Simple (use localhost)
- ✅ No network overhead

**Disadvantages**:
- ❌ No network isolation
- ❌ Port conflicts (can't publish ports)
- ❌ Security risk
- ❌ Loses Docker networking benefits

**When to use**: Never for production. Only for debugging.

---

### Comparison

| Method | Portability | Security | Performance | Use Case |
|--------|-------------|----------|-------------|----------|
| **host.docker.internal** | High | Good | Good | Recommended |
| **Bridge Gateway IP** | Low | Good | Good | Fallback |
| **Host Network** | Medium | Poor | Best | Debugging only |

---

### DocAI Configuration

**Currently using**: `host.docker.internal` with `host-gateway`

```yaml
# docker-compose.yml
services:
  docai-api:
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

**Why**:
- Host Ollama already running (port 11434 occupied)
- Models already downloaded (~5GB saved)
- Portable configuration

**Verification**:
```bash
# From inside container
docker exec docai-api curl http://host.docker.internal:11434/api/tags

# Should return: {"models": [...]}
```

---

### Troubleshooting Host Access

#### Container can't reach host service

**Check 1**: Service listening on correct interface

```bash
# Bad: Only localhost
ollama serve --host 127.0.0.1

# Good: All interfaces
ollama serve --host 0.0.0.0
```

**Check 2**: Firewall allows Docker

```bash
# Check if Docker bridge can access
sudo iptables -L | grep 11434
```

**Check 3**: host.docker.internal resolves

```bash
docker exec docai-api ping -c 2 host.docker.internal
docker exec docai-api nslookup host.docker.internal
```

**Check 4**: Use bridge IP directly

```bash
# Find gateway
ip addr show docker0 | grep inet

# Test from container
docker exec docai-api curl http://172.17.0.1:11434/api/tags
```

---

## Summary

| Concept | DocAI Implementation |
|---------|---------------------|
| **Network Type** | User-defined bridge |
| **Network Name** | `docai-network` |
| **DNS** | Automatic (use service names) |
| **Published Ports** | 8080 (API), 8000 (ChromaDB) |
| **Host Access** | `host.docker.internal:11434` (Ollama on host) |
| **Internal Services** | All services can communicate |
| **External Access** | Only via published ports |
| **Isolation** | Containers on other networks cannot access |

**Key Takeaways**:
- Docker networking provides DNS-based service discovery and network isolation
- Containers can access host services via `host.docker.internal` or bridge gateway IP
- Currently using host Ollama to avoid port conflicts and save downloads
