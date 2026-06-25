#!/usr/bin/env python3
"""Single image -> layered 3D scene with inpainted occlusions.

Estimates depth (Depth Anything V2), splits the photo into depth layers,
inpaints what each layer hides from the layers behind it (LaMa), and writes
a scene folder that trial-layers.html can render with real parallax fill.

usage: .venv/bin/python inpaint.py input.png [-o out_dir] [-k 3]
deps:  pip install torch transformers pillow numpy opencv-python-headless simple-lama-inpainting

models are loaded from ./models/ (offline). pre-download with:
    .venv/bin/python -m huggingface_hub.commands.huggingface_cli download \
        depth-anything/Depth-Anything-V2-Small-hf \
        --local-dir models/depth-anything-v2-small
    curl -L -o models/big-lama.pt \
        https://github.com/advimman/lama/releases/download/v1.0/big-lama.pt
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def kmeans_depth(depth, void, k):
    """Cluster depth values into k layers, labelled 0 (far) .. k-1 (near)."""
    vals = depth[~void].reshape(-1, 1).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-3)
    _, labels, centers = cv2.kmeans(vals, k, None, crit, 5, cv2.KMEANS_PP_CENTERS)
    order = np.argsort(centers.ravel())          # ascending = far .. near
    remap = np.empty(k, dtype=np.int32)
    remap[order] = np.arange(k)
    cluster = np.zeros(depth.shape, dtype=np.int32)
    cluster[~void] = remap[labels.ravel()]
    return cluster


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--out", help="output scene folder (default <input>_scene)")
    ap.add_argument("-k", "--layers", type=int, default=3)
    ap.add_argument("--max-side", type=int, default=1280)
    ap.add_argument("--ignore-alpha", action="store_true",
                    help="treat the image as fully opaque (use RGB under transparent areas)")
    args = ap.parse_args()

    src = Path(args.input)
    out = Path(args.out) if args.out else src.parent / f"{src.stem}_scene"
    out.mkdir(parents=True, exist_ok=True)

    pil = Image.open(src).convert("RGBA")
    scale = min(1.0, args.max_side / max(pil.size))
    size = (round(pil.width * scale), round(pil.height * scale))
    # resize RGB and alpha separately: PIL premultiplies alpha when resizing
    # RGBA, which blacks out the colour data under transparent pixels
    rgb = np.asarray(pil.convert("RGB").resize(size, Image.LANCZOS)).copy()
    alpha8 = np.asarray(pil.getchannel("A").resize(size, Image.LANCZOS))
    void = (alpha8 < 128) if not args.ignore_alpha \
        else np.zeros(rgb.shape[:2], dtype=bool)  # pixels that don't exist (cutout images)
    H, W = rgb.shape[:2]

    model_dir = Path(__file__).parent / "models" / "depth-anything-v2-small"
    lama_path = Path(__file__).parent / "models" / "big-lama.pt"
    if not model_dir.is_dir() or not lama_path.is_file():
        sys.exit(
            f"missing local models under {Path(__file__).parent / 'models'}/ — "
            "see download command in the header comment of this file"
        )

    print("estimating depth (Depth Anything V2 small, local)…")
    from transformers import pipeline
    depth_pil = pipeline("depth-estimation", model=str(model_dir),
                         local_files_only=True)(Image.fromarray(rgb))["depth"]
    depth = np.asarray(depth_pil.resize((W, H))).astype(np.float32) / 255.0  # 1 = near

    print(f"splitting into {args.layers} depth layers…")
    cluster = kmeans_depth(depth, void, args.layers)

    print("loading LaMa inpainting model (local)…")
    import torch
    # simple-lama-inpainting downloads to its cache if no env path; we point it
    # at our local file so it doesn't try the dead upstream URL on first run
    import os
    os.environ["LAMA_MODEL"] = str(lama_path)
    # big-lama.pt was traced on CUDA; without map_location it fails to load on Mac
    _jit_load = torch.jit.load
    torch.jit.load = lambda f, *a, **kw: _jit_load(f, map_location="cpu")
    from simple_lama_inpainting import SimpleLama
    lama = SimpleLama(device=torch.device("cpu"))

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))
    # median-smooth depth: silhouette noise otherwise serrates the displaced mesh
    depth8 = cv2.medianBlur((depth * 255).astype(np.uint8), 5)
    layers_meta = []

    for i in range(args.layers):
        holes = np.zeros((H, W), dtype=bool)
        if i == 0:
            alpha = np.where(void, 0, 255).astype(np.uint8)
        else:
            # cover own cluster AND everything nearer: when a nearer layer peels
            # away in parallax, this layer's inpainted fill is what shows behind
            own = ((cluster >= i) & ~void).astype(np.uint8) * 255
            # drop tiny disconnected islands (depth noise) that float as debris
            n_cc, cc, stats, _ = cv2.connectedComponentsWithStats(own)
            for c in range(1, n_cc):
                if stats[c, cv2.CC_STAT_AREA] < W * H * 5e-4:
                    own[cc == c] = 0
            alpha = cv2.dilate(own, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
            # snap the blunt cluster mask to real image edges (hair, silhouettes)
            alpha = cv2.ximgproc.guidedFilter(rgb, alpha, radius=6, eps=1e-4 * 255 * 255)
            alpha[void] = 0
            # fill small enclosed background pockets in the final mask (sky gaps
            # between hair tufts, glasses see-through): real in the photo, but
            # they render as ugly bright tunnels once the layer is displaced
            n_h, hc, hstats, _ = cv2.connectedComponentsWithStats((alpha < 128).astype(np.uint8))
            for c in range(1, n_h):
                x, y, ww, hh, area = hstats[c]
                if x > 0 and y > 0 and x + ww < W and y + hh < H and area < W * H * 0.005:
                    alpha[hc == c] = 255
                    holes |= hc == c

        # inpaint what this layer hides from layers behind it, plus the filled
        # pockets (their photo pixels are background seen through the gap — they
        # must become this layer's content or they read as holes when displaced)
        nearer = ((cluster > i) & ~void).astype(np.uint8) * 255
        img_i = rgb
        if nearer.any() or holes.any():
            # dilate so LaMa can't sample colours from the object being removed
            mask = cv2.dilate(nearer, kernel)
            mask |= cv2.dilate(holes.astype(np.uint8) * 255,
                               cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
            mask[void] = 0
            print(f"layer {i}: inpainting {mask.astype(bool).mean():.0%} of the image…")
            img_i = np.asarray(lama(Image.fromarray(rgb), Image.fromarray(mask)))[:H, :W]

        # per-layer depth: keep only this layer's own depth and extend it
        # smoothly under everything else — silhouettes are handled by alpha,
        # so the depth map must never contain a cliff to another layer's depth
        # (the gap-cut shader would tear the mesh open there)
        dmask = ((cluster != i) | void | holes) if i > 0 else (cluster > 0) | void
        d_i = cv2.inpaint(depth8, cv2.dilate(dmask.astype(np.uint8) * 255, kernel), 3,
                          cv2.INPAINT_TELEA) if dmask.any() else depth8.copy()
        if i > 0:
            # lift far-depth dips onto the subject surface: glasses lenses and
            # hair gaps read as "background" to the depth model and would tear
            # off the face when displaced; enclosed dips smaller than the
            # kernel are such errors, while real recesses are larger and stay
            closed = cv2.morphologyEx(d_i, cv2.MORPH_CLOSE,
                                      cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (71, 71)))
            sub = alpha > 64
            d_i[sub] = closed[sub]

        Image.fromarray(np.dstack([img_i, alpha])).save(out / f"layer{i}.png")
        Image.fromarray(d_i).save(out / f"depth{i}.png")
        own = (cluster == i) & ~void
        layers_meta.append({"image": f"layer{i}.png", "depth": f"depth{i}.png",
                            "mid": float(depth[own].mean()) if own.any() else 0.5})

    meta = {
        "width": W,
        "height": H,
        "mid": float(depth[~void].mean()) if (~void).any() else 0.5,
        "layers": layers_meta,
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"scene written to {out}/ — open trial-layers.html?scene={out.name}")


if __name__ == "__main__":
    main()
