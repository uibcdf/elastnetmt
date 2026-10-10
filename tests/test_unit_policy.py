"""Import order must preserve the application's active quantity policy (#14)."""

import os
import subprocess
import sys


def test_import_preserves_application_unit_policy():
    code = """
import pyunitwizard as puw
puw.configure.set_standard_units(['angstrom', 'fs', 'kcal/mol'], provenance='application')
before = puw.configure.report()
import elastnetmt
after = puw.configure.report()
for field in ('default_form', 'default_parser', 'standard_units', 'provenance'):
    assert after[field] == before[field], (field, before, after)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
