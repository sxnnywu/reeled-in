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
from statistics import mean

from backend.scoring.signals import rank_scores


def _decisive_detail(decisive: str, variants: list, by_vid: dict) -> dict:
    """The winner's differentiator, made renderable: the friendly label of the deciding
    dimension + each variant's value on it, sorted winner-first. This is the honest
    "why B won" number for the results header — it always agrees with the winner (unlike
    average engagement, which can disagree). None if there's no decisive component."""
    if not decisive or ":" not in decisive:
        return None
    from backend.science import COMPONENTS

    family, key = decisive.split(":", 1)
    label = next((c["label"] for c in COMPONENTS if c["key"] == decisive), key)

    def value_for(v):
        s = by_vid.get(v["id"]) or {}
        if family == "brain":
            arr = (s.get("networks") or {}).get(key) or []
            return round(mean(arr), 3) if arr else None
        return round(float((s.get("signals") or {}).get(key, 0.0)), 3)

    values = [{"variant_id": v["id"], "label": v["label"], "value": value_for(v)}
              for v in variants if v["id"] in by_vid]
    values.sort(key=lambda x: (x["value"] is None, -(x["value"] or 0)))  # winner (higher) first
    return {"component": decisive, "label": label, "values": values}


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
        # the deciding dimension + each variant's value on it, winner-first (for the header)
        "decisive_detail": _decisive_detail(ranked.get("decisive"), scored, by_vid),
    })
    return analysis
