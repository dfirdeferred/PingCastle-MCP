from __future__ import annotations
import sys

from . import cli, server


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "configure":
        return cli.configure()
    server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
