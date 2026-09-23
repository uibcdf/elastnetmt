# ArgDigest configuration for ElastNetMT

ARGUMENT_DIGESTERS = {
    "molecular_system": {
        "kind": "std",
        "rules": ["is_not_none"],
    },
    "selection": {
        "kind": "std",
        "rules": ["is_str"],
        "default": 'atom_name=="CA"',
    },
    "syntax": {
        "kind": "std",
        "rules": ["is_str"],
        "default": "MolSysMT",
    },
    "cutoff": {
        "kind": "quantity",
        "dimensionality": {"[L]": 1},
        "default_unit": "angstroms",
    },
    "structure_index": {
        "kind": "std",
        "rules": ["is_int"],
        "default": 0,
    },
}
