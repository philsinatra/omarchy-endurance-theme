#!/usr/bin/env python3
"""Tone-map an HDR render: bloom, filmic curve, deep-space grade, dark top edge, grain.

Usage: blackhole_post.py in.npy out.(png|jpg) [exposure=1.0 bloom=0.30 top=0.10 stars=0 ...]
Requires numpy and Pillow.
"""
import sys
import numpy as np
from PIL import Image

A = dict(exposure=1.0, bloom=0.30, bloom_r=0.012, bloom2=0.12, bloom2_r=0.06,
         top=0.10, vignette=0.35, grain=0.012, lift_r=0.018, lift_g=0.026, lift_b=0.040,
         stars=0.0, star_glow=0.0, star_r=1.1, out_w=0)


def blur(img, radius_px):
    """Gaussian blur (sigma = radius_px) of a float HDR image via FFT, edge-padded."""
    pad = int(3 * radius_px) + 1
    H, W, _ = img.shape
    p = np.pad(img, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
    fy = np.fft.fftfreq(p.shape[0])[:, None]
    fx = np.fft.rfftfreq(p.shape[1])[None, :]
    k = np.exp(-2 * (np.pi * radius_px) ** 2 * (fx ** 2 + fy ** 2)).astype(np.float32)
    out = np.empty_like(img)
    for c in range(3):
        out[..., c] = np.fft.irfft2(np.fft.rfft2(p[..., c]) * k, s=p.shape[:2])[pad:pad + H, pad:pad + W]
    return out


def filmic(x):
    # ACES approximation (Narkowicz)
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)


def to_srgb(x):
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(np.clip(x, 0, None), 1 / 2.4) - 0.055)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    a = dict(A)
    for kv in sys.argv[3:]:
        k, v = kv.split("="); a[k] = float(v)
    img = np.load(src).astype(np.float32)
    H, W, _ = img.shape
    img *= a["exposure"]
    if a["stars"] or a["star_glow"]:
        # Stars are the only point-like highlights on dark sky: a high-pass at a
        # few pixels isolates them, a wide blur tells sky from disk.
        lum = img.max(axis=2, keepdims=True)
        sky = np.clip(1 - blur(np.repeat(lum, 3, 2), 0.006 * W)[..., :1] / 0.04, 0, 1)
        pts = np.clip(img - blur(img, 2.5), 0, None) * sky
        img = img + a["stars"] * pts + a["star_glow"] * blur(pts, a["star_r"])
    bright = np.clip(img - 0.6, 0, None)
    img = img + a["bloom"] * blur(bright, a["bloom_r"] * W) + a["bloom2"] * blur(bright, a["bloom2_r"] * W)
    img = filmic(img)
    # deep-space lift: black point becomes the theme's void blue, not pure black
    lift = np.array([a["lift_r"], a["lift_g"], a["lift_b"]], dtype=np.float32) * 0.1
    img = lift + img * (1 - lift)
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, W, dtype=np.float32)[None, :]
    # radial vignette + guaranteed-dark top band for the status bar
    vig = 1 - a["vignette"] * np.clip((xx ** 2) * 0.6 + ((yy - 0.55) * 2) ** 2 * 0.5, 0, 1)
    topfade = np.clip(yy / max(a["top"], 1e-3), 0, 1) ** 1.2
    topfade = 0.35 + 0.65 * topfade if a["top"] > 0 else 1.0
    img = img * (vig * topfade)[..., None]
    out = to_srgb(img)
    rng = np.random.default_rng(3)
    out = out + rng.normal(0, a["grain"], out.shape).astype(np.float32)
    out = (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
    im = Image.fromarray(out)
    if a["out_w"]:
        w = int(a["out_w"]); im = im.resize((w, round(H * w / W)), Image.LANCZOS)
    if dst.endswith(".jpg"):
        im.save(dst, quality=94, subsampling=0, optimize=True, progressive=True)
    else:
        im.save(dst, optimize=True)
    lum = np.asarray(im.convert("L"), dtype=np.float32) / 255
    print(f"saved {dst} {im.size} mean {lum.mean()*100:.1f}% top8 {lum[:int(lum.shape[0]*0.08)].mean()*100:.1f}%")


if __name__ == "__main__":
    main()
