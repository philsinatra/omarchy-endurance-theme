#!/usr/bin/env python3
"""Schwarzschild black hole with a thin accretion disk — HDR render.

Units: G = c = M = 1, so the horizon is r = 2 and the photon sphere r = 3.
Rays are traced backward from the camera; each obeys the exact null
geodesic in Cartesian form:  a = -1.5 * h^2 * x / r^5,  h = |x cross v|.

Usage: blackhole.py out.npy WIDTH HEIGHT [key=value ...]
Writes a float32 HDR array (H, W, 3); tone-map it with blackhole_post.py.
Requires numpy. Uses every CPU core.

backgrounds/1-gargantua.jpg was made with (about 45 minutes on 8 cores):
  blackhole.py g.npy 5120 2880 r_out=20 elev=2 lum_pow=4.2 col_pow=2.2 \
      disk_gain=3.0 fov=30 ss=2
  blackhole_post.py g.npy ../backgrounds/1-gargantua.jpg exposure=0.75 stars=3 star_glow=8
"""
import sys, math, os
import numpy as np
from multiprocessing import Pool

P = dict(
    dist=34.0,          # camera distance from the hole
    elev=5.5,           # camera elevation above the disk plane (degrees)
    yaw=0.0,            # camera yaw around the vertical axis (degrees)
    fov=34.0,           # vertical field of view (degrees)
    tilt=0.0,           # roll of the camera (degrees)
    shift_x=0.0,        # principal point offset, fraction of width
    shift_y=0.0,        # principal point offset, fraction of height (+ = hole moves down)
    r_in=4.6,
    r_out=26.0,
    beaming=1.1,        # exponent on the Doppler factor (film used ~0)
    disk_gain=2.2,
    star_gain=1.0,
    seed=7,
    lum_pow=3.0,
    col_pow=1.0,
    ss=1,               # supersampling factor per axis (render at W*ss, box-filter down)
)

TEX_R, TEX_PHI = 1400, 3000


def disk_texture(seed):
    """Density texture in (r, phi): fine concentric streaks, slow azimuthal drift."""
    rng = np.random.default_rng(seed)
    n = rng.standard_normal((TEX_R, TEX_PHI)).astype(np.float32)
    F = np.fft.rfft2(n)
    fr = np.fft.fftfreq(TEX_R)[:, None]
    fp = np.fft.rfftfreq(TEX_PHI)[None, :]
    # strongly anisotropic: long along phi, fine along r
    k = np.exp(-(fr / 0.06) ** 2 - (fp / 0.0035) ** 2)
    streak = np.fft.irfft2(F * k, s=(TEX_R, TEX_PHI))
    k2 = np.exp(-(fr / 0.012) ** 2 - (fp / 0.0015) ** 2)
    band = np.fft.irfft2(F * k2, s=(TEX_R, TEX_PHI))
    s = streak / streak.std()
    b = band / band.std()
    d = 0.72 + 0.10 * np.tanh(0.9 * s) + 0.26 * np.tanh(0.8 * b)
    return np.clip(d, 0.05, 1.3).astype(np.float32)


def blackbody_rgb(t):
    """t in 0..1 (cool..hot) -> linear RGB along an ember -> amber -> white-gold ramp."""
    stops = np.array([
        [0.00, 0.28, 0.045, 0.008],
        [0.30, 0.90, 0.230, 0.035],
        [0.55, 1.00, 0.480, 0.110],
        [0.80, 1.00, 0.720, 0.330],
        [1.00, 1.00, 0.900, 0.700],
    ], dtype=np.float64)
    out = np.empty(t.shape + (3,))
    for c in range(3):
        out[..., c] = np.interp(t, stops[:, 0], stops[:, c + 1])
    return out


def _hash(ix, iy, salt):
    h = (ix.astype(np.int64) * 73856093) ^ (iy.astype(np.int64) * 19349663) ^ (salt * 83492791)
    h = (h ^ (h >> 13)) * 1274126177
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF).astype(np.float64) / float(0xFFFFFF)


