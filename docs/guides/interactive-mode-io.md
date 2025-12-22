# Interactive Mode & I/O in Docker

## What is Interactive Mode?

Interactive mode allows you to interact with a containerized process as if it were running locally - typing input and seeing output in real-time.

---

## The Two Flags

### `stdin_open: true` (-i flag)

**Keeps stdin open** even if not attached.

```yaml
stdin_open: true
# Equivalent to: docker run -i
```

**Without it**:
```bash
docker run ubuntu cat
# Immediately exits - stdin closed
```

**With it**:
```bash
docker run -i ubuntu cat
# Waits for input from stdin
hello
hello  # Echoes back
```

### `tty: true` (-t flag)

**Allocates a pseudo-TTY** (terminal).

```yaml
tty: true
# Equivalent to: docker run -t
```

**What is a TTY?**
- Emulates a physical terminal
- Enables:
  - Line editing (backspace, arrows)
  - Color output
  - Terminal control codes
  - Signal handling (Ctrl+C, Ctrl+D)

**Without it**:
```bash
docker run ubuntu bash
# Works but no prompt, no colors, weird behavior
```

**With it**:
```bash
docker run -t ubuntu bash
root@abc123:/#  # Proper prompt with colors
```

---

## Combined: -it (Interactive + TTY)

**File**: `docker-compose.yml`

```yaml
docai:
  stdin_open: true
  tty: true
```

**Equivalent to**:
```bash
docker run -it myimage
```

### Why Both Are Needed

```
stdin_open: true    →  Keeps stdin channel open
     +
tty: true          →  Makes it feel like a real terminal
     ║
     ║
     ▼
Interactive shell/application
```

---

## How It Works: The Plumbing

### File Descriptors

Every process has 3 standard streams:

```
┌─────────────────┐
│  Process        │
│                 │
│  stdin  (fd 0)  │ ← Input
│  stdout (fd 1)  │ → Output
│  stderr (fd 2)  │ → Errors
│                 │
└─────────────────┘
```

### Local Execution

```bash
python3 -m src.main chat
```

```
Terminal (pts/0)
    │
    │ Parent process forks
    │
    ▼
Python Process
    ├─ stdin  (fd 0) ← Terminal stdin
    ├─ stdout (fd 1) → Terminal stdout
    └─ stderr (fd 2) → Terminal stderr

Inheritance: Child process inherits parent's file descriptors
```

### Docker Execution

```bash
docker run -it myimage python -m src.main chat
```

```
Host Terminal
    │
    │ File descriptors don't cross container boundary!
    │ Docker creates pipes/sockets to bridge them
    │
    ▼
Docker Engine
    │
    │ Creates:
    │  - stdin pipe  (host → container)
    │  - stdout pipe (container → host)
    │  - stderr pipe (container → host)
    │  - pseudo-TTY (if -t flag)
    │
    ▼
Container Process
    ├─ stdin  (fd 0) ← Docker pipe ← Host terminal
    ├─ stdout (fd 1) → Docker pipe → Host terminal
    └─ stderr (fd 2) → Docker pipe → Host terminal
```

---

## Docker I/O Mechanisms

### 1. Pipes (Without TTY)

```bash
docker run -i ubuntu cat
```

```
Host stdin ──► pipe ──► Container stdin (fd 0)
Host stdout ◄─ pipe ◄── Container stdout (fd 1)
```

**Characteristics**:
- Simple byte streams
- No terminal features
- Buffered I/O

### 2. Pseudo-TTY (With -t)

```bash
docker run -it ubuntu bash
```

```
Host terminal ──► PTY Master ──► PTY Slave ──► Container (stdin)
                      │
                      └──────────────────────────► Container (stdout)
```

**PTY (Pseudo-Terminal)**:
- Emulates real terminal
- Line discipline (handles backspace, line editing)
- Signal handling (Ctrl+C sends SIGINT)
- Terminal modes (raw, cooked, cbreak)

---

## DocAI Configuration

### docker-compose.yml

```yaml
services:
  docai:
    stdin_open: true  # Keep stdin open
    tty: true         # Allocate pseudo-TTY
    # ... other settings
```

### Why DocAI Needs Both

**stdin_open: true** - Needed for:
```python
# src/cli/prompts.py
from prompt_toolkit import prompt

user_input = prompt("You: ")  # Reads from stdin
```

**tty: true** - Needed for:
```python
# src/cli/formatters.py
from rich.console import Console

console = Console()
console.print("[green]Success![/green]")  # Colors need TTY
```

**Without tty**:
- No colors (ANSI codes ignored)
- No cursor positioning
- Arrow keys send raw escape sequences
- Ctrl+C doesn't work properly

---

## Running Modes

### 1. Detached Mode (-d)

```bash
docker-compose up -d
```

**Behavior**:
- Runs in background
- No stdin/stdout connection
- stdout/stderr go to logs

```
Container runs
    ↓
No terminal attached
    ↓
View with: docker logs
```

### 2. Attached Mode (default)

```bash
docker-compose up
```

**Behavior**:
- Runs in foreground
- stdout/stderr → terminal
- stdin might not work (depends on config)

```
Container runs
    ↓
stdout/stderr → Your terminal
    ↓
Ctrl+C stops container
```

### 3. Interactive Mode (run)

```bash
docker-compose run --rm docai chat
```

**Behavior**:
- Starts new container
- Fully interactive (stdin + tty)
- Removed after exit (--rm)

```
New container starts
    ↓
stdin/stdout/stderr ↔ Your terminal
    ↓
Exit → Container removed
```

