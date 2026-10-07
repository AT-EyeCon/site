"""Locate the fighter's head in each base frame (template match on colour-class maps).
Output: {frame: [cx, cy, angle_deg, hflip, score]} in canvas coords."""
import numpy as np
from PIL import Image
from scipy.signal import fftconvolve

# colour classes of the shared Kitana/Mileena palette indices
CLASS = np.zeros(16, int)
for i in (2, 4, 5, 6, 11): CLASS[i] = 1      # costume
for i in (7, 9, 10, 12, 13): CLASS[i] = 2    # skin
for i in (1, 3, 8, 14, 15): CLASS[i] = 3     # dark / hair / belt
NCLS = 4


def class_map(img):
    a = np.frombuffer(img.tobytes(), np.uint8).reshape(img.size[1], img.size[0])
    return CLASS[a]


def rotate_cls(t, angle, flip):
    im = Image.fromarray(t.astype(np.uint8))
    if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    im = im.rotate(angle, resample=Image.NEAREST, expand=True, fillcolor=255)
    return np.array(im)


def find_head(cm, templates, weights=(0.25, 1.0, 1.4, 1.0), angles=range(0, 360, 15)):
    oh = [(cm == k).astype(np.float32) for k in range(NCLS)]
    best = None
    for tname, t in templates.items():
        for flip in (0, 1):
            for ang in angles:
                r = rotate_cls(t, ang, flip)
                valid = r != 255
                score = np.zeros(cm.shape, np.float32)
                n = valid.sum()
                for k in range(NCLS):
                    tk = ((r == k) & valid).astype(np.float32) * weights[k]
                    if tk.sum() == 0: continue
                    score += fftconvolve(oh[k], tk[::-1, ::-1], mode='same')
                score /= n
                y, x = np.unravel_index(np.argmax(score), score.shape)
                s = float(score[y, x])
                if best is None or s > best[4]:
                    best = [int(x), int(y), int(ang), int(flip), s, tname]
    return best
