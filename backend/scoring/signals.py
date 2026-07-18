"""Observable production signals + A/B comparison. Owner: B.

The comparison winner is decided here, by comparing two videos across the REAL
measured signals — the 5 brain networks (predicted neural engagement) plus the
observable production signals (facial expression, speech, hand gesture, motion,
clarity). It does NOT use peak/sustained/retention/overall. Evidence for each
signal + the "more is not better" caveat: SCORING_SCIENCE.md §7.

Every weight here is a literature-informed PRIOR, not fit to outcome data.
"""

from statistics import mean

from backend.scoring import metrics

# Observable production signals we compare on. Values are raw + interpretable;
# comparison normalizes them pairwise (within the A/B pair), so absolute scale
# doesn't matter — consistent with the shared-scale principle.
SIGNAL_KEYS = ["face_expression", "speech_rate", "volume", "hand_gesture", "motion", "clarity"]

# Prior weights (SCORING_SCIENCE §7). Brain networks carry the science-backed
# core; observable signals add behavioural corroboration.
BRAIN_SHARE = 0.6      # weight of the 5 brain networks together
SIGNAL_SHARE = 0.4     # weight of the observable signals together
SIGNAL_WEIGHTS = {     # relative importance among observable signals (sum = 1)
    "face_expression": 0.28,  # smile/affect — McDuff et al. [18]
    "speech_rate":     0.18,  # speech rate — prosody studies [22][23]
    "volume":          0.18,  # vocal loudness/energy — prosodic arousal [22][23]
    "hand_gesture":    0.18,  # gesture energy — JMR 2025 [20]
    "motion":          0.12,  # movement/pacing — JAMS [24]; note: more != better
    "clarity":         0.06,  # sharpness quality gate (weak direct evidence)
}


def collect_signals(objective_result: dict) -> dict:
    """Turn the objective-toolkit output (analyze_objective) into the scorecard's
    `signals` block — raw, interpretable values, one per comparison signal."""
    o = objective_result or {}
    face = o.get("face") or {}
    hands = o.get("hands") or {}
    speech = o.get("speech") or {}
    return {
        "face_expression": round(float(face.get("smile_frac", 0.0)), 4),
        "speech_rate": round(float(speech.get("words_per_sec", 0.0)), 4),
        "volume": round(float(o.get("volume", 0.0)), 5),
        "hand_gesture": round(float(hands.get("hand_motion", 0.0)), 4),
        "motion": round(float(o.get("motion", 0.0)), 4),
        "clarity": round(float(o.get("sharpness", 0.0)), 2),
    }


def _share(a: float, b: float):
    """Pairwise share in [0,1] for the two videos (0.5/0.5 if both ~0)."""
    t = a + b
    return (0.5, 0.5) if t <= 1e-9 else (a / t, b / t)


def _neural_component(a_score: dict, b_score: dict) -> dict:
    """Per-network pairwise shares from the (shared-scale) network curves."""
    out = {}
    for net in metrics.NETWORK_WEIGHTS:
        av = mean(a_score["networks"].get(net) or [0.0])
        bv = mean(b_score["networks"].get(net) or [0.0])
        sa, sb = _share(av, bv)
        out[net] = {"a": round(av, 4), "b": round(bv, 4), "a_share": round(sa, 4), "weight": metrics.NETWORK_WEIGHTS[net]}
    return out


