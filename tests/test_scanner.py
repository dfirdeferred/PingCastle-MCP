import asyncio
import pytest
from pingcastle_mcp.config import Config
from pingcastle_mcp.scanner import Scanner
from pingcastle_mcp.errors import ScannerError


def cfg(exe_path):
    return Config(enterprise_url="https://pc.test", api_key="k",
                  exe_path=exe_path, insecure_tls=True, login_location="t")


def test_unavailable_when_no_exe():
    s = Scanner(cfg(exe_path=None))
    assert s.available() is False


def test_unavailable_when_exe_missing(tmp_path):
    s = Scanner(cfg(exe_path=str(tmp_path / "nope.exe")))
    assert s.available() is False


async def test_run_raises_when_unavailable():
    s = Scanner(cfg(exe_path=None))
    with pytest.raises(ScannerError):
        await s.run(server="cloud.lab")


async def test_run_invokes_exe_and_reports_success(tmp_path, monkeypatch):
    exe = tmp_path / "PingCastle.exe"
    exe.write_text("")
    captured = {}

    class FakeProc:
        returncode = 0

        async def communicate(self):
            return (b"done", b"")

    async def fake_exec(*args, **kwargs):
        captured["args"] = args
        return FakeProc()

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake_exec)
    s = Scanner(cfg(exe_path=str(exe)))
    result = await s.run(server="cloud.lab")
    assert result.success is True
    assert "--healthcheck" in captured["args"]
    assert "cloud.lab" in captured["args"]
    assert "--api-endpoint" in captured["args"]


async def test_run_nonzero_exit_raises(tmp_path, monkeypatch):
    exe = tmp_path / "PingCastle.exe"
    exe.write_text("")

    class FakeProc:
        returncode = 2
        async def communicate(self):
            return (b"", b"scan failed: bad creds")

    async def fake_exec(*args, **kwargs):
        return FakeProc()

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake_exec)
    s = Scanner(cfg(exe_path=str(exe)))
    with pytest.raises(ScannerError):
        await s.run(server="cloud.lab")


async def test_run_launch_oserror_raises(tmp_path, monkeypatch):
    exe = tmp_path / "PingCastle.exe"
    exe.write_text("")

    async def fake_exec(*args, **kwargs):
        raise OSError("cannot exec")

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake_exec)
    s = Scanner(cfg(exe_path=str(exe)))
    with pytest.raises(ScannerError):
        await s.run(server="cloud.lab")


async def test_run_timeout_kills_process_and_raises(tmp_path, monkeypatch):
    exe = tmp_path / "PingCastle.exe"
    exe.write_text("")
    killed = {}

    class FakeProc:
        returncode = None
        async def communicate(self):
            return (b"", b"")
        def kill(self):
            killed["killed"] = True
        async def wait(self):
            return 0

    async def fake_exec(*args, **kwargs):
        return FakeProc()

    async def fake_wait_for(coro, timeout):
        coro.close()  # avoid 'coroutine never awaited' warning
        raise asyncio.TimeoutError

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake_exec)
    monkeypatch.setattr("asyncio.wait_for", fake_wait_for)
    s = Scanner(cfg(exe_path=str(exe)))
    with pytest.raises(ScannerError):
        await s.run(server="cloud.lab", timeout=1)
    assert killed.get("killed") is True
