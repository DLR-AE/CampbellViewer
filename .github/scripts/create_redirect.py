#!/usr/bin/python

import sys
import os
from pathlib import Path

version = sys.argv[1]

# Write the redirect file to the newest version
p = Path(os.getcwd()) / 'redirect' / 'index.html'
p.write_text(
    f"<head>\n"
    f"    <meta http-equiv=\"Refresh\" content=\"0; url='/campbellviewer/{version}'\" />\n"
    f"</head>"
)
