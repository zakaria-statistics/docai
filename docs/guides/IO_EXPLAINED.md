# I/O Deep Dive: How DocAI Communicates

## What is I/O?

**I/O = Input/Output** - How programs communicate with the outside world.

### The 3 Standard Streams

Every Unix/Linux process has these streams:

| Stream | File Descriptor | Purpose | Example |
|--------|----------------|---------|---------|
| **stdin** | 0 | Input from keyboard/pipe | `input()`, `read()` |
| **stdout** | 1 | Normal output | `print()`, `write()` |
| **stderr** | 2 | Error messages | `sys.stderr.write()` |

### Low-Level View

```c
// In C/Unix (what Python uses underneath):
int stdin  = 0;   // Read from this
int stdout = 1;   // Write to this
int stderr = 2;   // Errors go here

read(stdin, buffer, size);    // Read input
write(stdout, data, size);    // Write output
write(stderr, error, size);   // Write error
```

### Python Abstraction

```python
import sys

# These are file-like objects wrapping fd 0, 1, 2
sys.stdin   # File descriptor 0
sys.stdout  # File descriptor 1
sys.stderr  # File descriptor 2

# High-level functions use these:
input("Name? ")    # Reads from sys.stdin
print("Hello")     # Writes to sys.stdout
```

---

## DocAI I/O Libraries

### 1. **prompt_toolkit** - Enhanced Input

**File**: `src/cli/prompts.py`

```python
from prompt_toolkit import prompt

def get_user_input(message: str = "You: ") -> str:
    user_input = prompt(message)  # Reads from stdin
    return user_input.strip()
```

**What it does**:
- Reads from `stdin` (file descriptor 0)
- Adds features: history, auto-complete, arrow keys
- Still fundamentally reading from the same stdin stream

**Underneath**:
```
User types ──► Terminal ──► stdin (fd 0) ──► prompt_toolkit ──► Your program
```

### 2. **rich** - Fancy Output

**File**: `src/cli/formatters.py`

```python
from rich.console import Console

console = Console()  # Wraps stdout/stderr

def print_success(message: str):
    console.print(f"[green]✓[/green] {message}")
```

**What it does**:
- Writes to `stdout` (file descriptor 1)
- Adds colors, formatting, tables, progress bars
- Still fundamentally writing to the same stdout stream

**Underneath**:
```
Your program ──► rich.console ──► stdout (fd 1) ──► Terminal ──► Display
```

### 3. **click** - Command Parsing

**File**: `src/cli/commands.py`

```python
import click

@click.command()
def chat():
    # click handles parsing command-line args
    # Uses stdout/stderr for output
    pass
```

**What it does**:
- Parses command-line arguments (from `sys.argv`)
- Uses stdout/stderr for help text and errors
- Doesn't create new I/O streams, just manages existing ones

---

## Before Docker: Local Execution

### The Full Picture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Computer                             │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │           Terminal (bash/zsh)                      │    │
│  │                                                     │    │
│  │  You type: python3 -m src.main chat               │    │
│  │                                                     │    │
│  │  ┌──────────────────────────────────────────────┐ │    │
│  │  │  Python Process                              │ │    │
│  │  │                                               │ │    │
│  │  │  ┌─────────────────────────────────┐         │ │    │
│  │  │  │  click parses: "chat" command   │         │ │    │
│  │  │  └─────────────────────────────────┘         │ │    │
│  │  │                                               │ │    │
│  │  │  ┌─────────────────────────────────┐         │ │    │
│  │  │  │  Your Input Loop:               │         │ │    │
│  │  │  │                                 │         │ │    │
│  │  │  │  1. prompt_toolkit.prompt()     │         │ │    │
│  │  │  │     └─ read(stdin) ◄──────────────┼────── Keyboard
│  │  │  │                                 │         │ │    │
│  │  │  │  2. Process message             │         │ │    │
│  │  │  │                                 │         │ │    │
│  │  │  │  3. rich.console.print()        │         │ │    │
│  │  │  │     └─ write(stdout) ──────────────┼────► Screen
│  │  │  │                                 │         │ │    │
│  │  │  └─────────────────────────────────┘         │ │    │
│  │  │                                               │ │    │
│  │  └───────────────────────────────────────────────┘ │    │
│  │                                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Code Flow (Local)

```python
# src/main.py
import click
from src.cli.commands import cli

def main():
    cli()  # click routes to the right command

# src/cli/commands.py
@click.command()
def chat():
    from src.cli.prompts import get_user_input
    from src.cli.formatters import console

    while True:
        # INPUT: Read from stdin
        message = get_user_input("You: ")
        # ↑ Uses prompt_toolkit which calls read(stdin)

        # PROCESSING: Get AI response
        response = engine.chat(message)

        # OUTPUT: Write to stdout
        console.print(response)
        # ↑ Uses rich which calls write(stdout)
```

