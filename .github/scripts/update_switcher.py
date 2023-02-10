#!/usr/bin/python

import json
import os
from pathlib import Path

# Read generated tags.txt file
vp = Path(os.getcwd()) / 'tags.txt'
tags = vp.read_text().split('\n')

# Check if tags are versions
versions = [tag for tag in tags if tag.startswith('v')]

# Add all versions to switcher file
lv = []
for version in versions:
    lv.append(
        {
            'name': f'{version}',
            'version': f'{version}',
            'url': f'https://DLR-AE.github.io/CampbellViewer/{version}/'
        }
    )

# Write to file
p = Path(os.getcwd()) / 'redirect' /  'switcher.json'
with p.open('w') as f:
    json.dump(lv, fp=f, sort_keys=True, indent=4)
