#!/usr/bin/python

import sys
import os
from pathlib import Path

# Get input argument
version = sys.argv[1]

# Replace development version string with proper version from git tag
path = Path(os.getcwd()) / 'campbellviewer' / '__init__.py'
txt = path.read_text().replace("__version__ = '0.0.0-dev'", f"__version__ = '{version}'")
path.write_text(txt)