def stars(d, J, f0, gain):
    """Analytic starfield. d: (N,3) unit escape directions; J: (N,2,2) sky
    displacement (radians, lon*cos(lat) / lat) per image pixel — the lensing
    Jacobian. Each star is evaluated in *image* space, so it stays a round
    point however hard the hole bends the sky, and its brightness scales
    with the magnification (flux is conserved)."""
    lon = np.arctan2(d[:, 0], d[:, 2])  # seam sits behind the camera
    lat = np.arcsin(np.clip(d[:, 1], -1, 1))
    det = J[:, 0, 0] * J[:, 1, 1] - J[:, 0, 1] * J[:, 1, 0]
    det = np.where(np.abs(det) < 1e-18, 1e-18, det)
    inv = np.stack([np.stack([J[:, 1, 1], -J[:, 0, 1]], 1),
                    np.stack([-J[:, 1, 0], J[:, 0, 0]], 1)], 1) / det[:, None, None]
    boost = np.minimum(f0 * f0 / np.abs(det), 40.0)
    out = np.zeros((d.shape[0], 3))
    layers = [  # cell size (deg), probability, brightness, salt
        (0.05, 0.10, 0.07, 1),
        (0.14, 0.10, 0.30, 2),
        (0.50, 0.10, 1.20, 3),
        (1.60, 0.12, 4.00, 4),
    ]
    s_img = 0.62  # star radius in (supersampled) pixels
    for cell, prob, scale, salt in layers:
        c = math.radians(cell)
        gx = lon / c
        gy = lat / c
        ix, iy = np.floor(gx), np.floor(gy)
        present = _hash(ix, iy, salt) < prob
        ox = 0.15 + 0.7 * _hash(ix, iy, salt + 11)
        oy = 0.15 + 0.7 * _hash(ix, iy, salt + 23)
        dsky = np.stack([(ox + ix - gx) * c * np.cos(lat), (oy + iy - gy) * c], 1)
        pimg = np.einsum("nij,nj->ni", inv, dsky)
        r2 = np.sum(pimg * pimg, axis=1)
        u = _hash(ix, iy, salt + 37)
        b = scale * (0.12 + u ** 4.0)
        w = np.where(present & (r2 < 36), b * np.exp(-r2 / (2 * s_img * s_img)) * boost, 0.0)
        tint = _hash(ix, iy, salt + 51)
        col = np.stack([
            np.where(tint < 0.22, 1.00, np.where(tint > 0.78, 0.74, 0.93)),
            np.where(tint < 0.22, 0.84, np.where(tint > 0.78, 0.85, 0.94)),
            np.where(tint < 0.22, 0.62, np.where(tint > 0.78, 1.00, 0.98)),
        ], axis=1)
        out += w[:, None] * col
    return out * gain


def camera_rays(W, H, rows, p):
    el, yaw, roll = (math.radians(p[k]) for k in ("elev", "yaw", "tilt"))
    cam = p["dist"] * np.array([math.sin(yaw) * math.cos(el), math.sin(el), -math.cos(yaw) * math.cos(el)])
    fwd = -cam / np.linalg.norm(cam)
    up0 = np.array([0.0, 1.0, 0.0])
    right = np.cross(fwd, up0); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    right, up = (math.cos(roll) * right + math.sin(roll) * up,
                 -math.sin(roll) * right + math.cos(roll) * up)
    f = 0.5 * H / math.tan(math.radians(p["fov"]) / 2)
    yy, xx = np.meshgrid(rows + 0.5, np.arange(W) + 0.5, indexing="ij")
    xx = xx.ravel(); yy = yy.ravel()
    px = xx - W * (0.5 + p["shift_x"])
    py = -(yy - H * (0.5 + p["shift_y"]))
    d = fwd[None, :] * f + right[None, :] * px[:, None] + up[None, :] * py[:, None]
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    return np.broadcast_to(cam, d.shape).copy(), d, math.radians(p["fov"]) / H


