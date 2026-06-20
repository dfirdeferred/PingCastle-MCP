# Building the Windows executable

On a Windows host with Python 3.11+ and the project installed (`pip install -e ".[dev]"`):

```
pyinstaller packaging/pingcastle-mcp.spec
```

Output: `dist/pingcastle-mcp.exe` (one file). Smoke test:

```
dist\pingcastle-mcp.exe configure
```

The `keyring` Windows Credential Manager backend is bundled via `hiddenimports`.
Attach `dist/pingcastle-mcp.exe` to the GitHub Release.

## Implementation notes (do not "simplify" these)

Two non-obvious choices in `pingcastle-mcp.spec` are deliberate. Reverting them breaks the build:

1. **Entry point is `packaging/_entry.py`, not `src/pingcastle_mcp/__main__.py`.**
   PyInstaller runs the Analysis script as a top-level module, so `__main__.py`'s
   `from . import cli, server` fails with "attempted relative import with no known
   parent package". `_entry.py` is a thin wrapper that imports `main` from the
   installed package, sidestepping the relative-import problem.

2. **`mcp` submodules are collected targeted (`mcp.server`/`mcp.shared`/`mcp.client`),
   not via `collect_submodules("mcp")`.** The full collection pulls in `mcp.cli`,
   which imports `typer`; unless `mcp[cli]` is installed the build aborts. The server
   binary does not need `mcp.cli`, so it is excluded. Keep the targeted list.
