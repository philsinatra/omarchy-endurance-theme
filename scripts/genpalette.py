#!/usr/bin/env python3
"""Endurance — regenerate ../colors.toml and ../neovim.lua from OKLCH constants.

One source, two outputs. Edit the constants below, run this, then
`omarchy theme set endurance`.

The construction:
  * Surfaces are deep space: one cool hue (258deg) at very low chroma,
    rising in lightness only. Nothing in the chassis competes with code.
  * Syntax is a thermal spectrum. Warm hues (amber, ember) are the hot
    accretion-disk side and carry *language*: keywords and literals.
    Cool hues (ice, glacier, lichen) are the blueshifted side and carry
    *names*: functions, types, strings.
  * Every syntax hue lives in one lightness band (L 0.75-0.82) and one
    chroma band (C 0.075-0.12), so no token outshouts another.
  * Red is held above the band (C 0.15) and reserved for errors.
The generator refuses to write if any colour leaves sRGB, if body text
drops under 11:1, comments under 4.8:1, or any two syntax roles fall
closer than dE 0.08 in OKLab (the "can a beginner tell them apart" test).
"""
import os, sys, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oklch import hexof, in_gamut, cr, delta_e, mix, srgb_to_oklch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, os.pardir))

SPACE_H = 258.0   # the void: cool blue-black
TEXT_H = 245.0    # moonlight: text is cool, never pure grey

# Surfaces — (L, C). Same hue, rising lightness.
SURFACES = {
    "darker_background":  (0.140, 0.012),   # void — tab fill, deepest wells
    "dark_background":    (0.170, 0.013),   # panels, floats, statusline
    "background":         (0.198, 0.014),   # the editor
    "lighter_background": (0.240, 0.016),   # raised strips
}
SELECTION = (0.330, 0.050, 252.0)           # cockpit glass: cool, obvious

# Text — (L, C) on TEXT_H.
TEXT = {
    "muted":             (0.520, 0.020),    # line numbers, disabled
    "dark_foreground":   (0.655, 0.028),    # comments
    "light_foreground":  (0.790, 0.016),
    "foreground":        (0.885, 0.012),    # body text
    "bright_foreground": (0.960, 0.008),
}

# Syntax — (L, C, H). The thermal spectrum.
SPECTRUM = {
    "red":     (0.705, 0.150, 25.0),    # signal: errors only
    "orange":  (0.770, 0.115, 50.0),    # ember: numbers, constants, literals
    "yellow":  (0.825, 0.118, 80.0),    # accretion amber: keywords, accent
    "green":   (0.790, 0.095, 140.0),   # lichen: strings
    "cyan":    (0.820, 0.076, 199.0),   # glacier: types
    "blue":    (0.765, 0.098, 250.0),   # blueshift: functions
    "magenta": (0.755, 0.090, 305.0),   # nebula: macros, builtins, specials
}
BRIGHT_DL, BRIGHT_DC = 0.075, -0.012
BROWN = (0.585, 0.060, 60.0)

# Neovim-only roles, derived — (L, C, H).
EXTRA = {
    "param":    (0.840, 0.052, 60.0),   # sand: parameters, attributes
    "prop":     (0.840, 0.058, 235.0),  # frost: fields and properties
    "operator": (0.770, 0.050, 80.0),   # amber at low power
    "punct":    (0.600, 0.022, TEXT_H), # brackets recede
    "rule":     (0.355, 0.022, SPACE_H),# borders, separators
    "guide":    (0.270, 0.016, SPACE_H),# indent guides
    "guide_hi": (0.430, 0.030, SPACE_H),# active scope
    "linenr":   (0.440, 0.020, TEXT_H),
    "cursorline": (0.228, 0.016, SPACE_H),
    "inlay":    (0.580, 0.030, TEXT_H),
}

ORDER = ["red", "orange", "yellow", "green", "cyan", "blue", "magenta"]