### System Calls (What Actually Happens)

```
1. User presses keys
   └─► Terminal buffer receives: "h" "e" "l" "l" "o" "\n"

2. prompt_toolkit calls:
   └─► read(stdin=0, buffer, 1024)  # System call
       └─► Kernel copies: "hello\n" to buffer

3. Python code processes "hello"

4. rich.console.print() calls:
   └─► write(stdout=1, "AI: Hi there", 11)  # System call
       └─► Kernel sends bytes to terminal

5. Terminal displays: "AI: Hi there"
```

---

## After Docker: Container Execution

### The Docker Magic

When you run `docker-compose run --rm docai chat`:

```
┌──────────────────────────────────────────────────────────────────┐
│                      Your Computer (Host)                         │
│                                                                   │
│  ┌─────────────────────────────────────────┐                     │
│  │   Your Terminal (Host)                  │                     │
│  │                                          │                     │
│  │   stdin (fd 0)  ◄─── Keyboard           │                     │
│  │   stdout (fd 1) ───► Screen             │                     │
│  │   stderr (fd 2) ───► Screen             │                     │
│  └──────────┬──────────────────────────────┘                     │
│             │                                                     │
│             │ Docker forwards file descriptors                   │
│             │ (This is the magic part!)                          │
│             │                                                     │
│  ┌──────────▼──────────────────────────────────────────────────┐ │
│  │         Docker Container                                    │ │
│  │                                                             │ │
│  │  ┌───────────────────────────────────────────────────────┐ │ │
│  │  │  Python Process (Inside Container)                    │ │ │
│  │  │                                                        │ │ │
│  │  │  stdin (fd 0)  ◄────────────────────────────────────────┼─┼─ Host stdin
│  │  │  stdout (fd 1) ──────────────────────────────────────────┼─┼─► Host stdout
│  │  │  stderr (fd 2) ──────────────────────────────────────────┼─┼─► Host stderr
│  │  │                                                        │ │ │
│  │  │  Same libraries:                                      │ │ │
│  │  │  - prompt_toolkit reads from stdin                    │ │ │
│  │  │  - rich writes to stdout                              │ │ │
│  │  │  - click parses commands                              │ │ │
│  │  │                                                        │ │ │
│  │  └────────────────────────────────────────────────────────┘ │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### Docker Configuration Explained

**File**: `docker-compose.yml`

```yaml
docai:
  stdin_open: true   # Keep stdin open (don't close fd 0)
  tty: true          # Allocate a pseudo-TTY (terminal emulator)
```

**What these do**:

#### `stdin_open: true`
```bash
# Without this:
docker run myimage
# stdin is closed immediately, read() fails

# With this:
docker run -i myimage  # "-i" = interactive
# stdin stays open, can read from it
```

#### `tty: true`
```bash
# Without this:
docker run -i myimage
# No terminal features: no colors, no line editing

# With this:
docker run -it myimage  # "-t" = tty
# Full terminal emulation: colors, arrows, ctrl+c, etc.
```

### How Docker Forwards I/O

**Docker uses Unix pipes and pseudo-terminals**:

```
Host Terminal (pts/0)
        ├─ stdin  ─────┐
        ├─ stdout ◄────┤
        └─ stderr ◄────┤
                       │
        Docker Engine  │
        (Forwards I/O) │
                       │
Container Process      │
        ├─ stdin  ◄────┘
        ├─ stdout ─────►
        └─ stderr ─────►
```

**Technical Details**:

1. **Docker creates pipes**:
   ```c
   pipe(stdin_pipe);   // [read_fd, write_fd]
   pipe(stdout_pipe);
   pipe(stderr_pipe);
   ```

2. **Connects them**:
   ```
   Host stdin → write_fd → Container stdin (read_fd)
   Container stdout (write_fd) → read_fd → Host stdout
   ```

3. **Container doesn't know**:
   - Process inside container sees normal stdin/stdout/stderr
   - Doesn't know it's in a container
   - Works exactly like local execution

---

## Comparison: Local vs Docker

### Local Execution

```bash
$ python3 -m src.main chat
```

```
Keyboard ──► Terminal ──► stdin ──► Python ──► stdout ──► Terminal ──► Screen
         (direct)      (fd 0)              (fd 1)      (direct)
```

### Docker Execution

```bash
$ docker-compose run --rm docai chat
```

```
Keyboard ──► Host Terminal ──► Docker Pipes ──► Container stdin ──► Python
                                     ▲                (fd 0)
                                     │
                                  Forwarding
                                     │
                                     ▼
Screen ◄──── Host Terminal ◄──── Docker Pipes ◄──── Container stdout ◄──── Python
                                                          (fd 1)
