import re, numpy as np
from PIL import Image

def load(srcfiles, roots, texdir):
    src = '\n'.join(open(f).read() for f in srcfiles)
    src = re.sub(r'//[^\n]*', '', src)
    vtx = {}
    for name, body in re.findall(r'Vtx (\w+)\[\] = \{(.*?)\n\};', src, re.S):
        pts = []
        for m in re.finditer(r'\{\{\{\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)\s*\},\s*\w+,\s*\{\s*(-?\d+),\s*(-?\d+)\s*\},\s*\{\s*(\w+),\s*(\w+),\s*(\w+),\s*(\w+)\s*\}', body):
            g = m.groups()
            x, y, z, s, t = map(int, g[:5])
            n = [int(v, 0) for v in g[5:8]]
            n = [v - 256 if v > 127 else v for v in n]
            pts.append((x, y, z, s, t, *n))
        vtx[name] = pts
    gfx = {}
    for name, body in re.findall(r'Gfx (\w+)\[\] = \{(.*?)\n\};', src, re.S):
        gfx[name] = [c.strip() for c in re.findall(r'(gs\w+\(.*?\)),?\s*$', body, re.M)]
    texmap = {}
    for name, inc in re.findall(r'Texture (\w+)\[\] = \{\s*#include "actors/mario/([\w.]+)\.inc\.c"', src):
        texmap[name] = inc
    texcache = {}
    def tex(name):
        if name not in texcache:
            im = Image.open(f'{texdir}/{texmap[name]}.png').convert('RGBA')
            texcache[name] = np.asarray(im).astype(np.float32) / 255
        return texcache[name]
    
    def col(c):
        c = int(c, 0); return np.array([(c >> 24) & 255, (c >> 16) & 255, (c >> 8) & 255]) / 255
    
    tris = []  # (verts[3]: (pos,uv,n), light1, light2, texname or None)
    def run(dl, st):
        for c in gfx[dl]:
            op, args = c.split('(', 1)
            args = [x.strip() for x in args.rstrip(')').split(',')]
            if op == 'gsSPVertex':
                base = args[0]; off = 0
                if '+' in base: base, off = base.split('+'); base = base.strip(); off = int(off)
                for i in range(int(args[1])): st['buf'][int(args[2]) + i] = vtx[base][off + i]
            elif op in ('gsSP1Triangle', 'gsSP2Triangles'):
                idx = [int(x, 0) for x in args]
                for k in range(0, len(idx), 4):
                    tris.append(([st['buf'][i] for i in idx[k:k+3]], st['l1'], st['l2'], st['tex'] if st['ton'] else None))
            elif op == 'gsSPLightColor':
                st['l1' if args[0] == 'LIGHT_1' else 'l2'] = col(args[1])
            elif op == 'gsDPSetTextureImage':
                st['tex'] = args[3]
            elif op == 'gsSPTexture':
                st['ton'] = args[-1] == 'G_ON'
            elif op == 'gsSPDisplayList':
                run(args[0], st)
            elif op == 'gsSPEndDisplayList':
                return
    
    st = dict(buf=[None]*64, l1=np.array([1., 1, 1]), l2=np.array([.5, .5, .5]), tex=None, ton=False)
    for r in roots: run(r, st)
    
    return tris, tex, vtx, gfx
