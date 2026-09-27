# Background credits

Four frames that follow the film's arc: the black hole at the end of the
voyage, the light that comes before it, Saturn where the wormhole waits,
and Earth, left behind.

| File | Subject | Source | Credit | Licence | Size |
| --- | --- | --- | --- | --- | --- |
| `1-gargantua.jpg` | A spinning disk of light around a black hole, seen edge-on | Original — ray-traced for this theme (`scripts/blackhole.py`) | Endurance contributors | MIT | 5120×2880 |
| `2-event-horizon.webp` | The theme's own gradient: deep space, amber light blooming from off-frame | Original — `scripts/gradient.py` | Endurance contributors | MIT | 3840×2160 |
| `3-saturn.jpg` | Saturn eclipsing the Sun, rings and the E ring backlit ("The Day the Earth Smiled") | [PIA17172](https://photojournal.jpl.nasa.gov/catalog/PIA17172) | NASA/JPL-Caltech/Space Science Institute | Public domain | 5120×2880 |
| `4-crescent-earth.jpg` | A thin crescent Earth, alone, from lunar distance | [art002e014066](https://images.nasa.gov/details/art002e014066) (Artemis II) | NASA | Public domain | 5120×2880 |

## The black hole is real physics

`1-gargantua.jpg` is not a painting or a film still. Every pixel is a light ray
traced backwards through the curved spacetime of a Schwarzschild black hole —
the exact null-geodesic equation, integrated with RK4 — into a thin accretion
disk and a procedural starfield. The arch over the top and the ring under the
bottom are the far side of the disk, bent into view by gravity, just as in the
film. Stars are shaded through the lensing Jacobian, so they stay points and
brighten as the hole magnifies them. It is rendered at 10240×5760 and
box-filtered down to 5120×2880.

## Processing

The two photographs are cropped to 16:9 at native resolution or larger and
downsampled to 5120 px — never upscaled. Each gets the same light grade: a
whisper of the theme's void blue in the blacks, and a soft fade over the top
10% so the status bar always sits on dark. Nothing else is altered.

## Licences

NASA imagery is not subject to copyright in the United States. NASA asks that
its insignia and imagery not be used to imply endorsement; this theme is not
affiliated with or endorsed by NASA, nor with the film *Interstellar*.

The two original frames are MIT, like the rest of the theme.
