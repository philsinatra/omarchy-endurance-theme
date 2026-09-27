#!/usr/bin/env python3
"""Endurance — regenerate ../colors.toml and ../btop.theme from OKLCH constants.

Edit the constants below, run this, then `omarchy theme set endurance`.

Endurance ships no Lua: Omarchy generates Neovim, VS Code, Helix, terminals,
Chromium and the rest from colors.toml, so a `git clone` install gets the
whole theme. The palette is therefore designed for the role each key plays
in those templates (aether.nvim and the VS Code template agree):

  bright_magenta  keywords          nebula violet — the language itself
  yellow          types, accent     accretion amber
  orange          numbers           ember
  bright_yellow   constants         starlight gold
  blue            functions         blueshift
  cyan            parameters        glacier
  bright_cyan     properties        frost
  green           strings           lichen
  bright_red      errors            the only signal colour
  muted           comments          readable in a lecture hall

The construction:
  * Surfaces are deep space: one cool hue (258deg) at very low chroma,
    rising in lightness only. Nothing in the chassis competes with code.
  * Warm hues (amber, ember, gold) carry what things *are* — types and
    literal values. Cool hues carry what things *do* and are *called* —
    functions, parameters, properties. Keywords sit apart in violet.
  * Syntax hues share one lightness band (L 0.76-0.90) and one chroma band.
The generator refuses to write if any colour leaves sRGB, if body text drops
under 11:1 or comments under 4.8:1, or if any two syntax roles a student must
tell apart fall closer than dE 0.07 in OKLab.
"""
import os, sys, re, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oklch import hexof, in_gamut, cr, delta_e, srgb_to_oklch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, os.pardir))

SPACE_H = 258.0   # the void: cool blue-black
TEXT_H = 245.0    # moonlight: text is cool, never pure grey

# Surfaces — (L, C). Same hue, rising lightness.
SURFACES = {
    "darker_background":  (0.140, 0.012),
    "dark_background":    (0.170, 0.013),
    "background":         (0.198, 0.014),
    "lighter_background": (0.240, 0.016),
}
SELECTION = (0.330, 0.050, 252.0)           # cockpit glass: cool, obvious
RULE = (0.355, 0.022, SPACE_H)              # inactive window border

# Text — (L, C) on TEXT_H.
TEXT = {
    "muted":             (0.640, 0.026),    # comments, line numbers
    "dark_foreground":   (0.720, 0.020),
    "light_foreground":  (0.800, 0.016),
    "foreground":        (0.885, 0.012),    # body text
    "bright_foreground": (0.960, 0.008),
}

# Syntax — (L, C, H), keyed by the palette slot the templates read.
SYNTAX = {
    "red":            (0.705, 0.150, 25.0),
    "bright_red":     (0.725, 0.170, 20.0),   # errors
    "orange":         (0.770, 0.115, 50.0),   # numbers
    "bright_orange":  (0.845, 0.100, 50.0),
    "yellow":         (0.825, 0.118, 80.0),   # types, accent
    "bright_yellow":  (0.905, 0.075, 95.0),   # constants
    "green":          (0.790, 0.095, 140.0),  # strings
    "bright_green":   (0.865, 0.083, 140.0),
    "cyan":           (0.820, 0.076, 195.0),  # parameters
    "bright_cyan":    (0.840, 0.080, 255.0),  # properties
    "blue":           (0.765, 0.098, 250.0),  # functions
    "bright_blue":    (0.840, 0.086, 250.0),
    "magenta":        (0.720, 0.090, 305.0),
    "bright_magenta": (0.780, 0.110, 302.0),  # keywords
}
BROWN = (0.585, 0.060, 60.0)

ORDER = ["red", "orange", "yellow", "green", "cyan", "blue", "magenta"]

# Roles a reader must tell apart, as the stock templates assign them.
ROLES = {
    "keyword": "bright_magenta", "type": "yellow", "function": "blue",
    "string": "green", "number": "orange", "constant": "bright_yellow",
    "parameter": "cyan", "property": "bright_cyan", "error": "bright_red",
    "variable": "foreground",
}
MIN_DE = 0.070


def build():
    p = {k: hexof(L, C, SPACE_H) for k, (L, C) in SURFACES.items()}
    p.update({k: hexof(L, C, TEXT_H) for k, (L, C) in TEXT.items()})
    p["selection"] = hexof(*SELECTION)
    p.update({k: hexof(*v) for k, v in SYNTAX.items()})
    p["brown"] = hexof(*BROWN)
    p["accent"] = p["yellow"]
    p["cursor"] = p["yellow"]
    p["selection_foreground"] = p["bright_foreground"]
    p["selection_background"] = p["selection"]
    p["rule"] = hexof(*RULE)
    return p


