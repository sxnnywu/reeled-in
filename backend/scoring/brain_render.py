"""Render per-second brain PNGs (nilearn) -> brain_frames. Owner: B.

Turns TRIBE's per-second cortical predictions into a flipbook of brain images
that light up where activity is highest. This is the VISUAL half of the
brain-region bridge: A (frontend) plays these frames synced to the video, next
to the region_timeline data. B produces the pictures; A animates them.

fsaverage5 = 10242 left + 10242 right vertices (left first, matching TRIBE).
We render the left hemisphere lateral view (covers visual/motion occipital,
language frontal, auditory temporal). Model files cache to /cache.
"""

import os

import numpy as np


def render_frames(vertex_timeseries, variant_id: str, cache_dir: str = "/cache", sub: int = 1) -> list:
    """sub>1 interpolates `sub` frames per second for a smoother flipbook.
    NOTE: the brain model is 1 Hz, so interpolated frames are blended
    in-betweens, not new measurements. sub=1 keeps brain_frames aligned 1:1 with
    the network arrays (CONTRACTS §3); sub>1 desyncs that length, so prefer
    letting the frontend cross-fade the sub=1 frames instead."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from nilearn import datasets, plotting

    fs = datasets.fetch_surf_fsaverage("fsaverage5", data_dir=f"{cache_dir}/nilearn")
    preds = np.asarray(vertex_timeseries, dtype=float)
    if sub > 1 and preds.shape[0] > 1:
        n0 = preds.shape[0]
        new_x = np.linspace(0, n0 - 1, (n0 - 1) * sub + 1)
        lo = np.floor(new_x).astype(int)
        hi = np.clip(lo + 1, 0, n0 - 1)
        w = (new_x - lo)[:, None]
        preds = preds[lo] * (1 - w) + preds[hi] * w
    n = preds.shape[0]
    out_dir = f"{cache_dir}/media"
    os.makedirs(out_dir, exist_ok=True)

    vmax = float(np.abs(preds[:, :10242]).max()) or 1.0
    keys = []
    for t in range(n):
        lh = np.abs(preds[t, :10242])
        fig = plotting.plot_surf_stat_map(
            fs["infl_left"],
            lh,
            hemi="left",
            view="lateral",
            bg_map=fs.get("sulc_left"),
            colorbar=False,
            vmax=vmax,
            cmap="inferno",
            threshold=vmax * 0.15,
        )
        fname = f"{variant_id}_brain_{t:03d}.png"
        fig.savefig(f"{out_dir}/{fname}", dpi=60, bbox_inches="tight")
        plt.close(fig)
        keys.append(f"media/{fname}")
    return keys