def build():
    p = {k: hexof(L, C, SPACE_H) for k, (L, C) in SURFACES.items()}
    p.update({k: hexof(L, C, TEXT_H) for k, (L, C) in TEXT.items()})
    p["selection"] = hexof(*SELECTION)
    for k, (L, C, H) in SPECTRUM.items():
        p[k] = hexof(L, C, H)
        p["bright_" + k] = hexof(L + BRIGHT_DL, C + BRIGHT_DC, H)
    p["brown"] = hexof(*BROWN)
    p["accent"] = p["yellow"]
    p["cursor"] = p["yellow"]
    p["selection_foreground"] = p["bright_foreground"]
    p["selection_background"] = p["selection"]
    x = {k: hexof(*v) for k, v in EXTRA.items()}
    bg = p["background"]
    x["search"] = mix(bg, p["yellow"], 0.28)
    x["match"] = mix(bg, p["yellow"], 0.16)
    x["ref"] = mix(bg, p["blue"], 0.16)
    x["inlay_bg"] = mix(bg, p["blue"], 0.07)
    x["docstring"] = mix(p["dark_foreground"], p["green"], 0.45)
    for k in ("red", "yellow", "blue", "cyan", "green"):
        x[k + "_wash"] = mix(bg, p[k], 0.11)
    x["diff_add"] = mix(bg, p["green"], 0.16)
    x["diff_del"] = mix(bg, p["red"], 0.16)
    x["diff_chg"] = mix(bg, p["blue"], 0.12)
    x["diff_txt"] = mix(bg, p["blue"], 0.30)
    return p, x


# Primary roles must sit >= 0.08 apart in OKLab. Secondary roles are
# deliberate tints of plain text and only need to be visibly distinct.
PRIMARY = {"keyword": "yellow", "number": "orange", "string": "green", "type": "cyan",
           "function": "blue", "special": "magenta", "error": "red", "variable": "foreground"}
SECONDARY = {"parameter": "param", "property": "prop"}
MIN_PRIMARY, MIN_SECONDARY = 0.080, 0.045


def report(p, x):
    allc = {**p, **x}
    bad = [k for k, v in allc.items() if not in_gamut(*srgb_to_oklch(v))]
    bg = p["background"]
    sy = {k: cr(p[k], bg) for k in ORDER}
    prim = {r: allc[k] for r, k in PRIMARY.items()}
    roles = {**prim, **{r: allc[k] for r, k in SECONDARY.items()}}
    pairs = sorted((delta_e(prim[a], prim[b]), a, b)
                   for a, b in itertools.combinations(prim, 2))
    sec = sorted((delta_e(roles[s], roles[o]), s, o)
                 for s in SECONDARY for o in roles if o != s)
    body, cmt = cr(p["foreground"], bg), cr(p["dark_foreground"], bg)
    print(f"out of gamut        : {bad or 'none'}")
    print(f"background          : {bg}")
    print(f"body text           : {body:.2f}:1")
    print(f"comments            : {cmt:.2f}:1")
    for k in ORDER:
        print(f"  {k:<8} {p[k]}  {sy[k]:5.2f}:1   bright {p['bright_' + k]}")
    for k in ("param", "prop", "operator", "punct", "linenr", "inlay"):
        print(f"  {k:<8} {x[k]}  {cr(x[k], bg):5.2f}:1")
    print("closest primary     : " + ", ".join(f"{a}/{b} {d:.3f}" for d, a, b in pairs[:3]))
    print("closest secondary   : " + ", ".join(f"{a}/{b} {d:.3f}" for d, a, b in sec[:3]))
    ok = (not bad and body >= 11 and cmt >= 4.8
          and pairs[0][0] >= MIN_PRIMARY and sec[0][0] >= MIN_SECONDARY)
    return ok, dict(body=body, cmt=cmt, sy=sy, min_de=pairs[0])


def emit_colors(p, r):
    g = lambda *ks: "\n".join(f'{k} = "{p[k]}"' for k in ks)
    lo, hi = min(r["sy"].values()), max(r["sy"].values())
    a, b = p["yellow"].lstrip("#"), p["blue"].lstrip("#")
    rule = hexof(*EXTRA["rule"]).lstrip("#")
    return f'''# Endurance — Omarchy theme palette
#
# GENERATED by scripts/genpalette.py — do not hand-edit.
#
# Deep-space surfaces at hue {SPACE_H:.0f}deg, near-zero chroma.
# Syntax is a thermal spectrum: warm = language (keywords, literals),
# cool = names (functions, types, strings). Red is reserved for errors.
#
# Measured against background {p["background"]}:
#   body text    {r["body"]:.1f}:1
#   syntax band  {lo:.1f} - {hi:.1f}:1
#   comments     {r["cmt"]:.1f}:1
#   closest pair {r["min_de"][1]}/{r["min_de"][2]} dE {r["min_de"][0]:.3f} (OKLab)

mode = "dark"

# Accretion amber. Borders, focus, cursor, bar accents.
{g("accent", "cursor", "selection", "muted")}

# Deep space — one hue, rising lightness.
{g("background", "dark_background", "darker_background", "lighter_background")}

# Moonlight text ramp.
{g("foreground", "dark_foreground", "light_foreground", "bright_foreground")}

# Thermal spectrum.
{g("red", "orange", "yellow", "green", "cyan", "blue", "magenta", "brown")}

{g(*["bright_" + k for k in ORDER])}

{g("selection_foreground", "selection_background")}

# Window borders: amber redshifting to blue — the Doppler gradient.
hyprland_active_border = "rgba({a}ee) rgba({b}ee) 45deg"
hyprland_inactive_border = "rgba({rule}aa)"
'''


