# Connecting `pingcastle-mcp` to LLM clients

`pingcastle-mcp` is a standard **stdio MCP server**. Any MCP-capable client can use it — you just tell the client how to *launch* it and (optionally) pass credentials via environment variables.

> **Key idea for local models:** an LLM (Claude, GPT, Llama, Qwen, …) does not speak MCP by itself. MCP is spoken by the **host application** around the model. So "use a local model" really means "use an MCP-capable host that is pointed at a local model (Ollama / LM Studio / llama.cpp / vLLM)." The sections below cover both hosted and local setups.

---

## 1. The launch command (pick one)

Every client config boils down to a **command + args** that start the server. Use whichever install you chose:

| Install | `command` | `args` |
|---------|-----------|--------|
| PyPI / uv | `uvx` | `["pingcastle-mcp"]` |
| pip (installed on PATH) | `pingcastle-mcp` | `[]` |
| From GitHub (no clone) | `uvx` | `["--from", "git+https://github.com/dfirdeferred/PingCastle-MCP", "pingcastle-mcp"]` |
| Windows `.exe` | `C:\\path\\to\\pingcastle-mcp.exe` | `[]` |
| Python module | `python` | `["-m", "pingcastle_mcp"]` |

## 2. Credentials

Two options — pick one:

**A. Configure once (recommended for desktop use):**
```bash
pingcastle-mcp configure         # or:  pingcastle-mcp.exe configure
```
Stores the URL in a config file and the API key in your OS keyring. Nothing else needed in the client config.

**B. Pass via the client's `env` block** (good for headless/servers/containers):
```json
"env": {
  "PINGCASTLE_ENTERPRISE_URL": "https://your-pingcastle",
  "PINGCASTLE_API_KEY": "PC2…",
  "PINGCASTLE_INSECURE_TLS": "1"
}
```
> ⚠️ Putting the key in a config file stores it in plaintext. Prefer option A (keyring) on shared machines. `PINGCASTLE_INSECURE_TLS=1` is only for self-signed lab certs.

The canonical config object reused everywhere below:

```json
{
  "mcpServers": {
    "pingcastle": {
      "command": "uvx",
      "args": ["pingcastle-mcp"],
      "env": {
        "PINGCASTLE_ENTERPRISE_URL": "https://your-pingcastle",
        "PINGCASTLE_API_KEY": "PC2…"
      }
    }
  }
}
```

---

## 3. Hosted clients

### Claude Code (CLI)
```bash
claude mcp add pingcastle -- uvx pingcastle-mcp
# or with env inline:
claude mcp add pingcastle \
  -e PINGCASTLE_ENTERPRISE_URL=https://your-pingcastle \
  -e PINGCASTLE_API_KEY=PC2… \
  -- uvx pingcastle-mcp
```
List/verify: `claude mcp list`.

### Claude Desktop
Edit the config file, then restart Claude Desktop:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Paste the canonical `mcpServers` object above. On Windows, use the `.exe` form:
```json
{ "mcpServers": { "pingcastle": { "command": "C:\\Tools\\pingcastle-mcp.exe", "args": [] } } }
```

