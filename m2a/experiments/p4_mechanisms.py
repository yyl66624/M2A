"""Phase IV: the same three laws in three independent noise substrates (logistic, probit, Gumbel)."""
from __future__ import annotations

import numpy as np

SUBSTRATES = ("logistic", "probit", "gumbel")


def cdf(z, kind: str):
    z = np.asarray(z, dtype=float)
    if kind == "logistic":
        return 1.0 / (1.0 + np.exp(-z))
    if kind == "probit":
        # Abramowitz-Stegun-free: use erf via numpy's erf if available, else math.erf
        from math import erf, sqrt
        v = np.vectorize(lambda t: 0.5 * (1.0 + erf(t / sqrt(2.0))))(z)
        return v
    if kind == "gumbel":
        return np.exp(-np.exp(-z))
    raise ValueError(kind)


def quantile(alpha: float, kind: str) -> float:
    """Inverse CDF in closed form (used for the predicted thresholds)."""
    if kind == "logistic":
        return float(np.log(alpha / (1 - alpha)))
    if kind == "probit":
        # rational approximation to the normal quantile (Acklam), accurate to ~1e-9
        a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
             1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
        b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
             6.680131188771972e+01, -1.328068155288572e+01]
        c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
             -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
        d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
             3.754408661907416e+00]
        p = alpha
        if p < 0.02425:
            q = np.sqrt(-2 * np.log(p))
            return float((((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
                         ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1))
        if p > 1 - 0.02425:
            return -quantile(1 - p, "probit")
        q = p - 0.5
        r = q * q
        return float((((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q /
                     (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1))
    if kind == "gumbel":
        return float(-np.log(-np.log(alpha)))
    raise ValueError(kind)


def predicted_threshold(kind: str, alpha: float = 0.05) -> float:
    return quantile(1 - alpha, kind) - quantile(alpha, kind)


def p_unit(drive, beta, theta, kind):
    return float(cdf(beta * (drive - theta), kind))


def window_exists(kind: str, beta: float, alpha: float = 0.05,
                  theta_grid=None) -> bool:
    """A window exists at this beta iff some theta makes single-path <= alpha and joint >= 1-alpha."""
    if theta_grid is None:
        theta_grid = np.linspace(-0.5, 1.5, 2001)
    single = cdf(beta * (0.0 - theta_grid), kind)
    joint = cdf(beta * (1.0 - theta_grid), kind)
    return bool(np.any((single <= alpha) & (joint >= 1 - alpha)))


def critical_beta(kind: str, alpha: float = 0.05, lo=0.5, hi=15.0, tol=1e-3) -> float:
    """Smallest beta with a window, by bisection on window_exists (monotone in beta)."""
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if window_exists(kind, mid, alpha):
            hi = mid
        else:
            lo = mid
        if hi - lo < tol:
            break
    return float(hi)


def gate_curve(kind: str, xs, o: float, beta=6.0, theta=0.5):
    xs = np.asarray(xs, dtype=float)
    return cdf(beta * (xs * (2.0 * o - 1.0) - theta), kind)


def bayes_sensitivity(q: float, gamma=0.9, v_b=0.5, c=0.1, n_cues: int = 20000,
                      seed: int = 0) -> float:
    """Independent estimator: Beta-Binomial posterior over P(B|cue), then the same readout law.

    The probe state conditions on max=0.9, so the prior over B-availability is 1/2; the posterior
    given a cue with accuracy q after one observation is q (resp. 1-q).
    """
    rng = np.random.RandomState(seed)
    post = {}
    for cue in (0, 1):
        # Rejection sampling from the generative model: draw B-availability from the prior, draw the
        # cue with accuracy q, and keep only the draws whose cue equals the conditioning value.
        b = rng.rand(n_cues) < 0.5
        cue_draw = np.where(rng.rand(n_cues) < q, b.astype(int), 1 - b.astype(int))
        keep = cue_draw == cue
        post[cue] = float(b[keep].mean()) if keep.any() else 0.5
    return float(gamma * (v_b - c) * (post[1] - post[0]))