def emit_neovim(p, x):
    P = {
        "void": p["darker_background"], "panel": p["dark_background"], "bg": p["background"],
        "panel_hi": p["lighter_background"], "selection": p["selection"],
        "muted": p["muted"], "comment": p["dark_foreground"], "fg_dim": p["light_foreground"],
        "fg": p["foreground"], "fg_bright": p["bright_foreground"],
        "amber": p["yellow"], "amber_bright": p["bright_yellow"], "orange": p["orange"],
        "red": p["red"], "red_bright": p["bright_red"], "green": p["green"],
        "cyan": p["cyan"], "blue": p["blue"], "blue_bright": p["bright_blue"],
        "magenta": p["magenta"], **x,
    }
    width = max(map(len, P))
    ptable = "\n".join(f'  {k:<{width}} = "{v}",' for k, v in P.items())
    aether = "\n".join(
        f'        {k} = "{v}",' for k, v in [
            ("bg", p["background"]), ("dark_bg", p["dark_background"]),
            ("darker_bg", p["darker_background"]), ("lighter_bg", p["lighter_background"]),
            ("fg", p["foreground"]), ("dark_fg", p["dark_foreground"]),
            ("light_fg", p["light_foreground"]), ("bright_fg", p["bright_foreground"]),
            ("muted", p["muted"]),
            *[(k, p[k]) for k in ORDER], ("brown", p["brown"]),
            *[("bright_" + k, p["bright_" + k]) for k in ORDER if k != "orange"],
            ("accent", p["accent"]), ("cursor", p["cursor"]),
            ("foreground", p["foreground"]), ("background", p["background"]),
            ("selection", p["selection"]),
            ("selection_foreground", p["selection_foreground"]),
            ("selection_background", p["selection_background"]),
        ])
    with open(os.path.join(HERE, "neovim.lua.in")) as f:
        tpl = f.read()
    return tpl.replace("--@PALETTE@", ptable).replace("--@AETHER@", aether)


BTOP_TPL = "/usr/share/omarchy/default/themed/btop.theme.tpl"


def emit_btop(p):
    """Omarchy's btop template, with red kept for real alarms (temperature)
    instead of decorating the network box and ordinary graph peaks."""
    import re
    if not os.path.exists(BTOP_TPL):
        return None
    t = re.sub(r"\{\{\s*([a-z_]+)\s*\}\}", lambda m: p.get(m.group(1), m.group(0)), open(BTOP_TPL).read())
    t = t.replace(f'theme[net_box]="{p["red"]}"', f'theme[net_box]="{p["blue"]}"')
    t = re.sub(r'^(theme\[(?:available|download)_(?:mid|end)\]=)"' + p["red"] + '"',
               lambda m: m.group(1) + '"' + p["orange"] + '"', t, flags=re.M)
    return "# Endurance btop theme — GENERATED by scripts/genpalette.py from Omarchy's template.\n" \
           "# Red is kept for alarms only.\n" + t


if __name__ == "__main__":
    p, x = build()
    ok, r = report(p, x)
    if not ok:
        sys.exit("\nrefusing to write: a constraint above failed")
    outputs = [("colors.toml", emit_colors(p, r)), ("neovim.lua", emit_neovim(p, x)), ("btop.theme", emit_btop(p))]
    for name, text in outputs:
        if text is None:
            print(f"skipped {name} (template not found)")
            continue
        with open(os.path.join(ROOT, name), "w") as f:
            f.write(text)
        print(f"wrote {name}")