def report(p):
    bad = [k for k, v in p.items() if not in_gamut(*srgb_to_oklch(v))]
    bg = p["background"]
    roles = {r: p[k] for r, k in ROLES.items()}
    pairs = sorted((delta_e(roles[a], roles[b]), a, b)
                   for a, b in itertools.combinations(roles, 2))
    body, cmt = cr(p["foreground"], bg), cr(p["muted"], bg)
    print(f"out of gamut   : {bad or 'none'}")
    print(f"background     : {bg}")
    print(f"body text      : {body:.2f}:1")
    print(f"comments       : {cmt:.2f}:1")
    for r, k in ROLES.items():
        print(f"  {r:<10} {k:<15} {p[k]}  {cr(p[k], bg):5.2f}:1")
    print("closest roles  : " + ", ".join(f"{a}/{b} {d:.3f}" for d, a, b in pairs[:4]))
    ok = not bad and body >= 11 and cmt >= 4.8 and pairs[0][0] >= MIN_DE
    return ok, dict(body=body, cmt=cmt, pairs=pairs)


def emit_colors(p, r):
    g = lambda *ks: "\n".join(f'{k} = "{p[k]}"' for k in ks)
    d, a, b = r["pairs"][0]
    amber, blue, rule = p["yellow"][1:], p["blue"][1:], p["rule"][1:]
    return f'''# Endurance — Omarchy theme palette
#
# GENERATED by scripts/genpalette.py — do not hand-edit.
#
# Deep-space surfaces at hue {SPACE_H:.0f}deg, near-zero chroma. Each syntax
# slot is chosen for the role Omarchy's templates give it (Neovim, VS Code):
#   bright_magenta keywords · yellow types · orange numbers · bright_yellow
#   constants · blue functions · cyan parameters · bright_cyan properties ·
#   green strings · bright_red errors · muted comments
#
# Measured against background {p["background"]}:
#   body text    {r["body"]:.1f}:1
#   comments     {r["cmt"]:.1f}:1
#   closest pair {a}/{b} dE {d:.3f} (OKLab)

mode = "dark"

# Accretion amber. Borders, focus, cursor, bar accents.
{g("accent", "cursor", "selection", "muted")}

# Deep space — one hue, rising lightness.
{g("background", "dark_background", "darker_background", "lighter_background")}

# Moonlight text ramp.
{g("foreground", "dark_foreground", "light_foreground", "bright_foreground")}

{g(*ORDER, "brown")}

{g(*["bright_" + k for k in ORDER])}

{g("selection_foreground", "selection_background")}

# Window borders: amber redshifting to blue — the Doppler gradient.
hyprland_active_border = "rgba({amber}ee) rgba({blue}ee) 45deg"
hyprland_inactive_border = "rgba({rule}aa)"
'''


BTOP_TPL = "/usr/share/omarchy/default/themed/btop.theme.tpl"


def emit_btop(p):
    """Omarchy's btop template, with red kept for real alarms (temperature)
    instead of decorating the network box and ordinary graph peaks."""
    if not os.path.exists(BTOP_TPL):
        return None
    t = re.sub(r"\{\{\s*([a-z_]+)\s*\}\}", lambda m: p.get(m.group(1), m.group(0)), open(BTOP_TPL).read())
    t = t.replace(f'theme[net_box]="{p["red"]}"', f'theme[net_box]="{p["blue"]}"')
    t = re.sub(r'^(theme\[(?:available|download)_(?:mid|end)\]=)"' + p["red"] + '"',
               lambda m: m.group(1) + '"' + p["orange"] + '"', t, flags=re.M)
    return "# Endurance btop theme — GENERATED by scripts/genpalette.py from Omarchy's template.\n" \
           "# Red is kept for alarms only.\n" + t


if __name__ == "__main__":
    p = build()
    ok, r = report(p)
    if not ok:
        sys.exit("\nrefusing to write: a constraint above failed")
    for name, text in (("colors.toml", emit_colors(p, r)), ("btop.theme", emit_btop(p))):
        if text is None:
            print(f"skipped {name} (template not found)")
            continue
        with open(os.path.join(ROOT, name), "w") as f:
            f.write(text)
        print(f"wrote {name}")