```

**Key Point**: The Python code is **identical**. Docker just transparently forwards the I/O streams.

---

## What About the API Mode?

### CLI Mode (I/O Streams)

```
Terminal ──(stdin/stdout)──► DocAI Process
```

### API Mode (Network Sockets)

```
Browser ──(HTTP/TCP socket)──► DocAI API Server
```

### Different I/O Mechanisms

#### CLI Uses: File Descriptors (stdin/stdout)
```python
# src/cli/prompts.py
message = prompt("You: ")  # Reads from stdin (fd 0)
```

#### API Uses: Network Sockets
```python
# src/api.py
@app.post("/chat")
async def chat(request: ChatRequest):  # Reads from TCP socket
    # FastAPI reads from socket, parses HTTP, extracts JSON
    return {"response": "..."}  # Writes JSON to socket
```

### Full Comparison

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI MODE                                  │
│                                                              │
│  Terminal ─────► stdin (fd 0) ─────► prompt_toolkit         │
│                                                              │
│  Terminal ◄───── stdout (fd 1) ◄──── rich.console           │
│                                                              │
│  I/O Type: File descriptors (Unix streams)                  │
│  Protocol: None (direct I/O)                                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    API MODE                                  │
│                                                              │
│  Browser ──► TCP Socket (port 8080) ──► FastAPI ──► Pydantic│
│           HTTP Request                                       │
│           JSON payload                                       │
│                                                              │
│  Browser ◄── TCP Socket (port 8080) ◄── FastAPI ◄── Python  │
│           HTTP Response                                      │
│           JSON payload                                       │
│                                                              │
│  I/O Type: Network socket                                   │
│  Protocol: HTTP/TCP                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Hands-On: See I/O in Action

### 1. Trace System Calls (Local)

```bash
# Run with strace to see actual system calls
strace -e read,write python3 -m src.main chat 2>&1 | grep -E "read\(0|write\(1"

# You'll see:
# read(0, "hello\n", ...)     ← Reading from stdin (fd 0)
# write(1, "AI: Hello!\n", ...) ← Writing to stdout (fd 1)
```

### 2. See File Descriptors

```bash
# Start DocAI in background
python3 -m src.main chat &
PID=$!

# Check file descriptors
ls -l /proc/$PID/fd/

# Output:
# 0 -> /dev/pts/0  (stdin - your terminal)
# 1 -> /dev/pts/0  (stdout - your terminal)
# 2 -> /dev/pts/0  (stderr - your terminal)
```

### 3. Docker I/O Forwarding

```bash
# Run in Docker
docker-compose run --rm docai chat

# In another terminal, find container
docker ps

# Check file descriptors in container
docker exec -it <container-id> ls -l /proc/1/fd/

# Output:
# 0 -> pipe:[12345]  (stdin - forwarded from host)
# 1 -> pipe:[12346]  (stdout - forwarded to host)
# 2 -> pipe:[12347]  (stderr - forwarded to host)
```

### 4. Compare API Mode

```bash
# Start API
docker-compose up -d docai-api

# In container, check what ports are listening
docker exec docai-api netstat -tlnp

# Output:
# tcp  0  0.0.0.0:8080  LISTEN  1/python
#                  ↑
#            Network socket, not stdin/stdout!
```

---

## Summary

### I/O Fundamentals

| Concept | What It Is |
|---------|-----------|
| **stdin** | File descriptor 0, reads keyboard input |
| **stdout** | File descriptor 1, writes normal output |
| **stderr** | File descriptor 2, writes error messages |
| **File Descriptor** | Integer identifying an open file/stream |
| **System Call** | Kernel function (read, write, open, etc.) |

### DocAI I/O Libraries

| Library | Purpose | What It Wraps |
|---------|---------|---------------|
| **prompt_toolkit** | Enhanced input | stdin (fd 0) |
| **rich** | Fancy output | stdout/stderr (fd 1/2) |
| **click** | Command parsing | sys.argv, stdout/stderr |

### Local vs Docker

| Aspect | Local | Docker |
|--------|-------|--------|
| **stdin source** | Terminal directly | Terminal → Docker → Container |
| **stdout destination** | Terminal directly | Container → Docker → Terminal |
| **Mechanism** | Direct fd inheritance | Pipe/socket forwarding |
| **Code changes** | None | None (transparent!) |
| **Configuration** | N/A | `stdin_open: true`, `tty: true` |

### CLI vs API

| Mode | I/O Type | Protocol | Concurrency |
|------|----------|----------|-------------|
| **CLI** | File descriptors (0,1,2) | None | Single user |
| **API** | Network sockets | HTTP/TCP | Multi-user |

---

## Key Takeaway

**The libraries (prompt_toolkit, rich) don't change between local and Docker!**

- They always use stdin/stdout/stderr
- Docker just makes those streams appear local
- It's transparent to the Python code
- Same code runs in both environments

**API mode is fundamentally different**:
- Uses network sockets instead of stdin/stdout
- Requires HTTP protocol
- Needs different libraries (FastAPI, uvicorn)
- But shares the same backend logic!
