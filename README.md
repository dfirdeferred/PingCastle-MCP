<div align="center">

# PingCastle MCP Server

### Talk to PingCastle Enterprise from Claude (or any LLM)

An [MCP](https://modelcontextprotocol.io) server that plugs a **PingCastle Enterprise** instance straight into Claude — browse domains and reports, surface critical Active Directory findings, compare scans over time, and kick off on-demand health checks, all in natural language.

[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](#-requirements)
[![PyPI](https://img.shields.io/pypi/v/pingcastle-mcp?style=flat-square&logo=pypi&logoColor=red)](https://pypi.org/project/pingcastle-mcp/)
[![MCP Server](https://img.shields.io/badge/MCP-server-9cf?style=flat-square)](https://modelcontextprotocol.io)
[![Tools](https://img.shields.io/badge/tools-7-brightgreen?style=flat-square)](#-tools)
[![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20macOS%20%7C%20Linux%20%7C%20WSL-blueviolet?style=flat-square)](#-install)
[![PingCastle](https://img.shields.io/badge/PingCastle-Enterprise-red?style=flat-square)](https://netwrix.com/en/products/pingcastle/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](#-contributing)

**7 MCP tools · reports & critical findings · scan diffing & score trends · on-demand scans · OS-keyring credentials · standalone Windows `.exe`**

[Install](#-install) · [Configure](#-configure) · [Tools](#-tools) · [Clients & local LLMs](docs/CLIENTS.md) · [How it works](#-how-it-works) 

</div>

---

## Why

PingCastle Enterprise already scores your Active Directory and Entra ID security posture. `pingcastle-mcp` makes that data conversational:

> *"What changed in cloud.lab since last month?"*
> 
> *"Show me the critical findings on the latest report."*
> 
> *"Compare report 1002 against 1 and tell me what got fixed."*
> 
> *"Run a fresh health check on cloud.lab."*

Your LLM calls the right tool, pulls live data from the Enterprise REST API, and answers — no portal-clicking required.

## Tools

| Tool | What it does |
|------|--------------|
| `list_domains` | Enumerate scanned domains / forests (and Entra tenants) with their latest score and report count |
| `list_reports` | List a domain's reports — id, date, global + category scores, maturity level |
| `get_report_summary` | Scores by category, maturity level, finding counts **by category**, and the top findings by points (for a report id, or a domain's latest) |
| `get_findings` | Matched risk rules for a report — filter by `category` and `min_points` (severity ≈ points) |
| `compare_reports` | Diff two reports: **new / resolved / unchanged** findings (by `riskId`) plus per-category & global score deltas |
| `score_trend` | Global score over time for a domain, sorted chronologically |
| `run_scan` | Trigger an on-demand `PingCastle.exe` health check and upload it to Enterprise *(Windows + AD reachability)* |

> The read tools work on **any OS** with just an Enterprise URL + API key. `run_scan` additionally needs `PingCastle.exe`, so it lights up on a Windows host; elsewhere it degrades gracefully with a clear message.

## Install

**Standalone Windows `pingcastle-mcp.exe`** (no Python required) — download from [Releases](https://github.com/dfirdeferred/PingCastle-MCP/tree/main/Windows%20Executable), verify, and register:
```powershell
# verify the download against the published checksum
Get-FileHash .\pingcastle-mcp.exe -Algorithm SHA256
# compare with pingcastle-mcp.exe.sha256
claude mcp add pingcastle -- C:\path\to\pingcastle-mcp.exe
```

**From PyPI** (recommended once published):
```bash
claude mcp add pingcastle -- uvx pingcastle-mcp
```
uvx (from uv (https://docs.astral.sh/uv/)) downloads and runs it in an isolated environment — nothing to manage. Or with pip:
```pip install pingcastle-mcp```
```claude mcp add pingcastle -- pingcastle-mcp```

**From GitHub, no clone:**
```bash
claude mcp add pingcastle -- uvx --from git+https://github.com/dfirdeferred/PingCastle-MCP pingcastle-mcp
```

**Manual clone:**
```bash
git clone https://github.com/dfirdeferred/PingCastle-MCP && cd PingCastle-MCP
pip install .
claude mcp add pingcastle -- pingcastle-mcp
```

**Project-scoped `.mcp.json`:**
```json
{ "mcpServers": { "pingcastle": { "command": "uvx", "args": ["pingcastle-mcp"] } } }
```

> Using a different assistant (Cursor, Claude Desktop, VS Code, Cline, **Ollama / LM Studio / local models**, …)? See **[docs/CLIENTS.md](docs/CLIENTS.md)** for per-client setup.

## Configure

Run the one-time setup — it prompts for your Enterprise URL and API key, validates them against the server, stores the **URL in a config file** and the **API key in your OS keyring** (Windows Credential Manager / macOS Keychain / Linux Secret Service):

```bash
pingcastle-mcp configure
```

Re-running `configure` rotates the key by overwriting it. Prefer environment variables (CI / headless)? Set them instead:

| Env var | Purpose |
|---------|---------|
| `PINGCASTLE_ENTERPRISE_URL` | Enterprise base URL |
| `PINGCASTLE_API_KEY` | API key (exchanged for a short-lived JWT at runtime) |
| `PINGCASTLE_EXE_PATH` | Path to `PingCastle.exe` — enables `run_scan` |
| `PINGCASTLE_INSECURE_TLS` | `1` to skip TLS verification (self-signed lab certs) |
| `PINGCASTLE_LOGIN_LOCATION` | Override the `location` sent at login (default `pingcastle-mcp`) |

Or, where the OS keyring isn't available (headless / WSL / containers / CI), pass them as env vars instead — e.g. inline with the Claude Code command:
```bash
claude mcp add pingcastle \
  -e PINGCASTLE_ENTERPRISE_URL=https://your-pingcastle \
  -e PINGCASTLE_API_KEY=<YOUR-API-KEY> \
  -- uvx pingcastle-mcp
```

  Other clients (Claude Desktop, Cursor, VS Code, local LLMs, …)

Same package, just point the client's MCP config at it:
```json
{ "mcpServers": { "pingcastle": { "command": "uvx", "args": ["pingcastle-mcp"], "env": { "PINGCASTLE_ENTERPRISE_URL": "https://your-pingcastle", "PINGCASTLE_API_KEY": "PC2…" } } } }
```
Full per-client setup (incl. Ollama/LM Studio/local models) is in [docs/CLIENTS.md](https://github.com/dfirdeferred/PingCastle-MCP/tree/main/docs).

Resolution order: **environment variables first, then stored config + keyring.** The API key and JWT are never logged or written to disk in plaintext.

## How it works

```
LLM client ──stdio──▶ FastMCP tool handlers (thin)
                          ├──▶ EnterpriseClient ──HTTPS──▶ PingCastle Enterprise REST API
                          │      (API key → POST /api/Agent/Login → JWT; auto-refresh)
                          └──▶ Scanner ──▶ PingCastle.exe --healthcheck --api-endpoint … (upload to Enterprise)
```

- **EnterpriseClient** owns auth and all reads. The API key is exchanged for a `Bearer` JWT at `/api/Agent/Login`; the token is cached, proactively refreshed before expiry, and re-issued on a `401`.
- **Scanner** wraps `PingCastle.exe`, with a timeout that reaps the child process and graceful degradation when the exe isn't available.
- **Pure parsing/diff** (summaries, filtering, report comparison, trends) is isolated and unit-tested against real captured API responses.

## Requirements

- **Python 3.11+** (for the pip/uvx install paths; the `.exe` bundles its own runtime)
- A reachable **PingCastle Enterprise** instance + an **API key** (Agent authorization)
- For `run_scan`: a Windows host with `PingCastle.exe` and AD/network reachability



## Contributing

Issues and PRs welcome. The codebase is small, typed, and test-first — please add or update tests with any change.

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">
<sub>Not affiliated with or endorsed by Netwrix / PingCastle. "PingCastle" is a trademark of its respective owner.</sub>
</div>
