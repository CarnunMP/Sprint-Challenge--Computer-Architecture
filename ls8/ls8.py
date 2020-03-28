#!/usr/bin/env python3

"""Main."""

import sys
from cpu import *

cpu = CPU()

if len(sys.argv) != 2:
    print("error: cla should be of the form 'py ls8.py examples/<filename>'")
    sys.exit(1)

cpu.load(f'{sys.argv[1]}')
cpu.run()