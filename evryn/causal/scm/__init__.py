# meflux --help

"""SCM package."""

from .structural_causal_model import StructuralCausalModel, StructuralEquation
from .mechanisms import (
    simulate_lotka_volterra,
    simulate_financial_market_cycle,
    linear_mechanism,
    polynomial_mechanism,
    sigmoid_mechanism,
    tanh_mechanism,
    sinusoidal_mechanism,
)
from .generator import CausalTask, CausalTaskGenerator

__all__ = [
    "StructuralCausalModel",
    "StructuralEquation",
    "simulate_lotka_volterra",
    "simulate_financial_market_cycle",
    "linear_mechanism",
    "polynomial_mechanism",
    "sigmoid_mechanism",
    "tanh_mechanism",
    "sinusoidal_mechanism",
    "CausalTask",
    "CausalTaskGenerator",
]