---

## Comparison Table

| Command | Detached | Attached | Interactive | TTY | Use Case |
|---------|----------|----------|-------------|-----|----------|
| `docker run ubuntu` | No | Yes | No | No | One-off command |
| `docker run -d ubuntu` | Yes | No | No | No | Background service |
| `docker run -i ubuntu` | No | Yes | Yes | No | Pipe input |
| `docker run -it ubuntu bash` | No | Yes | Yes | Yes | Interactive shell |
| `docker-compose up` | No | Yes | No | No | View logs |
| `docker-compose up -d` | Yes | No | No | No | Start services |
| `docker-compose run --rm app` | No | Yes | Yes | Yes | CLI apps |

---

## Practical Examples

### Example 1: Interactive Chat

```bash
docker-compose run --rm docai chat
```

**What happens**:
1. Docker creates new container
2. Allocates pseudo-TTY (tty: true)
3. Connects your terminal stdin to container
4. Runs `python -m src.main chat`
5. You type → goes to container stdin → prompt_toolkit reads it
6. AI responds → rich writes to stdout → appears in terminal

### Example 2: Non-Interactive Command

```bash
docker-compose run --rm docai list
```

**What happens**:
1. Docker creates container
2. Allocates TTY (for colors)
3. Runs `python -m src.main list`
4. Outputs list → stdout → terminal
5. Exits immediately (no stdin needed)

### Example 3: Piping Data

```bash
echo "What is ML?" | docker run -i docai-image python -m src.main query
```

**What happens**:
1. `-i` keeps stdin open
2. No `-t` (pipe doesn't need TTY)
3. echo output → pipe → container stdin
4. Container processes and outputs
5. Output → stdout → your terminal

---

## Testing I/O Modes

### Test 1: Echo (stdin → stdout)

```bash
# Works (interactive + tty)
docker run -it ubuntu bash
echo "test"
test

# Doesn't work well (no tty)
docker run -i ubuntu bash
echo "test"
test  # Works but no prompt, no colors
```

### Test 2: Colors (needs TTY)

```bash
# Colors work
docker run -it ubuntu bash -c "echo -e '\e[32mGreen\e[0m'"
Green  # (in green)

# Colors don't work (no tty)
docker run ubuntu bash -c "echo -e '\e[32mGreen\e[0m'"
Green  # (no color, shows escape codes)
```

### Test 3: Signal Handling (needs TTY)

```bash
# Ctrl+C works
docker run -it ubuntu bash
# Press Ctrl+C → SIGINT sent → bash exits

# Ctrl+C doesn't work well
docker run ubuntu bash
# Press Ctrl+C → might kill docker, not bash
```

---

## Troubleshooting

### Problem: No input prompt

```yaml
# Missing stdin_open
docai:
  tty: true  # Has TTY but stdin closed

# Fix:
docai:
  stdin_open: true
  tty: true
```

### Problem: No colors

```yaml
# Missing tty
docai:
  stdin_open: true

# Fix:
docai:
  stdin_open: true
  tty: true
```

### Problem: Ctrl+C doesn't work

```yaml
# Need both flags
docai:
  stdin_open: true
  tty: true

# Also check signal handling:
init: true  # Use init system to handle signals
```

### Problem: Input not echoed

```bash
# TTY issue - check if allocated
docker exec -it <container> bash
# Should show: the input device is not a TTY

# Fix: Make sure tty: true in docker-compose.yml
```

---

## API Server vs CLI

### API Server (No Interactive I/O)

```yaml
docai-api:
  # NO stdin_open or tty
  command: ["uvicorn", "src.api:app", "--host", "0.0.0.0"]
```

**Why?**
- HTTP server doesn't need stdin/stdout
- Input comes from network (HTTP requests)
- Output goes to network (HTTP responses)
- Logs go to Docker logs

### CLI (Needs Interactive I/O)

```yaml
docai:
  stdin_open: true
  tty: true
  # Used with: docker-compose run
```

**Why?**
- User types commands → stdin
- App shows prompts/results → stdout
- Interactive chat needs real-time I/O

---

## Advanced: PTY Internals

### How PTY Works

```
User Terminal
    │
    ▼
┌─────────────────┐
│   PTY Master    │ ← Docker controls this
└────────┬────────┘
         │
         │ Kernel PTY driver
         │
┌────────▼────────┐
│   PTY Slave     │ ← Container sees this
└────────┬────────┘
         │
         ▼
Container Process
(thinks it has real terminal)
```

**PTY provides**:
- Line discipline (buffering, editing)
- Terminal attributes (size, baud rate)
- Signal generation (Ctrl+C → SIGINT)
- Job control (background/foreground)

### Check If TTY Allocated

```bash
# Inside container
if [ -t 0 ]; then
    echo "stdin is a TTY"
else
    echo "stdin is NOT a TTY"
fi

# Python equivalent
import sys
if sys.stdin.isatty():
    print("stdin is a TTY")
```

---

## Summary

| Setting | Effect | When Needed |
|---------|--------|-------------|
| `stdin_open: true` | Keeps stdin open | When app reads input |
| `tty: true` | Allocates pseudo-TTY | When app needs terminal features |
| Both | Interactive mode | CLI apps, shells, chat |
| Neither | Detached service | API servers, daemons |

**DocAI Usage**:
- **CLI mode**: Needs both (interactive chat)
- **API mode**: Needs neither (HTTP server)

**Key Takeaway**: Interactive mode (`-it`) bridges the container boundary, making containerized apps feel local.
