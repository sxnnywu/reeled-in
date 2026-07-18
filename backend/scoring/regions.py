"""Vertices -> top region/network per second -> region_timeline. Owner: B.

PHASE 1: derive the timeline from the reduced 5-network series — per second,
the highest-activation network wins and maps to its representative region
(region list from CONTRACTS.md §2). PHASE 2 uses true per-region vertex masks
so top_region varies within a network (e.g. primary_visual vs fusiform_face_area).
"""

from backend.scoring.networks import reduce_to_networks

# Representative region per network (subset of CONTRACTS.md §2 region list).
NETWORK_TO_REGION = {
    "visual": "fusiform_face_area",
    "auditory": "primary_auditory",
    "language": "broca_area",
    "motion": "motion_mt",
    "default_mode": "prefrontal_dmn",
}


def region_timeline(vertex_timeseries) -> list:
    """-> [{t, top_network, top_region, activation}, ...], one entry per second.
    Per-clip normalized (legacy single-clip path). Batch scoring uses
    region_timeline_from_networks so activations sit on the test's shared scale."""
    return region_timeline_from_networks(reduce_to_networks(vertex_timeseries))


def region_timeline_from_networks(networks: dict) -> list:
    """Same timeline, but from already-normalized network curves (shared scale)."""
    names = list(networks.keys())
    n = len(next(iter(networks.values())))
    timeline = []
    for t in range(n):
        top_network = max(names, key=lambda k: networks[k][t])
        timeline.append(
            {
                "t": t,
                "top_network": top_network,
                "top_region": NETWORK_TO_REGION[top_network],
                "activation": round(float(networks[top_network][t]), 4),
            }
        )
    return timeline
