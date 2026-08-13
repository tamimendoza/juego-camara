"""Enable ``python3 -m src.games.mario`` as the Mario Face Jump entry point."""

import sys

from .main import main

if __name__ == "__main__":
    sys.exit(main())