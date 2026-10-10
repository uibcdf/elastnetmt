"""Reusable value contracts for public ENM operations."""

from numbers import Integral

import numpy as np
import pyunitwizard as puw
from pyunitwizard._private.exceptions import ArgumentError as QuantityArgumentError

from .smonitor import ArgumentError


def invalid(argument, requirement):
    raise ArgumentError(
        code="ENM-E001", extra={"argument": argument, "requirement": requirement}
    )


def integer(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
        invalid(name, f"an integer greater than or equal to {minimum}")
    return int(value)


def text(value, name):
    if not isinstance(value, str) or not value.strip():
        invalid(name, "a nonempty string")
    return value


def length(value, name, allow_none=False, minimum=0):
    if allow_none and value is None:
        return None
    if isinstance(value, str) and value.strip().endswith(" A"):
        value = value.strip()[:-2] + " angstroms"
    try:
        quantity = puw.ensure_quantity(value, dimensionality={"[L]": 1})
        magnitude = puw.get_value(quantity, to_unit="nanometers")
        if np.ndim(magnitude) or not np.isfinite(magnitude) or magnitude < minimum:
            invalid(
                name, f"a finite scalar length greater than or equal to {minimum} nm"
            )
        return quantity
    except ArgumentError:
        raise
    except (QuantityArgumentError, ValueError, TypeError) as exc:
        try:
            invalid(name, "a scalar length with explicit compatible units")
        except ArgumentError as error:
            raise error from exc


def digest_engine(engine):
    if not isinstance(engine, str) or engine not in (
        "auto",
        "vectorized",
        "parallel",
        "gpu",
    ):
        invalid("engine", "one of auto, vectorized, parallel or gpu")
    return engine


def digest_interpolation_engine(interpolation_engine):
    if not isinstance(interpolation_engine, str) or interpolation_engine not in (
        "auto",
        "vectorized",
        "parallel",
        "gpu",
    ):
        invalid("interpolation_engine", "one of auto, vectorized, parallel or gpu")
    return interpolation_engine


def digest_cutoff(cutoff):
    quantity = length(cutoff, "cutoff", allow_none=True)
    if quantity is not None and puw.get_value(quantity, to_unit="nanometers") <= 0:
        invalid("cutoff", "a positive scalar length")
    return quantity


def digest_n_modes(n_modes):
    return (
        n_modes
        if isinstance(n_modes, str) and n_modes == "all"
        else integer(n_modes, "n_modes", 1)
    )


def digest_stiffness(stiffness):
    if stiffness is not None:
        invalid("stiffness", "None; physical stiffness calibration is not implemented")
    return None


def boolean(value, name):
    if not isinstance(value, bool):
        invalid(name, "a boolean")
    return value


def molecular_system(value):
    if value is None:
        invalid("molecular_system", "a molecular system")
    return value


ARGUMENT_DIGESTERS = {
    "molecular_system": molecular_system,
    "selection": lambda value: None if value is None else text(value, "selection"),
    "syntax": lambda value: None if value is None else text(value, "syntax"),
    "structure_index": lambda value: integer(value, "structure_index"),
    "cutoff": digest_cutoff,
    "engine": digest_engine,
    "interpolation_engine": digest_interpolation_engine,
    "stiffness": digest_stiffness,
    "n_modes": digest_n_modes,
    "mode": lambda value: integer(value, "mode"),
    "amplitude": lambda value: length(value, "amplitude"),
    "oscillation_steps": lambda value: integer(value, "oscillation_steps", 1),
    "min_cutoff": lambda value: length(value, "min_cutoff"),
    "max_cutoff": lambda value: length(value, "max_cutoff"),
    "steps": lambda value: integer(value, "steps", 2),
    "show_experimental": lambda value: boolean(value, "show_experimental"),
    "title": lambda value: text(value, "title"),
}
