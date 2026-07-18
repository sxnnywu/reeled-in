"""Presentation analysis for GET /tests/{id}. Encodes the display semantics of
CONTRACTS §3a / SCORING_SCIENCE.md §6-§7 server-side, so the frontend just renders
what it's told instead of re-deriving science. Owner: C (Seb) + B (signal ranking).

- **profile** (1 variant): mode only. No winner, grade, or ranking — a single clip is a
  profile, not a verdict (SCORING_SCIENCE §6).
- **comparison** (2+): winner + per-network AND per-signal advantage + ranking, decided by
  the REAL measured signals (5 brain networks + observable production signals), NOT by
  peak/sustained/retention/overall (SCORING_SCIENCE §7). Ranking is delegated to
  `scoring.signals.rank_scores` — the single source of truth for the winner.
"""
from backend.scoring.signals import rank_scores


def build_analysis(test: dict, variants: list, scores: list) -> dict:
    if len(variants) <= 1:
        return {"mode": "profile"}  # §3a: profile only — no winner/grade/ranking

    analysis = {"mode": "comparison"}

    by_vid = {s["variant_id"]: s for s in scores}
    scored = [v for v in variants if v["id"] in by_vid]
    if len(scored) < 2:
        return analysis  # not enough scored variants yet (status pending/scoring)

    ranked = rank_scores([by_vid[v["id"]] for v in scored])
    label_of = {v["id"]: v["label"] for v in scored}
    analysis.update({
        # ranking + winner come from the real signals, not an objective metric
        "ranking": [{"variant_id": r["variant_id"], "label": label_of.get(r["variant_id"]),
                     "index": r["index"]} for r in ranked["ranking"]],
        "winner_variant_id": ranked["winner_variant_id"],
        "network_advantage": ranked.get("network_advantage"),   # family A: winner − runner-up per brain network
        "signal_advantage": ranked.get("signal_advantage"),     # family B: winner − runner-up per production signal
        "decisive": ranked.get("decisive"),                     # the component (brain:* or signal:*) that separated them
    })
    return analysis
