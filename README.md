# Endurance

**v0.1.0** · [Changelog](CHANGELOG.md)

![Endurance preview](preview.webp)

A deep-space engineering theme for [Omarchy](https://omarchy.org/), built for
long sessions and live lectures. Inspired by *Interstellar*: blue-black space,
amber light from something vast and hot, and nothing on screen that is not
doing a job.

## A thermal spectrum

The palette is one idea. Syntax colours are laid out like temperature — a
Doppler shift across the code:

| | Colour | Hex | Carries |
| --- | --- | --- | --- |
| **hot** | Accretion amber | `#eebd67` | **the language** — every reserved word, one colour |
| | Ember | `#ef9e70` | literal values — numbers, booleans, constants |
| **cold** | Blueshift | `#82b8ef` | functions — **bold where defined**, regular where called |
| | Glacier | `#87d4d7` | types, classes, constructors, components |
| | Lichen | `#9aca90` | strings |
| | Nebula | `#bda1de` | machinery — macros, decorators, builtins, escapes |
| **signal** | Red | `#ef766f` | errors, and nothing else |

Two quiet tints sit between those and plain text: **sand** `#e5c3a9` for
parameters and **frost** `#a6d1eb` for fields and properties.

That gives a beginner one rule per colour — *amber is the language, blue is a
function, glacier is a type, green is a string* — and gives an experienced
reader the structure at a glance: definitions stand out from call sites,
operators and brackets recede, and red never appears unless something is wrong.

![Palette](docs-palette.webp)

### Measured, not eyeballed

The palette is generated in OKLCH by `scripts/genpalette.py`, which refuses to
write unless every constraint holds:

| Check | Target | Endurance |
| --- | --- | --- |
| body text on background | ≥ 11:1 | **12.9:1** |
| comments | ≥ 4.8:1 | **5.7:1** |
| syntax band | — | 6.5 – 10.7:1 |
| closest pair of primary syntax roles (OKLab ΔE) | ≥ 0.08 | **0.082** |
| parameters/properties vs anything else | ≥ 0.045 | **0.048** |
| every colour inside sRGB | yes | yes |

The distance check is the one that matters on a projector: no two roles a
student has to tell apart are allowed to collapse into each other. Every syntax
hue sits in one lightness band (L 0.75–0.83) and one chroma band, so nothing
outshouts anything else during hour six.

## Neovim

Endurance ships its own `neovim.lua`: the full palette on top of the
`aether.nvim` engine Omarchy already uses, with every syntax and UI group
re-specified — over 400 of them. It is generated alongside `colors.toml` from
`scripts/neovim.lua.in`.

- **Semantic, not decorative.** One colour per role, as in the table above.
  LSP semantic tokens are mapped to the same roles, and deliberately step aside
  for function names so treesitter's definition-vs-call distinction survives.
- **Chrome is instrument-panel quiet.** One rule colour for every border and
  separator; floats, pickers and the file tree sit on a slightly deeper panel.
  Amber appears only where the eye should land: the cursor line number,
  titles, the prompt, fuzzy-match characters.
- **Diagnostics are readable in a lecture hall.** Undercurls in the role colour,
  virtual text on a faint wash of the same colour, inlay hints on their own
  tinted chip so they never read as code.
- Integrations: treesitter, LSP, blink.cmp, snacks (picker, dashboard, indent),
  neo-tree, telescope, which-key, flash, noice, gitsigns, trouble, lazy, mason,
  mini.icons, render-markdown.

If Neovim does not change, an old colorscheme override in
`~/.config/nvim/lua/plugins/` is pinning something else. Remove it and run
`omarchy theme set endurance` again.

## Backgrounds

Four frames that follow the film's arc — from the end of the voyage back home.

| File | Subject | Size | Mean |
| --- | --- | --- | --- |
| `1-gargantua.jpg` | A black hole and its disk, **ray-traced for this theme** | 5120×2880 | 12% |
| `2-event-horizon.webp` | The theme gradient: deep space, amber light from off-frame | 3840×2160 | 9% |
| `3-saturn.jpg` | Saturn eclipsing the Sun — Cassini, *The Day the Earth Smiled* | 5120×2880 | 13% |
| `4-crescent-earth.jpg` | A thin crescent Earth from lunar distance — Artemis II | 5120×2880 | 4% |

Every frame keeps its top edge dark (top 8% under 5% mean luminance), so the
status bar always has contrast. `1-gargantua.jpg` is real physics, not a
painting: light rays traced through Schwarzschild spacetime into a thin disk —
see `scripts/blackhole.py`. Credits and licences:
[`backgrounds/CREDITS.md`](backgrounds/CREDITS.md). Cycle them with
`omarchy theme bg next`.

## Install

Omarchy menu (`Super + Space`) → **Install → Style → Theme**, paste the git URL
of this repository. Or:

```sh
omarchy theme install https://github.com/philsinatra/omarchy-endurance-theme.git
omarchy theme set endurance
```

> `omarchy theme install` drops `.lua` files from cloned themes, so that route
> uses Omarchy's stock Neovim mapping. For the full Neovim theme, clone the
> repository anywhere and symlink it in. Omarchy trusts a symlink to your own
> working copy:
>
> ```sh
> git clone https://github.com/philsinatra/omarchy-endurance-theme.git ~/omarchy-endurance-theme
> ln -s ~/omarchy-endurance-theme ~/.config/omarchy/themes/endurance
> omarchy theme set endurance
> ```

## What is shipped

| File | Purpose |
| --- | --- |
| `colors.toml` | Source of truth for terminals, btop, Hyprland, the shell, VS Code, Helix, Obsidian and Chromium |
| `neovim.lua` | The full Neovim theme (generated) |
| `btop.theme` | Omarchy's btop template with red kept for alarms only (generated) |
| `icons.theme` | `Yaru-yellow` |
| `keyboard.rgb` | Accretion amber for RGB keyboards |
| `backgrounds/` | Four frames — see [`backgrounds/CREDITS.md`](backgrounds/CREDITS.md) |
| `preview.webp`, `docs-palette.webp` | Theme picker thumbnail, palette card |
| `unlock.png`, `preview-unlock.png` | Boot / disk-unlock (Plymouth) wordmark and its preview |
| `scripts/genpalette.py` | OKLCH constants → `colors.toml`, `neovim.lua` and `btop.theme`, with the contrast and separation checks |
| `scripts/neovim.lua.in` | Neovim highlight template |
| `scripts/oklch.py` | OKLCH ↔ sRGB, WCAG contrast, OKLab distance; no dependencies |
| `scripts/gradient.py` | Renders `2-event-horizon.webp` (numpy, Pillow) |
| `scripts/blackhole.py`, `scripts/blackhole_post.py` | Ray-traces and tone-maps `1-gargantua.jpg` (numpy, Pillow) |

## Design rules

1. Colour is information. Each hue has exactly one job, and a student can learn
   all of them in a minute.
2. Warm is the language, cool is the names. Red means *stop* and is never used
   for decoration.
3. Harmony is enforced numerically: one lightness band, one chroma band, a
   minimum perceptual distance between roles, and a generator that refuses to
   write a palette that breaks any of it.
4. The chassis is deep space: one cool hue at near-zero chroma, so code is the
   brightest thing on screen.
5. Backgrounds are single-subject, never upscaled, dark at the top edge, and
   good enough to sell the theme on their own.

## License

Theme files, the ray-traced black hole and the gradient are MIT — see
[`LICENSE`](LICENSE). The Saturn and Earth photographs are NASA imagery in the
public domain; see [`backgrounds/CREDITS.md`](backgrounds/CREDITS.md). Endurance
is not affiliated with NASA or with the film *Interstellar*.
