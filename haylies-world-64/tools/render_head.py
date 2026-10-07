"""Offline preview renderer for SM64 head display lists (head-bone space: X up, Y forward, Z side)."""
import re, sys, math, argparse
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument('--src', nargs='+', required=True)
ap.add_argument('--root', nargs='+', required=True)
ap.add_argument('--texdir', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--yaws', default='0,90,180,270,35')
ap.add_argument('--size', type=int, default=260)
a = ap.parse_args()

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sm64dl
tris, tex, vtx, gfx = sm64dl.load(a.src, a.root, a.texdir)
S = a.size
views = []
for yaw in [float(y) for y in a.yaws.split(',')]:
    th = math.radians(yaw)
    img = np.full((S, S, 3), 0.12); zb = np.full((S, S), -1e9)
    ldir = np.array([0.4, 0.7, 0.3]); ldir /= np.linalg.norm(ldir)
    for vs, l1, l2, tn in tris:
        P = []; UV = []; N = []
        for (x, y, z, s, t, nx, ny, nz) in vs:
            # rotate about head-up axis X; viewer looks along -Y at yaw 0
            yy = y * math.cos(th) - z * math.sin(th); zz = y * math.sin(th) + z * math.cos(th)
            P.append((zz, x - 110, yy)); UV.append((s / 32.0, t / 32.0))
            n = np.array([nx, ny, nz], float); N.append(n / (np.linalg.norm(n) + 1e-6))
        P = np.array(P); sc = S / 420
        sx = S / 2 + P[:, 0] * sc; sy = S / 2 - P[:, 1] * sc; dz = P[:, 2]
        x0, x1 = int(max(0, math.floor(sx.min()))), int(min(S - 1, math.ceil(sx.max())))
        y0, y1 = int(max(0, math.floor(sy.min()))), int(min(S - 1, math.ceil(sy.max())))
        if x1 < x0 or y1 < y0: continue
        den = (sy[1] - sy[2]) * (sx[0] - sx[2]) + (sx[2] - sx[1]) * (sy[0] - sy[2])
        if abs(den) < 1e-9: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        w0 = ((sy[1] - sy[2]) * (gx - sx[2]) + (sx[2] - sx[1]) * (gy - sy[2])) / den
        w1 = ((sy[2] - sy[0]) * (gx - sx[2]) + (sx[0] - sx[2]) * (gy - sy[2])) / den
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
        if not m.any(): continue
        z = w0 * dz[0] + w1 * dz[1] + w2 * dz[2]
        sub = zb[y0:y1+1, x0:x1+1]; m &= z > sub
        if not m.any(): continue
        nrm = sum(w * n for w, n in zip((w0[m], w1[m], w2[m]), N)) if False else None
        n = N[0] + N[1] + N[2]; n /= np.linalg.norm(n) + 1e-6
        shade = np.clip(l2 + l1 * max(0.0, float(n @ ldir)), 0, 1)
        c = np.broadcast_to(shade, (m.sum(), 3)).copy()
        if tn:
            T = tex(tn); u = w0[m]*UV[0][0] + w1[m]*UV[1][0] + w2[m]*UV[2][0]; v = w0[m]*UV[0][1] + w1[m]*UV[1][1] + w2[m]*UV[2][1]
            tx = np.clip(u.astype(int), 0, T.shape[1]-1); ty = np.clip(v.astype(int), 0, T.shape[0]-1)
            tc = T[ty, tx]; al = tc[:, 3:4]
            c = c * (1 - al) + tc[:, :3] * al
        sub[m] = z[m]; img[y0:y1+1, x0:x1+1][m] = c
    views.append(img)
out = np.concatenate(views, axis=1)
Image.fromarray((out * 255).astype(np.uint8)).resize((out.shape[1]*2, out.shape[0]*2), Image.NEAREST).save(a.out)
print('tris', len(tris))