def trace(args):
    rows, W, H, p, tex = args
    x, v, _ = camera_rays(W, H, rows, p)
    n = x.shape[0]
    h2 = np.sum(np.cross(x, v) ** 2, axis=1)
    col = np.zeros((n, 3))
    alpha = np.zeros(n)
    alive = np.ones(n, dtype=bool)
    escaped = np.zeros(n, dtype=bool)
    r_in, r_out = p["r_in"], p["r_out"]

    def acc(xx, hh):
        r2 = np.sum(xx * xx, axis=1)
        return -1.5 * hh[:, None] * xx / (r2 ** 2.5)[:, None]

    for _ in range(3000):
        idx = np.nonzero(alive)[0]
        if idx.size == 0:
            break
        xi, vi, hi = x[idx], v[idx], h2[idx]
        r = np.linalg.norm(xi, axis=1)
        dt = np.clip(0.035 * r * np.clip((r - 1.9) / 2.0, 0.08, 1.0), 0.004, 1.5)[:, None]
        # RK4 on (x, v)
        k1x, k1v = vi, acc(xi, hi)
        k2x, k2v = vi + 0.5 * dt * k1v, acc(xi + 0.5 * dt * k1x, hi)
        k3x, k3v = vi + 0.5 * dt * k2v, acc(xi + 0.5 * dt * k2x, hi)
        k4x, k4v = vi + dt * k3v, acc(xi + dt * k3x, hi)
        nx = xi + dt / 6 * (k1x + 2 * k2x + 2 * k3x + k4x)
        nv = vi + dt / 6 * (k1v + 2 * k2v + 2 * k3v + k4v)

        # disk plane crossing (y = 0)
        cross = (xi[:, 1] * nx[:, 1]) < 0
        if cross.any():
            ci = np.nonzero(cross)[0]
            t = xi[ci, 1] / (xi[ci, 1] - nx[ci, 1])
            pc = xi[ci] + (nx[ci] - xi[ci]) * t[:, None]
            rc = np.hypot(pc[:, 0], pc[:, 2])
            hit = (rc > r_in) & (rc < r_out)
            if hit.any():
                ci, pc, rc = ci[hit], pc[hit], rc[hit]
                gi = idx[ci]
                phi = np.arctan2(pc[:, 2], pc[:, 0])
                # texture co-ordinates; slight spiral so streaks are not perfect circles
                ur = (np.log(rc / r_in) / np.log(r_out / r_in))
                up_ = ((phi + 0.35 * np.log(rc)) / (2 * np.pi)) % 1.0
                dens = tex[np.clip((ur * (TEX_R - 1)).astype(int), 0, TEX_R - 1),
                           np.clip((up_ * (TEX_PHI - 1)).astype(int), 0, TEX_PHI - 1)]
                # thin-disk temperature profile
                T = rc ** -0.75 * np.clip(1 - np.sqrt(r_in / rc), 0, 1) ** 0.25
                Tmax = (49 / 36 * r_in) ** -0.75 * (1 - math.sqrt(36 / 49)) ** 0.25
                tn = np.clip(T / Tmax, 0, 1.2)
                # edges: soft inner rim, long outer fade
                fade = np.clip((rc - r_in) / 0.9, 0, 1) ** 1.5 * np.clip((r_out - rc) / (0.55 * r_out), 0, 1) ** 1.6
                # Doppler: disk orbits counter-clockwise seen from +y
                beta = np.clip(np.sqrt(1.0 / np.maximum(rc - 2.0, 0.5)), 0, 0.62)
                u_orb = np.stack([-pc[:, 2], np.zeros_like(rc), pc[:, 0]], axis=1) / rc[:, None]
                vd = vi[ci] / np.linalg.norm(vi[ci], axis=1, keepdims=True)
                cos_t = np.sum(u_orb * (-vd), axis=1)
                gamma = 1 / np.sqrt(1 - beta ** 2)
                D = 1 / (gamma * (1 - beta * cos_t))
                grav = np.sqrt(np.clip(1 - 3 / rc, 0.05, 1))
                lum = p["disk_gain"] * (tn ** p["lum_pow"]) * dens * fade * (D ** p["beaming"]) * grav
                ctemp = np.clip((tn ** p["col_pow"]) * (D ** 0.35), 0, 1)
                c = blackbody_rgb(ctemp) * lum[:, None]
                a = np.clip(0.93 * dens * fade * np.clip(tn * 2.2, 0, 1), 0, 0.97)
                col[gi] += (1 - alpha[gi])[:, None] * c
                alpha[gi] += (1 - alpha[gi]) * a

        x[idx], v[idx] = nx, nv
        rn = np.linalg.norm(nx, axis=1)
        dead = rn < 2.0005
        esc = (rn > 80) & (np.sum(nx * nv, axis=1) > 0)
        opaque = alpha[idx] > 0.995
        alive[idx[dead | esc | opaque]] = False
        escaped[idx[esc]] = True

    d = np.full((n, 3), np.nan)
    e = np.nonzero(escaped)[0]
    d[e] = v[e] / np.linalg.norm(v[e], axis=1, keepdims=True)
    shape = (len(rows), W)
    return (col.reshape(shape + (3,)).astype(np.float32),
            alpha.reshape(shape).astype(np.float32),
            d.reshape(shape + (3,)).astype(np.float32))


