#!/usr/bin/env python3
"""Render backgrounds/2-event-horizon.webp (lossless) — the theme's own gradient.

Deep space falling from the void at the top edge to a blue-black floor,
with amber light blooming from the bottom-right corner: something vast and
hot, just out of frame. The base ramp is blended in OKLab so it stays
perceptually even; light is added in linear RGB so the amber lights the blue
instead of greying it; the result is dithered so it never bands.

Requires numpy and Pillow.  Usage: gradient.py [WIDTH HEIGHT]
"""
import os, sys, math
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oklch import srgb_to_oklab

W, H = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (3840, 2160)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "backgrounds", "2-event-horizon.webp")

VOID = "#04070c"    # top edge, darker than darker_background
SPACE = "#0c121a"   # mid-field
DEEP = "#121a26"    # lower field, a touch more blue than the editor
# light sources, linear RGB, added on top (light adds; it never greys the blue)
EMBER = np.array([1.00, 0.34, 0.05])   # accretion amber
GOLD = np.array([1.00, 0.62, 0.22])    # hot core of the horizon
ICE = np.array([0.20, 0.36, 0.70])     # cool scatter above the glow


def lab(hx):
    return np.array(srgb_to_oklab(hx), dtype=np.float64)


def oklab_to_srgb(L, a, b):
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    rgb = np.clip(np.stack([r, g, bb], -1), 0, 1)
    return np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - 0.055)


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


y = np.linspace(0, 1, H)[:, None]
x = np.linspace(0, 1, W)[None, :]
aspect = W / H

# base: void -> space -> deep, top to bottom, with a slight diagonal lean
t = np.clip(0.80 * y + 0.20 * x, 0, 1)
base = (lab(VOID)[None, None] * (1 - smooth(t / 0.55))[..., None]
        + lab(SPACE)[None, None] * (smooth(t / 0.55) * (1 - smooth((t - 0.55) / 0.45)))[..., None]
        + lab(DEEP)[None, None] * smooth((t - 0.55) / 0.45)[..., None])

rgb = oklab_to_srgb(base[..., 0], base[..., 1], base[..., 2])
lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)

# warm bloom tucked into the bottom-right corner, tight so it never muddies
# the blue: light from something vast and hot just out of frame
cx, cy = 1.02, 1.10
R = np.sqrt(((x - cx) * aspect) ** 2 + (y - cy) ** 2)
bloom = np.exp(-(R / 0.46) ** 2)
core = np.exp(-(R / 0.20) ** 2)
# cool scatter across the lower-left, the blueshifted side
haze = np.exp(-(((x - 0.18) * aspect) / 1.3) ** 2 - ((y - 0.95) / 0.45) ** 2)

# the warm light sits on black, not on blue: blue + amber would read as grey
lin = lin * (1 - 0.85 * np.exp(-(R / 0.62) ** 2))[..., None]
lin = (lin + EMBER * (0.085 * bloom)[..., None] + GOLD * (0.30 * core ** 1.6)[..., None]
       + ICE * (0.010 * haze)[..., None])
rgb = np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * np.clip(lin, 0, None) ** (1 / 2.4) - 0.055)

# dither: triangular noise at +-1 LSB, so 8-bit output never bands
rng = np.random.default_rng(2014)
noise = (rng.random(rgb.shape) - rng.random(rgb.shape)) / 255.0
img = np.clip(np.round((rgb + noise) * 255), 0, 255).astype(np.uint8)

Image.fromarray(img).save(os.path.normpath(OUT), lossless=True, method=6, exact=True)
lum = img.mean(axis=2) / 255
print(f"wrote {os.path.normpath(OUT)} {W}x{H}  mean {lum.mean()*100:.1f}%  top8 {lum[:int(H*0.08)].mean()*100:.1f}%")
