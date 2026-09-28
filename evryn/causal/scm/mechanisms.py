# meflux --help

"""Causal mechanisms and dynamical systems supporting Causality in Flux.

Includes:
- Additive Noise Models (ANM)
- Linear and Non-Linear mechanisms (polynomial, sigmoid, tanh, sine)
- Lotka-Volterra predator-prey cyclical system (Paper Example 1)
- Financial market cyclic dynamics (Paper Example 1 & Figure 1)
- Non-Gaussian exogenous noise generators (Laplace, Uniform, Gumbel, Student-t)
"""

from typing import Callable, Tuple
import numpy as np



def gaussian_noise(scale: float = 1.0) -> Callable[[int], np.ndarray]:
    return lambda n: np.random.normal(0.0, scale, size=n)


def laplace_noise(scale: float = 1.0) -> Callable[[int], np.ndarray]:
    return lambda n: np.random.laplace(0.0, scale, size=n)


def uniform_noise(low: float = -1.0, high: float = 1.0) -> Callable[[int], np.ndarray]:
    return lambda n: np.random.uniform(low, high, size=n)


def gumbel_noise(loc: float = 0.0, scale: float = 1.0) -> Callable[[int], np.ndarray]:
    return lambda n: np.random.gumbel(loc, scale, size=n)


def student_t_noise(df: float = 3.0) -> Callable[[int], np.ndarray]:
    return lambda n: np.random.standard_t(df, size=n)



def linear_mechanism(weight: float = 1.0) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
    def fn(x: np.ndarray, noise: np.ndarray) -> np.ndarray:
        return weight * x + noise
    return fn


def polynomial_mechanism(deg: int = 2, scale: float = 0.5) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
    def fn(x: np.ndarray, noise: np.ndarray) -> np.ndarray:
        return scale * (x ** deg) + noise
    return fn


def sigmoid_mechanism(steepness: float = 2.0, scale: float = 1.5) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
    def fn(x: np.ndarray, noise: np.ndarray) -> np.ndarray:
        sig = 1.0 / (1.0 + np.exp(-steepness * x))
        return scale * (sig - 0.5) + noise
    return fn


def tanh_mechanism(scale: float = 1.5) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
    def fn(x: np.ndarray, noise: np.ndarray) -> np.ndarray:
        return scale * np.tanh(x) + noise
    return fn


def sinusoidal_mechanism(freq: float = 1.0, amp: float = 1.0) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
    def fn(x: np.ndarray, noise: np.ndarray) -> np.ndarray:
        return amp * np.sin(freq * x) + noise
    return fn



def simulate_lotka_volterra(
    num_samples: int = 1000,
    alpha: float = 1.1,
    beta: float = 0.4,
    delta: float = 0.1,
    gamma: float = 0.4,
    dt: float = 0.05,
    noise_std: float = 0.05,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """Simulate Lotka-Volterra predator-prey dynamics with slight phase shift.

    dx/dt = alpha*x - beta*x*y   (prey)
    dy/dt = delta*x*y - gamma*y   (predator)
    Highlighted in Section 1 (Example 1) of the paper.
    Returns:
        (prey, predator) arrays of shape (num_samples,)
    """
    rng = np.random.default_rng(seed)
    x = np.zeros(num_samples)
    y = np.zeros(num_samples)
    x[0] = 10.0 + rng.normal(0, 0.5)
    y[0] = 2.0 + rng.normal(0, 0.2)

    for t in range(1, num_samples):
        dx = (alpha * x[t - 1] - beta * x[t - 1] * y[t - 1]) * dt
        dy = (delta * x[t - 1] * y[t - 1] - gamma * y[t - 1]) * dt
        x[t] = max(0.1, x[t - 1] + dx + rng.normal(0, noise_std))
        y[t] = max(0.1, y[t - 1] + dy + rng.normal(0, noise_std))

    return x, y


def simulate_financial_market_cycle(
    num_samples: int = 1000,
    period: float = 50.0,
    phase_shift: float = np.pi / 4.0,
    noise_std: float = 0.1,
    trend: float = 0.001,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """Simulate financial market cycle (stock price and share volume).

    Stock prices and share volume exhibit cyclical patterns with phase shifts,
    sharing causal patterns with Lotka-Volterra systems (Section 1, Fig. 1).
    Returns:
        (stock_price, volume) arrays of shape (num_samples,)
    """
    rng = np.random.default_rng(seed)
    t = np.arange(num_samples)
    cycle = np.sin(2.0 * np.pi * t / period)
    price = 100.0 + 20.0 * cycle + trend * t + rng.normal(0, noise_std * 5, size=num_samples)
    volume = 50.0 + 15.0 * np.sin(2.0 * np.pi * t / period - phase_shift) + rng.normal(0, noise_std * 3, size=num_samples)
    return price, volume
