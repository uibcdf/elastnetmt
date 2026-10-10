"""Validated GNM B-factor profiles and numerically scaled least-squares fitting.

The experimental boundary requires square-length quantities and returns
square-angstrom magnitudes. Pearson fitting requires finite, nonnegative,
varying profiles, one value per node. Variation below float64 roundoff is
constant; no artificial correlation is assigned to such a profile.
"""

import numpy as np
import pyunitwizard as puw
from pyunitwizard._private.exceptions import ArgumentError as QuantityArgumentError

from .arguments import invalid
from .smonitor import ArgumentError, UndefinedCorrelationError


def validate_profile(values, *, n_nodes, argument):
    """Return a flat varying profile, rejecting missing or invalid observations."""
    if values is None:
        invalid(argument, "an available experimental B-factor profile")
    profile = np.asarray(values, dtype=float)
    if n_nodes < 2 or profile.shape not in ((n_nodes,), (1, n_nodes)):
        invalid(
            argument,
            "one scalar value per node in a single structure with at least two nodes",
        )
    profile = profile.reshape(-1)
    if (
        profile.size != n_nodes
        or not np.all(np.isfinite(profile))
        or np.any(profile < 0)
    ):
        invalid(argument, f"{n_nodes} finite nonnegative values, one per node")
    maximum = np.max(profile)
    if np.ptp(profile) <= 64 * np.finfo(float).eps * maximum:
        raise UndefinedCorrelationError(extra={"argument": argument})
    return profile


def experimental_profile(quantity, *, n_nodes):
    """Validate an experimental quantity and convert explicitly to square angstroms."""
    if quantity is None:
        invalid("b_factor", "an available experimental B-factor profile")
    try:
        quantity = puw.ensure_quantity(quantity, dimensionality={"[L]": 2})
        values = puw.get_value(quantity, to_unit="angstroms**2")
    except QuantityArgumentError as exc:
        try:
            invalid("b_factor", "a profile with explicit square-length units")
        except ArgumentError as error:
            raise error from exc
    return validate_profile(values, n_nodes=n_nodes, argument="b_factor")


def fit_profiles(experimental, theoretical):
    """Return finite scale and Pearson correlation without modifying either profile."""
    experimental = validate_profile(
        experimental, n_nodes=len(theoretical), argument="b_factor"
    )
    theoretical = validate_profile(
        theoretical, n_nodes=len(experimental), argument="theoretical_b_factors"
    )
    exp_max, theo_max = np.max(experimental), np.max(theoretical)
    exp_scaled, theo_scaled = experimental / exp_max, theoretical / theo_max
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            scale = float(
                (exp_max / theo_max)
                * (np.dot(exp_scaled, theo_scaled) / np.dot(theo_scaled, theo_scaled))
            )
            # A finite scale alone does not guarantee representable predictions.
            prediction = scale * theoretical
            if not np.all(np.isfinite(prediction)):
                raise FloatingPointError("nonfinite calibrated prediction")
    except FloatingPointError as exc:
        try:
            invalid(
                "b_factor",
                "a profile yielding a representable finite calibration scale and prediction",
            )
        except ArgumentError as error:
            raise error from exc
    exp_centered, theo_centered = (
        exp_scaled - exp_scaled.mean(),
        theo_scaled - theo_scaled.mean(),
    )
    correlation = float(
        np.clip(
            np.dot(exp_centered, theo_centered)
            / (np.linalg.norm(exp_centered) * np.linalg.norm(theo_centered)),
            -1,
            1,
        )
    )
    return scale, correlation
