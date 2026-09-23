# ElastNetMT Diagnostics Catalog

CODES = {
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
        "title": "Singular Matrix Error",
        "user_message": "The Kirchhoff/Hessian matrix is singular and cannot be inverted.",
        "user_hint": "This usually happens when the system is not fully connected. Check your cutoff and selection.",
    },
    "ENM-E030": {
        "title": "Negative Eigenvalues",
        "user_message": "Detected negative eigenvalues in ANM (min: {min_ev:.2e}).",
        "user_hint": "The input structure is not at a local minimum. Minimize the structure before ENM analysis.",
    },
}

SIGNALS = {
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
