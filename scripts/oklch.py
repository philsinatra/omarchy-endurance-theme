"""OKLCH <-> sRGB, WCAG contrast and OKLab distance. No dependencies."""
import math


def _f(x): return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4


def _g(x):
    x = max(0.0, min(1.0, x))
    return 12.92 * x if x <= 0.0031308 else 1.055 * (x ** (1 / 2.4)) - 0.055


def oklch_to_srgb(L, C, H):
    h = math.radians(H); a = C * math.cos(h); b = C * math.sin(h)
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return r, g, bb


def in_gamut(L, C, H, eps=1e-4):
    return all(-eps <= v <= 1 + eps for v in oklch_to_srgb(L, C, H))


def hexof(L, C, H):
    r, g, b = oklch_to_srgb(L, C, H)
    return "#%02x%02x%02x" % tuple(round(_g(v) * 255) for v in (r, g, b))


def srgb_to_oklab(hx):
    hx = hx.lstrip('#'); r, g, b = (_f(int(hx[i:i + 2], 16) / 255) for i in (0, 2, 4))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def srgb_to_oklch(hx):
    L, A, B = srgb_to_oklab(hx)
    return L, math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360


def delta_e(a, b):
    """Euclidean distance in OKLab. ~0.02 is a just-noticeable difference."""
    return math.dist(srgb_to_oklab(a), srgb_to_oklab(b))


def mix(a, b, t):
    """Blend hex a toward hex b by t (0..1), perceptually, in OKLab."""
    la, lb = srgb_to_oklab(a), srgb_to_oklab(b)
    L, A, B = (x + (y - x) * t for x, y in zip(la, lb))
    return hexof(L, math.hypot(A, B), math.degrees(math.atan2(B, A)))


def relLum(hx):
    hx = hx.lstrip('#'); r, g, b = (_f(int(hx[i:i + 2], 16) / 255) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def cr(a, b):
    l1, l2 = sorted((relLum(a), relLum(b)), reverse=True); return (l1 + 0.05) / (l2 + 0.05)
