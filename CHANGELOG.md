# Changelog

All notable changes to Endurance are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-09-27

Endurance now installs like any other Omarchy theme: one `omarchy theme
install` and every app, Neovim included, is themed from `colors.toml`.

### Changed

- Palette redesigned for the roles Omarchy's templates assign each slot:
  - nebula violet keywords, accretion amber types, starlight constants, ember
    numbers
  - blueshift functions, glacier parameters, frost properties, lichen strings
  - Neovim and VS Code now read the same way.
- Comments raised to 5.4:1 contrast. Every pair of syntax roles is at least
  0.078 apart in OKLab.
- Preview image and palette card regenerated from the stock-generated editor
  theme.

### Removed

- The hand-written `neovim.lua` and its template. Omarchy drops Lua files from
  git-installed themes, so it only ever reached symlinked installs.

## [0.1.0] - 2026-09-27

First release.

### Added

- Thermal-spectrum palette generated in OKLCH: amber for keywords, ember for
  literals, blue for functions, glacier for types, lichen for strings, nebula
  for machinery, red for errors only. Enforced checks for text contrast
  (12.9:1), comments (5.7:1) and minimum perceptual distance between roles.
- Full Neovim theme on `aether.nvim`: over 400 highlight groups, including
  treesitter, LSP semantic tokens, diagnostics and common plugins, with bold
  definitions and regular call sites.
- `btop.theme` with red reserved for alarms.
- Four backgrounds, each with a dark top edge:
  - `1-gargantua.jpg`, an original ray-traced black hole
  - `2-event-horizon.webp`, an original lossless gradient
  - `3-saturn.jpg`, NASA Cassini
  - `4-crescent-earth.jpg`, NASA Artemis II
- Theme-switcher preview, Plymouth unlock wordmark and palette card.
- Generator scripts for the palette, Neovim theme, btop theme, gradient and
  black hole render.

[0.2.0]: https://github.com/philsinatra/omarchy-endurance-theme/releases/tag/v0.2.0
[0.1.0]: https://github.com/philsinatra/omarchy-endurance-theme/releases/tag/v0.1.0
