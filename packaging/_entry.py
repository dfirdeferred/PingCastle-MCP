# PyInstaller entry point — avoids relative-import issue in __main__.py
import sys

from pingcastle_mcp.__main__ import main

sys.exit(main())