def compare_scores(a_score: dict, b_score: dict, a_label: str = "A", b_label: str = "B") -> dict:
    """Rank two Score Objects on the real signals. Returns the winner, the per-network
    and per-signal deltas, and which components separated them. Never uses
    peak/sustained/retention/overall."""
    a_idx = b_idx = 0.0
    breakdown = {"brain": {}, "signals": {}}

    # Brain networks (neural engagement) — BRAIN_SHARE of the decision.
    for net, w in metrics.NETWORK_WEIGHTS.items():
        av = mean(a_score["networks"].get(net) or [0.0])
        bv = mean(b_score["networks"].get(net) or [0.0])
        sa, sb = _share(av, bv)
        wt = BRAIN_SHARE * w
        a_idx += wt * sa
        b_idx += wt * sb
        breakdown["brain"][net] = {"a": round(av, 4), "b": round(bv, 4),
                                    "favors": a_label if sa >= sb else b_label,
                                    "delta": round(sa - sb, 4)}

    # Observable production signals — SIGNAL_SHARE of the decision.
    sa_sig = a_score.get("signals") or {}
    sb_sig = b_score.get("signals") or {}
    for sig, w in SIGNAL_WEIGHTS.items():
        av = float(sa_sig.get(sig, 0.0))
        bv = float(sb_sig.get(sig, 0.0))
        sa, sb = _share(av, bv)
        wt = SIGNAL_SHARE * w
        a_idx += wt * sa
        b_idx += wt * sb
        breakdown["signals"][sig] = {"a": round(av, 4), "b": round(bv, 4),
                                      "favors": a_label if sa >= sb else b_label,
                                      "delta": round(sa - sb, 4)}

    winner = a_label if a_idx >= b_idx else b_label
    # what most separated them (largest deltas toward the winner)
    allc = [{"component": f"brain:{k}", **v} for k, v in breakdown["brain"].items()] + \
           [{"component": f"signal:{k}", **v} for k, v in breakdown["signals"].items()]
    separated_by = sorted([c for c in allc if c["favors"] == winner],
                          key=lambda c: -abs(c["delta"]))[:3]

    return {
        "winner": winner,
        "index": {a_label: round(a_idx, 4), b_label: round(b_idx, 4)},
        "margin": round(abs(a_idx - b_idx), 4),
        "separated_by": [c["component"] for c in separated_by],
        "breakdown": breakdown,
        "note": "Ranked on brain networks + observable signals (SCORING_SCIENCE §7). "
                "peak/sustained/retention/overall are NOT used. Weights are a prior.",
    }


def _shares(vals: list) -> list:
    t = sum(vals)
    return [1.0 / len(vals)] * len(vals) if t <= 1e-9 else [v / t for v in vals]


def rank_scores(scores: list) -> dict:
    """Rank 2+ Score Objects on the real signals — brain networks (family A) + observable
    production signals (family B). Returns the ordered ranking, winner_variant_id, and the
    winner-vs-runner-up advantage per network and per signal. NEVER uses
    peak/sustained/retention/overall. This is the single source of truth for the A/B winner
    (used by analysis.py and repo.compute_winner)."""
    ids = [s["variant_id"] for s in scores]
    idx = {i: 0.0 for i in ids}

    for net, w in metrics.NETWORK_WEIGHTS.items():
        vals = [mean(s.get("networks", {}).get(net) or [0.0]) for s in scores]
        for i, sh in zip(ids, _shares(vals)):
            idx[i] += BRAIN_SHARE * w * sh
    for sig, w in SIGNAL_WEIGHTS.items():
        vals = [float((s.get("signals") or {}).get(sig, 0.0)) for s in scores]
        for i, sh in zip(ids, _shares(vals)):
            idx[i] += SIGNAL_SHARE * w * sh

    order = sorted(ids, key=lambda i: -idx[i])
    out = {
        "ranking": [{"variant_id": i, "index": round(idx[i], 4)} for i in order],
        "winner_variant_id": order[0],
        "basis": "signals",  # networks + observable signals, not the legacy metrics
    }
    if len(order) >= 2:
        by = {s["variant_id"]: s for s in scores}
        w_s, r_s = by[order[0]], by[order[1]]
        na, sa, contrib = {}, {}, []
        # raw deltas (per component, for display) + weighted-share contribution (for `decisive`,
        # scale-invariant so a big-unit signal like clarity can't spuriously dominate).
        for net, w in metrics.NETWORK_WEIGHTS.items():
            wv = mean(w_s["networks"].get(net) or [0.0]); rv = mean(r_s["networks"].get(net) or [0.0])
            na[net] = round(wv - rv, 4)
            sw, sr = _share(wv, rv)
            contrib.append((f"brain:{net}", BRAIN_SHARE * w * (sw - sr)))
        wsig, rsig = w_s.get("signals") or {}, r_s.get("signals") or {}
        for sig, w in SIGNAL_WEIGHTS.items():
            wv = float(wsig.get(sig, 0.0)); rv = float(rsig.get(sig, 0.0))
            sa[sig] = round(wv - rv, 4)
            sw, sr = _share(wv, rv)
            contrib.append((f"signal:{sig}", SIGNAL_SHARE * w * (sw - sr)))
        out["network_advantage"] = na
        out["signal_advantage"] = sa
        out["decisive"] = max(contrib, key=lambda c: c[1])[0]
    return out
