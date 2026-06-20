# PyInstaller spec — build on Windows: pyinstaller packaging/pingcastle-mcp.spec
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = (
    collect_submodules("keyring.backends")
    + collect_submodules("mcp.server")
    + collect_submodules("mcp.shared")
    + collect_submodules("mcp.client")
    + collect_submodules("pingcastle_mcp")
)

a = Analysis(
    ["_entry.py"],
    pathex=["../src"],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="pingcastle-mcp",
    console=True,
    onefile=True,
)
