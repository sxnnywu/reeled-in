# How TRIBE v2 Works

*Reference doc for the Reeled In team. Everything here is sourced (links at the bottom). Where a figure is specific to the earlier **TRIBE v1** (the Algonauts 2025 winner) vs the **v2** release, it's flagged, so we don't overstate precision.*

## What it is
TRIBE v2 is an open-source **brain encoding model** from Meta FAIR — Meta describes it as a "digital twin of human neural activity." Given a stimulus (video, audio, and/or text), it **predicts the fMRI brain response** a person would have to that stimulus across the whole cortex. It generalizes zero-shot to new subjects, languages, and tasks — you don't have to scan anyone.

**Lineage.** The original **TRIBE (Trimodal Brain Encoder)** won the **Algonauts 2025** brain-modeling competition — a ~1B-parameter model trained on just 4 subjects (arXiv 2507.22229). **TRIBE v2** (released 2026) is the scaled-up foundation-model version — Meta reports it was trained on **700+ volunteers** with a **~70× resolution increase** over comparable models — and it's the one open-sourced with weights, code, and a demo.

## The pipeline (how a video becomes a brain map)

**Stage 1 — Feature extraction: three frozen encoders, one per modality.** TRIBE doesn't process raw pixels/waveforms itself; it stands on three pretrained, **frozen** encoders:
- **Video → V-JEPA 2 (Giant):** processes 64-frame segments (~the preceding 4 seconds); video embeddings (dim ≈ 1280).
- **Audio → Wav2Vec-BERT 2.0:** audio representations resampled to ~2 Hz (dim ≈ 1024).
- **Text → LLaMA 3.2-3B:** contextualized word embeddings (up to ~1,024 words of context), mapped to ~2 Hz (dim ≈ 2048). Text with no audio is auto-converted to speech to recover word-level timings.

Because the encoders are frozen, TRIBE learns *on top of* their features — it doesn't retrain them.

**Stage 2 — Fusion: a Transformer over time.** Each modality is projected to a shared dimension (D = 384) and concatenated into a multimodal time series (D_model = 3 × 384 = 1152). A **Transformer encoder (~8 layers, ~8 heads)** attends over a long temporal window (~100 seconds) to model how the brain integrates the stream over time.

**Stage 3 — Brain mapping: project to cortical space.** A final linear projection maps the fused representation onto the **fsaverage5 cortical surface (~20,484 vertices)** (reporting also cites subcortical voxels), at **~1 Hz**. Output shape ≈ **(n_timesteps, ~20k vertices)** for an "average" subject.

## The five networks (this is what Reeled In actually uses)
Applying ICA to TRIBE's predictions recovers **five well-known functional networks**, so we can collapse the ~20k-vertex output into five interpretable channels:
- **Visual** — visual processing / imagery
- **Auditory** — sound, music, audio texture
- **Language** — speech / text comprehension
- **Motion** — visual motion / action
- **Default-mode** — internal / self-referential processing, meaning-making, narrative engagement

TRIBE also recovers classic functional landmarks (e.g. the **fusiform face area**, **Broca's area**) — evidence it's learned something brain-real, not arbitrary.

For Reeled In, each variant yields five time-series (one per network); our engagement / retention metrics are derived from these.

## Training & accuracy (know the limits)
- Trained on hundreds of hours of fMRI from naturalistic stimuli (the TRIBE paper reports **451.6 hours from 25 subjects across four naturalistic studies**; the v2 release scales subjects to 700+).
- Reported **group correlation (R_group) ≈ 0.4** on high-resolution HCP 7T data — ~a two-fold improvement over the median-subject baseline. Fine-tuning on **~1 hour** of a new subject's data gives a further **2–4×** improvement over linear models.
- **Temporal caveat:** fMRI BOLD is sluggish (hemodynamic lag ~4–6 s) and output is ~1 Hz → sub-2 s cut differences are smoothed.
- **Distribution caveat:** trained on long-form naturalistic media → short punchy Reels are directional, not gospel.

## How we call it
Minimal API (from the model card):
```python
from tribev2 import TribeModel

model = TribeModel.from_pretrained("facebook/tribev2", cache_folder="./cache")
df = model.get_events_dataframe(video_path="variant_A.mp4")   # or text_path= / audio_path=
preds, segments = model.predict(events=df)                    # preds: (n_timesteps, ~20k vertices)
```

## Runtime / hardware
- Full trimodal stack VRAM footprint ≈ **28–32 GB** → needs an **A100 40GB** (minimum). Rough split: LLaMA-3B ~7 GB + V-JEPA2-Giant ~14 GB + Wav2Vec-BERT ~1 GB + TRIBE.
- Audio-only or text-only fits a 24 GB **L4**, but loses the video branch (our core signal).
- **Gated dependency:** LLaMA 3.2-3B needs a HuggingFace token (accept the license) — required for any text/video run.
- Meta's demo caches inference for interactive use → per-run is seconds-scale on an A100. We precompute for the pitch.

## License
**CC BY-NC 4.0** — research / non-commercial. Fine for the hackathon; blocks a genuine "sell it" go-to-market (relevant to the Base44 track).

## What this means for Reeled In
- The "score a video" step is essentially **one API call on a GPU** — cheap and simple. Our engineering value is in **variant handling, the network-reduction + metric design, the comparison / winner logic, and the UX** — which is also what dodges the "just an API wrapper" judging penalty.
- We host the model once on **Modal** and **precompute**; the app never touches the GPU during the demo.

## Sources
- Meta AI blog — Introducing TRIBE v2: https://ai.meta.com/blog/tribe-v2-brain-predictive-foundation-model/
- TRIBE paper (arXiv 2507.22229): https://arxiv.org/abs/2507.22229
- Hugging Face model card (facebook/tribev2): https://huggingface.co/facebook/tribev2
- GitHub (facebookresearch/tribev2): https://github.com/facebookresearch/tribev2
- MarkTechPost technical breakdown: https://www.marktechpost.com/2026/03/26/meta-releases-tribe-v2-a-brain-encoding-model-that-predicts-fmri-responses-across-video-audio-and-text-stimuli/
- DataCamp tutorial (runtime / hardware): https://www.datacamp.com/tutorial/tribe-v2-tutorial
