"""Composite engagement curve. Weights pinned in CONTRACTS.md §3. Owner: B.

The legacy scalar metrics (peak / sustained / retention / overall) were removed —
they never ranked the winner (that's scoring.signals.rank_scores) and are no longer
part of the Score Object. The composite `engagement` curve stays: it's the weighted
blend of the 5 networks that the UI plots and that the signal-based winner reads.
"""

NETWORK_WEIGHTS = {"default_mode": 0.30, "visual": 0.25, "language": 0.20,
                   "auditory": 0.15, "motion": 0.10}

def compute_engagement(networks: dict) -> list:
    n = len(next(iter(networks.values())))
    return [round(sum(NETWORK_WEIGHTS[k] * networks[k][t] for k in NETWORK_WEIGHTS), 4)
            for t in range(n)]
