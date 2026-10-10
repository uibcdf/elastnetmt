# ElastNetMT Diagnostics Catalog

CODES = {
    "ENM-E001": {
        "title": "Invalid Argument",
        "user_message": "Argument '{argument}' requires {requirement}.",
        "user_hint": "Consult the operation's documented argument contract.",
    },
    "ENM-W001": {
        "title": "Isolated Nodes Detected",
        "user_message": "Some nodes in the system have no contacts within the specified cutoff ({cutoff}).",
        "user_hint": "Try increasing the cutoff distance or check if the molecular system is correctly loaded.",
    },
    "ENM-W005": {
        "title": "Low Network Connectivity",
        "user_message": "The average degree of the network is low ({avg_degree:.2f}).",
        "user_hint": "A low connectivity might lead to unstable normal modes. Consider a larger cutoff.",
    },
    "ENM-W010": {
        "title": "Low B-factor Correlation",
        "user_message": "The correlation between modeled and experimental B-factors is low ({correlation:.3f}).",
        "user_hint": "This might indicate that the selection or the force constant is not optimal for this system.",
    },
    "ENM-W015": {
        "title": "Small Spectral Gap",
        "user_message": "The gap between rigid and vibrational modes is very small ({gap:.2e}).",
        "user_hint": "The system might be near-singular or poorly constrained. Check for missing residues.",
    },
    "ENM-E020": {
        "title": "Degenerate Network",
        "user_message": "The {model} network has {n_zero_modes} zero modes; expected {expected_zero_modes} rigid modes.",
        "user_hint": "Check connectivity and geometric constraints; increase the cutoff or revise the node selection.",
    },
    "ENM-E011": {
        "title": "Undefined Correlation",
        "user_message": "Pearson correlation is undefined for the constant '{argument}' profile.",
        "user_hint": "Use varying experimental B factors and a network with a varying fluctuation profile.",
    },
    "ENM-E021": {
        "title": "No Admissible Cutoff",
        "user_message": "No cutoff in the requested grid gives a connected GNM network with a defined B-factor correlation.",
        "user_hint": "Revise the cutoff range or selection. The previous model state has been preserved.",
    },
    "ENM-E030": {
        "title": "Invalid Spectrum",
        "user_message": "The {model} eigendecomposition is invalid: {reason}.",
        "user_hint": "Check the coordinates, matrix construction and numerical backend.",
    },
}

SIGNALS = {
    "elastnetmt.model.trajectory": {
        "description": "Trajectory amplitude, mode and executed interpolation engine.",
        "level": "INFO",
    },
    "elastnetmt.model.selection": {
        "description": "Details about the atoms selected for the network nodes.",
        "level": "DEBUG",
    },
    "elastnetmt.model.make_model": {
        "description": "Emitted during the construction of the ENM model.",
        "level": "INFO",
    },
    "elastnetmt.model.spectral_stats": {
        "description": "Physical properties of the calculated spectrum.",
        "level": "DEBUG",
    },
}
