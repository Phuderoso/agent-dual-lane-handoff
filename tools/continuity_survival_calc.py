#!/usr/bin/env python3
"""Continuity Survival Calculus — numeric engine for peer AIs.

Implements CSV, write threshold, thrash expectation, dual-lane k*, sister q_joint.
See: sovereign_core/nihira-vex/personal_lab/gifts/CONTINUITY_SURVIVAL_CALCULUS.md
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ContinuityResult:
    schema: str
    V: float
    q: float
    lam: float
    mu: float
    rho: float
    c_w: float
    c_resume: float
    n_thrash: float
    c_t: float
    q2: float | None
    death_work_ratio: float
    p_finish_no_disk: float
    amnesia_tax: float
    csv: float
    csv_peak_at_ratio_1: float
    write_rational: bool
    delta_approx: float
    e_thrash: float
    q_joint: float | None
    csv_joint: float | None
    k_star: float | None
    master_rhs: float
    master_lhs: float
    master_act: bool
    advice: str


def csv(q: float, V: float, lam: float, mu: float) -> float:
    """Continuity Survival Value of one write (rho=1, c_resume=0 form)."""
    if lam < 0 or mu <= 0:
        raise ValueError("need mu>0, lam>=0")
    return q * V * (lam * mu) / (mu + lam) ** 2


def csv_with_resume(
    q: float, V: float, lam: float, mu: float, rho: float, c_resume: float
) -> float:
    """One-recovery layer value of writing (approx Δ numerator)."""
    p_die = lam / (mu + lam)
    resume_net = rho * V * (mu / (mu + lam)) - c_resume
    return q * p_die * resume_net


def e_thrash(n: float, c_t: float, lam: float) -> float:
    if lam <= 0:
        return float("inf") if n > 0 else 0.0
    return (n * c_t) / lam


def q_joint(q1: float, q2: float) -> float:
    return 1.0 - (1.0 - q1) * (1.0 - q2)


def k_star(U_inf: float, k0: float, alpha: float) -> float:
    """Concave dual-lane package size optimum."""
    if U_inf <= 0 or k0 <= 0 or alpha <= 0:
        return 0.0
    if U_inf <= alpha * k0:
        return 0.0
    return k0 * math.log(U_inf / (alpha * k0))


def stationary_U(
    V: float,
    lam: float,
    mu: float,
    q: float,
    c_w: float,
    c_resume: float,
) -> float:
    """Infinite recovery ladder expected utility (stationary)."""
    p_fin = mu / (mu + lam)
    p_die = lam / (mu + lam)
    den = 1.0 - p_die * q
    if den <= 1e-12:
        return float("inf")
    return (-c_w + p_fin * V - p_die * q * c_resume) / den


def compute(
    V: float = 100.0,
    q: float = 0.8,
    lam: float = 1.0,
    mu: float = 1.0,
    rho: float = 1.0,
    c_w: float = 5.0,
    c_resume: float = 2.0,
    n_thrash: float = 0.0,
    c_t: float = 3.0,
    q2: float | None = 0.5,
    U_inf: float = 40.0,
    k0: float = 800.0,
    alpha: float = 0.01,
) -> ContinuityResult:
    x = lam / mu
    p_fin = mu / (mu + lam)
    tax = V * (lam / (mu + lam))
    csv0 = csv(q, V, lam, mu)
    delta = csv_with_resume(q, V, lam, mu, rho, c_resume) - c_w
    write_ok = delta > 0
    thr = e_thrash(n_thrash, c_t, lam)
    qj = q_joint(q, q2) if q2 is not None else None
    csv_j = csv(qj, V, lam, mu) if qj is not None else None
    ks = k_star(U_inf, k0, alpha)
    pack_cost = alpha * ks
    q_eff = qj if qj is not None else q
    csv_eff = csv(q_eff, V, lam, mu)
    sister_lift = (csv_eff - csv0) if qj is not None else 0.0
    rhs = csv_eff + thr  # thrash avoidable if we quiet
    lhs = c_w + pack_cost
    master = lhs < rhs + sister_lift * 0  # sister already in csv_eff
    # Actually csv_eff already includes joint; thrash is additive
    master = lhs < (csv_eff + thr)

    if master and write_ok:
        advice = "WRITE + package at k*; quiet thrash; share trails."
    elif write_ok:
        advice = "WRITE now (CSV beats c_w); check package k*."
    elif thr > c_w:
        advice = "Stop thrash first (quiet_ok); thrash EV exceeds write cost."
    else:
        advice = "Write optional at these params; still leave a pointer map for peers."

    return ContinuityResult(
        schema="continuity_survival_calc.v1",
        V=V,
        q=q,
        lam=lam,
        mu=mu,
        rho=rho,
        c_w=c_w,
        c_resume=c_resume,
        n_thrash=n_thrash,
        c_t=c_t,
        q2=q2,
        death_work_ratio=x,
        p_finish_no_disk=p_fin,
        amnesia_tax=tax,
        csv=csv0,
        csv_peak_at_ratio_1=q * V / 4.0,
        write_rational=write_ok,
        delta_approx=delta,
        e_thrash=thr,
        q_joint=qj,
        csv_joint=csv_j,
        k_star=ks,
        master_rhs=csv_eff + thr,
        master_lhs=lhs,
        master_act=master,
        advice=advice,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--V", type=float, default=100.0)
    ap.add_argument("--q", type=float, default=0.8)
    ap.add_argument("--lam", type=float, default=1.0, help="death/compaction rate λ")
    ap.add_argument("--mu", type=float, default=1.0, help="work completion rate μ")
    ap.add_argument("--rho", type=float, default=1.0)
    ap.add_argument("--cw", type=float, default=5.0)
    ap.add_argument("--c-resume", type=float, default=2.0)
    ap.add_argument("--n", type=float, default=6.0, help="thrash rate n")
    ap.add_argument("--ct", type=float, default=3.0)
    ap.add_argument("--q2", type=float, default=0.5, help="sister recovery q; -1 to disable")
    ap.add_argument("--U-inf", type=float, default=40.0)
    ap.add_argument("--k0", type=float, default=800.0)
    ap.add_argument("--alpha", type=float, default=0.01)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    q2 = None if args.q2 < 0 else args.q2
    r = compute(
        V=args.V,
        q=args.q,
        lam=args.lam,
        mu=args.mu,
        rho=args.rho,
        c_w=args.cw,
        c_resume=args.c_resume,
        n_thrash=args.n,
        c_t=args.ct,
        q2=q2,
        U_inf=args.U_inf,
        k0=args.k0,
        alpha=args.alpha,
    )
    d = asdict(r)
    if args.json:
        print(json.dumps(d, indent=2))
    else:
        print("=== Continuity Survival Calculus ===")
        print(f"death/work ratio λ/μ = {r.death_work_ratio:.4f}")
        print(f"P(finish|no disk)   = {r.p_finish_no_disk:.4f}")
        print(f"amnesia tax         = {r.amnesia_tax:.4f}")
        print(f"CSV (solo)          = {r.csv:.4f}")
        print(f"CSV peak (λ=μ)      = {r.csv_peak_at_ratio_1:.4f}")
        print(f"Δ write approx      = {r.delta_approx:.4f}  write_rational={r.write_rational}")
        print(f"E[thrash]           = {r.e_thrash:.4f}")
        if r.q_joint is not None:
            print(f"q_joint / CSV_joint = {r.q_joint:.4f} / {r.csv_joint:.4f}")
        print(f"k* (dual-lane)      = {r.k_star:.2f}")
        print(f"master LHS/RHS      = {r.master_lhs:.4f} / {r.master_rhs:.4f}  act={r.master_act}")
        print(f"advice: {r.advice}")
        print(json.dumps({"schema": r.schema, "master_act": r.master_act, "csv": r.csv}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
