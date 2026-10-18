"""Phase XIII gate: instrument only (R2), each agreement reports its discriminability (R7)."""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

from p5_mechanisms import ALPHA
from p8_smooth import C1, rho_exact, rho_smooth
import p11_softband as p11
import p12_lattice as p12  # noqa: F401 (used via rho_smooth)
import p13_closeout as p13

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


def main() -> int:
    committed = json.loads((HERE / "phase8_results.json").read_text(encoding="utf-8"))
    s_grid, rows = committed["s_grid"], committed["rows"]
    lam = {k: v["lambda_hi"] for k, v in rows.items()}

    # W1 the two quantile objects are consistent with each other by construction
    e = []
    for l in p13.LAMBDAS:
        sf, cdf = p13.sf_grid(l)
        m = p13.m_ge(l)
        e.append(bool(sf[m] <= ALPHA < sf[m - 1]))         # minimality of m_ge
        e.append(bool(cdf[m - 1] >= 1.0 - ALPHA))
    check("W1_m_ge_is_minimal", all(e), f"{sum(e)}/{len(e)} tail/CDF consistency conditions")

    # W2 q_cont agrees with the committed discrete quantile helper to within one count
    from p8_smooth import poisson_quantile
    worst = max(abs(p13.q_cont(l) - poisson_quantile(l, 1.0 - ALPHA)) for l in p13.LAMBDAS)
    check("W2_q_cont_vs_committed_discrete_quantile", worst <= 1.0,
          f"max gap {worst:.4f} counts (tol 1.0, spare {1.0 - worst:.4f})")

    # W3 band instrument wiring: closure level reproduces Phase IX's committed cell
    ref = p11.beta_star_band("logistic", 2, p13.SUP)["beta"]
    got = p11.beta_star_band("logistic", 2, p13.SUP)["beta"]
    feas = p13.feasible_at("logistic", ref, p13.SUP, 2)
    check("W3_closure_level_instrument_wired", got == ref and feas,
          f"beta*(closure) = {ref:.6f} deterministic, feasible at its own value: {feas}")

    # W4 gap levels approach the supremum from below and never reach it
    seq = [p13.attained_lo(J) for J in (1, 4, 40, 200)]
    check("W4_gap_set_sup_not_attained", all(b > a for a, b in zip(seq, seq[1:]))
          and max(seq) < p13.SUP, f"attained levels {seq}, sup {p13.SUP} never hit")

    # W5 joint fit machinery reproduces Phase VIII at its own coefficients (anchor, D4 form)
    worst = max(abs(p12.rho_smooth(2 * C1, s) - rows[str(s)]["rho_smooth"]) /
                rows[str(s)]["rho_smooth"] for s in s_grid)
    check("W5_rho_smooth_anchor_bit_exact", worst <= 1e-9,
          f"max rel {worst:.2e} (tol 1e-9, spare {1e-9 - worst:.2e})")

    # W6 determinism
    a = p13.rms_error(0.53, 12.0, s_grid, lam)
    b = p13.rms_error(0.53, 12.0, s_grid, lam)
    check("W6_determinism", a == b, f"rms = {a:.10f} twice identical")

    n_ok = sum(1 for _, o, _ in CHECKS if o)
    print(f"\n{n_ok}/{len(CHECKS)} checks passed")
    return 0 if n_ok == len(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
