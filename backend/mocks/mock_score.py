"""Canned ScoreObject matching CONTRACTS.md §3 — for A (Kimi) & C (Seb) to build against."""
import hashlib
import math

_W = {"default_mode": 0.30, "visual": 0.25, "language": 0.20, "auditory": 0.15, "motion": 0.10}
_REGION = {"visual": "fusiform_face_area", "auditory": "primary_auditory",
           "language": "broca_area", "motion": "motion_mt", "default_mode": "prefrontal_dmn"}


def _jitter(variant_id: str, salt: str, base: float, spread: float) -> float:
    """Deterministic per-variant nudge in [base-spread/2, base+spread/2], ≥0."""
    h = int(hashlib.sha256(f"{variant_id}:{salt}".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return max(0.0, base + spread * (h - 0.5))


def mock_score(variant_id: str = "var_demo0001", n: int = 18) -> dict:
    def curve(phase, amp):
        return [round(max(0.0, min(1.0, amp * (0.55 + 0.45 * math.sin(t / 2.0 + phase)))), 3)
                for t in range(n)]
    networks = {"visual": curve(0.0, 0.85), "auditory": curve(0.6, 0.6),
                "language": curve(1.1, 0.7), "motion": curve(1.7, 0.5),
                "default_mode": curve(0.3, 0.9)}
    eng = [round(sum(_W[k] * networks[k][t] for k in _W), 3) for t in range(n)]
    rt = [{"t": t, "top_network": max(networks, key=lambda k: networks[k][t]),
           "top_region": _REGION[max(networks, key=lambda k: networks[k][t])],
           "activation": round(max(networks[k][t] for k in networks), 3)} for t in range(n)]
    # signals (§3 family B) — varied per variant so mock-mode comparisons pick a real winner
    signals = {
        "face_expression": round(_jitter(variant_id, "face", 0.55, 0.4), 4),
        "speech_rate": round(_jitter(variant_id, "speech", 2.3, 1.0), 4),
        "volume": round(_jitter(variant_id, "vol", 0.5, 0.3), 5),
        "hand_gesture": round(_jitter(variant_id, "hand", 0.25, 0.2), 4),
        "motion": round(_jitter(variant_id, "motion", 0.06, 0.04), 4),
        "clarity": round(_jitter(variant_id, "clarity", 700, 300), 2),
    }
    return {"variant_id": variant_id, "networks": networks, "engagement": eng,
            "brain_frames": [f"media/{variant_id}_brain_{t:03d}.png" for t in range(n)],
            "region_timeline": rt, "signals": signals,
            "duration_sec": float(n), "sample_rate_hz": 1}
