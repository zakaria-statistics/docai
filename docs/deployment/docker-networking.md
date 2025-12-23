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

---

## DocAI System Components & Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Host Machine (k8s01 - Linux)                               │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Ollama Service (Native Process)                     │   │
│  │  - Port: 11434                                       │   │
│  │  - Models: llama3.1:8b, nomic-embed-text             │   │
│  │  - Accessible at: 172.26.0.1 (from containers)      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Docker Network: docai-network (172.26.0.0/16)      │   │
│  │                                                      │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │  chromadb (Container)                        │   │   │
│  │  │  - Image: chromadb/chroma:0.5.23             │   │   │
│  │  │  - Internal: chromadb:8000                   │   │   │
│  │  │  - External: localhost:8000                  │   │   │
│  │  │  - Role: Vector database storage             │   │   │
│  │  │  - Data: /data (persistent volume)           │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  │                                                      │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │  docai-api (Container)                       │   │   │
│  │  │  - Image: llm-dir-docai-api                  │   │   │
│  │  │  - Internal: docai-api:8080                  │   │   │
│  │  │  - External: localhost:8080                  │   │   │
│  │  │  - Role: REST API server                     │   │   │
│  │  │  - Entrypoint: uvicorn                       │   │   │
│  │  │  - Connects to: chromadb + ollama            │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  │                                                      │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │  docai (Container - Ephemeral)               │   │   │
│  │  │  - Image: llm-dir-docai                      │   │   │
│  │  │  - Profile: cli (manual start)               │   │   │
│  │  │  - Role: Interactive CLI                     │   │   │
│  │  │  - Entrypoint: python -m src.main            │   │   │
│  │  │  - Connects to: chromadb + ollama            │   │   │
│  │  │  - Removed after use (--rm flag)             │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Persistent Storage (Host Volumes)                  │   │
│  │  - ./data/documents   → Document files              │   │
│  │  - ./data/sessions    → Chat history                │   │
│  │  - ./data/vector_db   → Local embeddings cache      │   │
│  │  - ./test_docs        → Test documents (read-only)  │   │
│  │                                                      │   │
│  │  Docker Volumes:                                     │   │
│  │  - chroma_data        → ChromaDB persistent data    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### 1. Ollama (Host Process)
**Location**: Runs natively on host machine, not in container
**Why on host**:
- Already installed and configured
- Models already downloaded (~5GB for llama3.1:8b)
- Can utilize GPU if available
- No port conflicts (11434 already in use)

**Access from containers**: `http://172.26.0.1:11434`
**Access from host**: `http://localhost:11434`

**Responsibilities**:
- Generate text completions (LLM inference)
- Create embeddings for documents and queries
- Heavy compute workload

#### 2. ChromaDB (Container)
**Location**: Docker container in docai-network
**Image**: `chromadb/chroma:0.5.23`
**Why containerized**:
- Isolated environment
- Reproducible deployment
- Version control
- Easy backup/restore

**Endpoints**:
- Internal: `http://chromadb:8000` (from containers)
- External: `http://localhost:8000` (from host)

**Responsibilities**:
- Store vector embeddings
- Perform similarity search
- Return relevant document chunks
- Manage collections and tenants

**Data persistence**: Docker volume `chroma_data` → `/data` in container

#### 3. docai-api (Container)
**Location**: Docker container in docai-network
**Image**: Built from `Dockerfile`
**Why containerized**:
- Portable across environments
- Easy scaling (multiple instances)
- Dependency isolation
- Production-ready

**Endpoints**:
- Internal: `http://docai-api:8080` (from containers)
- External: `http://localhost:8080` (from host/internet)

**Responsibilities**:
- Expose REST API endpoints
- Process document uploads
- Handle queries and summarization requests
- Orchestrate between ChromaDB and Ollama
- Serve health checks

**API Examples**:
```bash
# Health check
curl http://localhost:8080/health

# Upload document
curl -X POST http://localhost:8080/api/upload \
  -F "file=@document.pdf"

# Query documents
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main findings?"}'
```

#### 4. docai CLI (Container)
**Location**: Docker container (ephemeral)
**Image**: Same Dockerfile as API
**Why containerized**:
- Consistent environment
- No Python dependency conflicts
- Same codebase as API

**Launch**: Requires `--profile cli` flag
**Lifecycle**: Created on `run`, removed on exit (`--rm`)

**Responsibilities**:
- Interactive terminal interface
- Same functionality as API (add, query, summarize, etc.)
- Direct user interaction
- Session management

**Usage**:
```bash
# One-off command (container removed after)
docker compose --profile cli run --rm docai list

# Interactive session
docker compose --profile cli run --rm docai chat
```

---

### Data Flow & Interactions

#### Document Indexing Flow
```
┌──────┐
│ User │ uploads PDF via CLI or API
└───┬──┘
    │
    ▼
┌─────────────────┐
│  docai / API    │ Parse PDF, chunk text
└───┬─────────────┘
    │ text chunks
    ▼
┌─────────────────┐
│  Ollama (Host)  │ Generate embeddings
│  172.26.0.1     │ nomic-embed-text model
└───┬─────────────┘
    │ vector embeddings
    ▼
┌─────────────────┐
│  ChromaDB       │ Store embeddings + metadata
│  chromadb:8000  │ Create/update collection
└─────────────────┘
```

