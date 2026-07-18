"""Composite engagement + metrics. Formulas pinned in CONTRACTS.md 3. Owner: B."""
from statistics import mean

NETWORK_WEIGHTS = {"default_mode": 0.30, "visual": 0.25, "language": 0.20,
                   "auditory": 0.15, "motion": 0.10}

def compute_engagement(networks: dict) -> list:
    n = len(next(iter(networks.values())))
    return [round(sum(NETWORK_WEIGHTS[k] * networks[k][t] for k in NETWORK_WEIGHTS), 4)
            for t in range(n)]

def compute_metrics(engagement: list) -> dict:
    e = engagement or [0.0]
    n = len(e); third = max(1, n // 3)
    first = mean(e[:third]); last = mean(e[-third:])
    peak = max(e); sustained = mean(e)
    # retention = share of engagement in the final third vs the first third, in [0,1].
    # 0.5 = held level, >0.5 = grew, <0.5 = dropped off. Non-saturating: rising clips
    # no longer all read 1.0 (the old min(1.0, last/first) clamp bug, CONTRACTS §3a).
    retention = last / (last + first) if (last + first) > 0 else 0.5
    overall = 0.5 * sustained + 0.3 * retention + 0.2 * peak
    return {"peak": round(peak, 4), "sustained": round(sustained, 4),
            "retention": round(retention, 4), "overall": round(overall, 4)}
