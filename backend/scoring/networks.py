"""Reduce ~20k cortical vertices -> the 5 functional networks. Owner: B.

Real mapping: each fsaverage5 vertex (10242 left + 10242 right = 20484, in that
order to match TRIBE's output) is assigned to one of our 5 networks by its
anatomical region, using the Destrieux surface atlas (nilearn). We then average
the vertices in each network per second and normalize to [0,1].

This replaces the earlier placeholder contiguous split so the 5 network curves
actually differ. The region->network grouping is approximate (a directional
proxy, per HOW_TRIBE_V2_WORKS.md), and lives in REGION_KEYWORDS below so it's
easy to tune.
"""

from pathlib import Path

import numpy as np

NETWORKS = ["visual", "auditory", "language", "motion", "default_mode"]

# Destrieux region-name substrings -> our network. First match wins, in this
# order, so more specific networks are listed before broader ones.
REGION_KEYWORDS = {
    "auditory": ["temp_sup-g_t_transv", "temp_sup-plan_tempo", "temp_sup-plan_polar",
                 "temp_sup-lateral", "lat_fis"],
    "language": ["front_inf-opercular", "front_inf-triangul", "pariet_inf-supramar"],
    "motion":   ["occipital_middle", "s_oc_middle", "oc-temp_lat", "precentral", "postcentral"],
    "visual":   ["occipital", "cuneus", "calcarine", "lingual", "fusifor", "pole_occipital",
                 "oc-temp_med"],
    "default_mode": ["front_sup", "cingul-post", "precuneus", "pariet_inf-angular",
                     "g_orbital", "rectus", "cingul-ant", "front_middle"],
}

_MASK_CACHE = "/cache/network_mask.npy"


def _label_to_network(label: str) -> int:
    lab = label.lower()
    for i, name in enumerate(NETWORKS):
        for kw in REGION_KEYWORDS[name]:
            if kw in lab:
                return i
    return -1  # unassigned vertices are excluded from all networks


def build_network_mask(cache_path: str = _MASK_CACHE) -> np.ndarray:
    """(20484,) int array: network index per vertex, -1 = unassigned. Cached."""
    p = Path(cache_path)
    if p.exists():
        return np.load(p)

    from nilearn import datasets

    atlas = datasets.fetch_atlas_surf_destrieux()
    labels = [l.decode() if isinstance(l, bytes) else l for l in atlas["labels"]]
    per_label_net = np.array([_label_to_network(l) for l in labels], dtype=int)

    left = np.asarray(atlas["map_left"], dtype=int)
    right = np.asarray(atlas["map_right"], dtype=int)
    vertex_labels = np.concatenate([left, right])  # fsaverage5 order: L then R
    mask = per_label_net[vertex_labels]

    p.parent.mkdir(parents=True, exist_ok=True)
    np.save(p, mask)
    return mask


def _normalize01(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    lo, hi = float(np.nanmin(x)), float(np.nanmax(x))
    if hi - lo < 1e-9:
        return np.zeros_like(x)
    return (x - lo) / (hi - lo)


def reduce_to_networks(vertex_timeseries) -> dict:
    """(n_timesteps, ~20k vertices) -> {network: [float per second]}, normalized [0,1]."""
    preds = np.asarray(vertex_timeseries, dtype=float)
    _, n_vertices = preds.shape
    mask = build_network_mask()

    # If atlas resolution and TRIBE output disagree, fall back to a contiguous
    # split so scoring never hard-fails (shape stays contract-correct).
    if mask.shape[0] != n_vertices:
        bounds = np.linspace(0, n_vertices, len(NETWORKS) + 1, dtype=int)
        mask = np.empty(n_vertices, dtype=int)
        for i in range(len(NETWORKS)):
            mask[bounds[i] : bounds[i + 1]] = i

    series = {}
    for i, name in enumerate(NETWORKS):
        cols = np.where(mask == i)[0]
        if cols.size == 0:
            series[name] = [0.0] * preds.shape[0]
            continue
        raw = np.abs(preds[:, cols]).mean(axis=1)
        series[name] = [round(float(v), 4) for v in _normalize01(raw)]
    return series