### Cursor
Add to `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (per project) — same `mcpServers` shape. Enable it in **Settings → MCP**.

### VS Code (GitHub Copilot agent mode)
Create `.vscode/mcp.json` in your workspace:
```json
{
  "servers": {
    "pingcastle": { "command": "uvx", "args": ["pingcastle-mcp"], "env": { "PINGCASTLE_ENTERPRISE_URL": "https://your-pingcastle", "PINGCASTLE_API_KEY": "PC2…" } }
  }
}
```
(VS Code uses the key `servers`; most other clients use `mcpServers`.)

### Cline / Roo Code (VS Code extensions)
Open the MCP settings file (`cline_mcp_settings.json`, reachable from the extension's **MCP Servers → Configure**) and add the canonical `mcpServers` object.

### Windsurf
`~/.codeium/windsurf/mcp_config.json` — canonical `mcpServers` object, then refresh MCP in the Cascade panel.

### Zed
In `settings.json`, add under `context_servers`:
```json
"context_servers": {
  "pingcastle": { "command": { "path": "uvx", "args": ["pingcastle-mcp"], "env": { "PINGCASTLE_ENTERPRISE_URL": "https://your-pingcastle", "PINGCASTLE_API_KEY": "PC2…" } } }
}
```

---

## 4. Local / self-hosted models

These hosts run (or connect to) a **local model** and act as the MCP host. Point them at Ollama, LM Studio, llama.cpp, vLLM, etc.

> Tool use works best with models trained for function calling — e.g. **Llama 3.1/3.3**, **Qwen 2.5/3 (Instruct)**, **Mistral/Mixtral**, **Command-R**. Tiny models often won't reliably call tools.

### LM Studio (runs the model *and* hosts MCP)
LM Studio includes a local model server and an MCP host. Edit its `mcp.json` (**Program → Edit mcp.json**, or the chat sidebar's MCP/Integrations panel) and add the canonical `mcpServers` object. Pick a tool-calling model in the chat, and pingcastle's tools appear.

### Ollama via `mcphost`
[`mcphost`](https://github.com/mark3labs/mcphost) bridges Ollama models to MCP servers.
```bash
# config.json
{
  "mcpServers": {
    "pingcastle": { "command": "uvx", "args": ["pingcastle-mcp"],
      "env": { "PINGCASTLE_ENTERPRISE_URL": "https://your-pingcastle", "PINGCASTLE_API_KEY": "PC2…" } }
  }
}
```
```bash
ollama pull llama3.1
mcphost -m ollama:llama3.1 --config ./config.json
```

### Open WebUI + `mcpo` (works with any OpenAI-compatible local model)
[`mcpo`](https://github.com/open-webui/mcpo) exposes an MCP server as an OpenAPI tool server that Open WebUI (backed by Ollama/vLLM/etc.) can call:
```bash
uvx mcpo --port 8000 --env PINGCASTLE_ENTERPRISE_URL=https://your-pingcastle --env PINGCASTLE_API_KEY=PC2… \
  -- uvx pingcastle-mcp
```
Then in Open WebUI: **Settings → Tools → Add** `http://localhost:8000` (OpenAPI). Use any local chat model with tool calling enabled.

### LibreChat (local models + MCP)
In `librechat.yaml`:
```yaml
mcpServers:
  pingcastle:
    command: uvx
    args: ["pingcastle-mcp"]
    env:
      PINGCASTLE_ENTERPRISE_URL: "https://your-pingcastle"
      PINGCASTLE_API_KEY: "PC2…"
```
Point LibreChat's endpoint at your Ollama/vLLM server and pick a tool-capable model.

### oterm (terminal Ollama client)
Add the canonical `mcpServers` object to oterm's `config.json` (path shown by `oterm --data-dir`), then chat with a tool-calling Ollama model.

### Desktop MCP clients with local-model support
**5ire**, **Cherry Studio**, **Jan**, and **Witsy** are GUI chat apps that support MCP servers *and* local backends (Ollama / LM Studio). Add a new **stdio** server in their MCP/Tools settings using the command + args from §1, and select a local model with function calling.

---

## 5. Verify & troubleshoot

- **Quick self-test (no client):** with credentials configured, run the server directly — it should start and wait on stdio (Ctrl-C to exit). With *no* credentials it exits immediately with `ConfigError: No Enterprise URL configured…`, which confirms the binary/imports are healthy.
- **Tools don't appear:** confirm the client picked up the config (restart it), and that `command`/`args` resolve on its PATH. For `uvx`, ensure [uv](https://docs.astral.sh/uv/) is installed; for the `.exe`, use an absolute path.
- **Model never calls the tools:** use a model trained for function/tool calling (see note above) and make sure the client's tool-calling/agent mode is enabled.
- **TLS errors against a lab server:** set `PINGCASTLE_INSECURE_TLS=1` (self-signed certs only).
- **401 / auth errors:** the API key is wrong or lacks Agent authorization; re-run `pingcastle-mcp configure` or fix the `PINGCASTLE_API_KEY` env value.
- **`run_scan` says "not available":** set `PINGCASTLE_EXE_PATH` to a real `PingCastle.exe` on a Windows host with AD reachability. Read tools work without it.

> Client config formats evolve quickly. If a path or key here drifts from a client's current docs, the **command + args + env** triple from §1–§2 is what every MCP client ultimately needs — drop it into that client's MCP config in whatever shape it expects.
