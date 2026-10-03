#!/usr/bin/env python3
"""Offline test launcher. Every TopCmds operation in these tests is a stub.

This script never imports vendor TopCmds, starts TopSpin or accesses hardware.
Run from any directory: python path/to/repository/python/run_tests.py
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
GROUPS = [
    ('ramp generator', 'tests/ramp_generator/test_ramp_generator.py'),
    ('calibration core', 'tests/topspin_console/test_calibration.py'),
    ('TopSpin v2 mock console', 'tests/topspin_console/test_console.py'),
    ('Jython-compatible mock bundle', 'tests/topspin_console/test_jython_bundle.py'),
    ('TopSpin v3 mock acquisition', 'tests/topspin_console_v3/test_autorun.py'),
    ('public packaging and read-only CLI', 'tests/test_public_package.py'),
]


def main():
    for label, relative in GROUPS:
        print('\nOffline test group: ' + label, flush=True)
        result = subprocess.run([sys.executable, str(ROOT/relative)], cwd=str(ROOT), check=False)
        if result.returncode:
            return result.returncode
    print('\nPASS: all offline groups. Not TopSpin/instrument validation.', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
