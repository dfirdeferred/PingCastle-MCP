from __future__ import annotations
import asyncio
from dataclasses import dataclass
from pathlib import Path

from .config import Config
from .errors import ScannerError


@dataclass
class ScanResult:
    success: bool
    returncode: int
    report_path: str | None
    message: str


class Scanner:
    def __init__(self, config: Config):
        self._cfg = config

    def available(self) -> bool:
        p = self._cfg.exe_path
        return bool(p) and Path(p).exists()

    async def run(self, server: str, timeout: int = 1800) -> ScanResult:
        if not self.available():
            raise ScannerError(
                "Scanning is not available on this host. Set PINGCASTLE_EXE_PATH "
                "to a valid PingCastle.exe (Windows + AD reachability required)."
            )
        # NOTE: PingCastle.exe requires the API key as a CLI arg; it is therefore
        # visible in host process listings. This is dictated by the tool's CLI,
        # not a free design choice.
        args = [
            self._cfg.exe_path, "--healthcheck",
            "--server", server,
            "--api-endpoint", self._cfg.enterprise_url,
            "--api-key", self._cfg.api_key,
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            _, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError as e:
            proc.kill()
            await proc.wait()
            raise ScannerError(f"Scan of {server} timed out after {timeout}s") from e
        except OSError as e:
            raise ScannerError(f"Failed to launch PingCastle.exe: {e}") from e

        if proc.returncode != 0:
            raise ScannerError(
                f"Scan failed (exit {proc.returncode}): {err.decode(errors='replace')[:500]}"
            )
        return ScanResult(
            success=True,
            returncode=proc.returncode,
            report_path=f"ad_hc_{server}.xml",
            message=f"Scan of {server} complete and uploaded.",
        )