def shade_stars(dirs, alpha, f0, gain, chunk=192):
    """Shade escaped rays with the starfield, using finite-difference Jacobians."""
    H, W, _ = dirs.shape
    out = np.zeros((H, W, 3), np.float32)
    for y0 in range(0, H, chunk):
        y1 = min(H, y0 + chunk)
        b = min(H, y1 + 1)
        d = dirs[y0:b].astype(np.float64)
        n = y1 - y0
        lon = np.arctan2(d[..., 0], d[..., 2]); lat = np.arcsin(np.clip(d[..., 1], -1, 1))
        # tangent basis: d/dlon (normalised) and d/dlat
        e_lon = np.stack([np.cos(lon), np.zeros_like(lon), -np.sin(lon)], -1)
        e_lat = np.stack([-np.sin(lat) * np.sin(lon), np.cos(lat), -np.sin(lat) * np.cos(lon)], -1)
        Dx = np.empty_like(d); Dy = np.empty_like(d)
        Dx[:, :-1] = d[:, 1:] - d[:, :-1]; Dx[:, -1] = Dx[:, -2]
        Dy[:-1] = d[1:] - d[:-1]; Dy[-1] = Dy[-2]
        J = np.empty(d.shape[:2] + (2, 2))
        J[..., 0, 0] = np.sum(Dx * e_lon, -1); J[..., 0, 1] = np.sum(Dy * e_lon, -1)
        J[..., 1, 0] = np.sum(Dx * e_lat, -1); J[..., 1, 1] = np.sum(Dy * e_lat, -1)
        d, J = d[:n], J[:n]
        bad = ~np.isfinite(J).all(axis=(-1, -2))
        J[bad] = np.array([[f0, 0.0], [0.0, -f0]])
        ok = np.isfinite(d[..., 0])
        blk = np.zeros((n, W, 3))
        blk[ok] = stars(d[ok], J[ok], f0, gain)
        out[y0:y1] = (blk * (1 - alpha[y0:y1, :, None])).astype(np.float32)
    return out


def main():
    out, W, H = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    p = dict(P)
    for kv in sys.argv[4:]:
        k, v = kv.split("=")
        p[k] = type(P[k])(float(v)) if not isinstance(P[k], int) else int(float(v))
    ss = int(p["ss"])
    RW, RH = W * ss, H * ss
    tex = disk_texture(p["seed"])
    step = 24
    tiles = [(np.arange(y, min(y + step, RH)), RW, RH, p, tex) for y in range(0, RH, step)]
    with Pool(os.cpu_count()) as pool:
        parts = pool.map(trace, tiles, chunksize=1)
    col = np.concatenate([q[0] for q in parts]); alpha = np.concatenate([q[1] for q in parts])
    dirs = np.concatenate([q[2] for q in parts]); del parts
    f0 = math.radians(p["fov"]) / RH
    col += shade_stars(dirs, alpha, f0, p["star_gain"])
    img = col.reshape(H, ss, W, ss, 3).mean(axis=(1, 3))
    np.save(out, img.astype(np.float32))
    print("saved", out, img.shape, "max", float(img.max()), "mean", float(img.mean()))


if __name__ == "__main__":
    main()
