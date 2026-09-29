"""Permite `python -m traffic_analyzer` quando `src` está no caminho de importação."""

import sys

from traffic_analyzer.cli import main

if __name__ == "__main__":
    sys.exit(main())
