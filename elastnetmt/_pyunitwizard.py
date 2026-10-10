"""Declare the shared MolSysSuite baseline without replacing an active policy."""

import pyunitwizard as puw

STANDARD_UNITS = [
    "nm",
    "ps",
    "K",
    "mole",
    "dalton",
    "e",
    "kJ/mol",
    "kJ/(mol*nm)",
    "kJ/(mol*nm**2)",
    "radians",
]

if not puw.configure.has_active_policy():
    puw.configure.set_default_form("pint")
    puw.configure.set_default_parser("pint")
    puw.configure.set_standard_units(STANDARD_UNITS, provenance="elastnetmt")

# Standard fast-tracks for ElastNetMT
puw.register_fast_track("angstroms", puw.unit("angstrom"))
puw.register_fast_track("nanometers", puw.unit("nm"))
puw.register_fast_track("picoseconds", puw.unit("ps"))

# Force constant fast-track (dimensions: [mass]/[time]**2)
# Typically: kcal/(mol*angstrom**2)
puw.register_fast_track("force_constant", puw.unit("kcal/(mol*angstrom**2)"))