#### Query Processing Flow
```
┌──────┐
│ User │ asks "What are the main findings?"
└───┬──┘
    │
    ▼
┌─────────────────┐
│  docai / API    │ Receive query
└───┬─────────────┘
    │ query text
    ▼
┌─────────────────┐
│  Ollama (Host)  │ Embed query
│  172.26.0.1     │
└───┬─────────────┘
    │ query embedding
    ▼
┌─────────────────┐
│  ChromaDB       │ Similarity search
│  chromadb:8000  │ Return top 5 chunks
└───┬─────────────┘
    │ relevant chunks
    ▼
┌─────────────────┐
│  docai / API    │ Assemble context
└───┬─────────────┘
    │ prompt + context
    ▼
┌─────────────────┐
│  Ollama (Host)  │ Generate answer
│  llama3.1:8b    │
└───┬─────────────┘
    │ answer text
    ▼
┌──────┐
│ User │ receives response
└──────┘
```

---

### Understanding "Tenants" in ChromaDB

#### What is a Tenant?
A **tenant** is a namespace/boundary for organizing collections in ChromaDB.

**Default tenant**: `default_tenant`
- All collections created without specifying tenant go here
- Used for single-user/single-project scenarios
- DocAI uses only the default tenant

**Multi-tenancy**: In production systems, you might have:
```
Tenant: customer_a
  └── Collection: documents
  └── Collection: embeddings

Tenant: customer_b
  └── Collection: documents
  └── Collection: embeddings
```

This prevents data leakage between customers.

#### DocAI Tenant Structure
```
ChromaDB Server (chromadb:8000)
  │
  └── default_tenant (only tenant)
        │
        └── docai_documents (collection)
              │
              ├── Chunk 1: embedding + metadata
              ├── Chunk 2: embedding + metadata
              └── Chunk N: embedding + metadata
```

**Collection**: `docai_documents` (configurable via env var)
**Tenant**: `default_tenant` (implicit, not configurable)

#### The Tenant Error (Previously)
```
ValueError: Could not connect to tenant default_tenant. Are you sure it exists?
Exception: {"error":"Unimplemented","message":"The v1 API is deprecated. Please use /v2 apis"}
```

**What happened**:
- Old ChromaDB client (0.4.22) used v1 API for tenant validation
- New ChromaDB server (latest) only supports v2 API
- v1 endpoint returned 410 Gone error
- Client couldn't validate tenant existence

**Solution**: Upgrade client to 0.5.23 to use v2 API

---

### Network Address Reference

#### From Inside Containers

| Service | Address | Port | Protocol |
|---------|---------|------|----------|
| Ollama | `172.26.0.1` | 11434 | HTTP |
| ChromaDB | `chromadb` | 8000 | HTTP |
| API | `docai-api` | 8080 | HTTP |

#### From Host Machine

| Service | Address | Port | Protocol |
|---------|---------|------|----------|
| Ollama | `localhost` | 11434 | HTTP |
| ChromaDB | `localhost` | 8000 | HTTP |
| API | `localhost` | 8080 | HTTP |

#### From Internet (if firewall allows)

| Service | Address | Port | Exposed? |
|---------|---------|------|----------|
| Ollama | N/A | 11434 | ❌ No (host service) |
| ChromaDB | `<host-ip>` | 8000 | ✅ Yes |
| API | `<host-ip>` | 8080 | ✅ Yes |

---

### Component Lifecycle

#### Startup Order
```
1. docker compose up -d
   ↓
2. Network created: docai-network
   ↓
3. Volumes created: chroma_data
   ↓
4. chromadb starts
   ↓
5. chromadb health check passes (30s max)
   ↓
6. docai-api starts (depends_on: chromadb healthy)
   ↓
7. System ready
```

**CLI**: Starts only when explicitly invoked with `--profile cli`

#### Shutdown
```
docker compose down
   ↓
1. Stop docai-api (graceful shutdown)
   ↓
2. Stop chromadb (graceful shutdown)
   ↓
3. Remove containers
   ↓
4. Network remains (unless -v flag)
   ↓
5. Volumes remain (data persists)
```

**Persistent data**: Survives container removal
**Ephemeral data**: Container filesystems (logs, temp files)

---

### Why This Architecture?

#### Separation of Concerns
- **Ollama on host**: Compute-heavy, GPU utilization, already configured
- **ChromaDB in container**: Stateful service, needs isolation
- **API in container**: Stateless, horizontally scalable
- **CLI in container**: Consistent user environment

#### Benefits
✅ **Portability**: Containers work on any Docker host
✅ **Scalability**: Can run multiple API instances
✅ **Isolation**: Services don't interfere
✅ **Versioning**: Pin exact ChromaDB version
✅ **Development**: Easy to rebuild/test

#### Trade-offs
⚠️ **Network overhead**: Container-to-host adds ~1-2ms latency
⚠️ **Complexity**: Multiple moving parts
⚠️ **Debugging**: Need to inspect multiple containers

---

### Current Configuration Summary

```yaml
Network: docai-network (bridge, 172.26.0.0/16)
Gateway: 172.26.0.1

Services:
  chromadb:
    - Image: chromadb/chroma:0.5.23
    - Port: 8000 (published)
    - Volume: chroma_data:/data
    - Health: Monitored
    - Network: docai-network

  docai-api:
    - Image: llm-dir-docai-api (custom)
    - Port: 8080 (published)
    - Volumes: documents, sessions, vector_db
    - Depends: chromadb (healthy)
    - Ollama: 172.26.0.1:11434
    - Network: docai-network

  docai (CLI):
    - Image: llm-dir-docai (custom)
    - Profile: cli (manual start)
    - Ephemeral: --rm flag
    - Volumes: Same as API
    - Ollama: 172.26.0.1:11434
    - Network: docai-network

External:
  Ollama: localhost:11434 (host process)
```
