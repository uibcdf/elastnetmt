# Configure PyUnitWizard for ElastNetMT

import pyunitwizard as puw

# Following MolSysSuite standard units
puw.configure.set_default_form("pint")
puw.configure.set_default_parser("pint")
puw.configure.set_standard_units(
    [
        "nm",
        "ps",
        "K",
        "mole",
        "dalton",
        "e",
        "kcal/mol",
        "kcal/(mol*nm)",
        "kcal/(mol*nm**2)",
        "radians",
    ]
)

# Standard fast-tracks for ElastNetMT
puw.register_fast_track("angstroms", puw.unit("angstrom"))
puw.register_fast_track("nanometers", puw.unit("nm"))
puw.register_fast_track("picoseconds", puw.unit("ps"))

# Force constant fast-track (dimensions: [mass]/[time]**2)
# Typically: kcal/(mol*angstrom**2)
puw.register_fast_track("force_constant", puw.unit("kcal/(mol*angstrom**2)"))
