"""Render sprite-set frames to PIL images / contact sheets."""
from PIL import Image, ImageDraw
import sprites as sp

W, H = 128, 160          # frame canvas; origin placed at (OX, OY)
OX, OY = 64, 120


def bgr555(c):
    return ((c & 31) << 3, (c >> 5 & 31) << 3, (c >> 10 & 31) << 3)


def read_palette(rom, addr):
    o = sp.off(addr)
    return [bgr555(rom[o + 2 * i] | rom[o + 2 * i + 1] << 8) for i in range(16)]


def frame_index_image(rom, hdr, n):
    """'P' image of colour indices (0 = transparent)."""
    fr = sp.parse_frame(rom, hdr, n)
    im = Image.new('P', (W, H), 0)
    for x, y, v in sp.frame_pixels(rom, hdr, fr):
        X, Y = x + OX, y + OY
        # earlier pieces have OAM priority -> first writer wins
        if 0 <= X < W and 0 <= Y < H and not im.getpixel((X, Y)): im.putpixel((X, Y), v)
    return im


def sheet(images, labels, pal, cols=16, bg=(40, 40, 56)):
    rows = (len(images) + cols - 1) // cols
    out = Image.new('RGB', (cols * W, rows * (H + 10)), bg)
    d = ImageDraw.Draw(out)
    flat = []
    for c in pal: flat += list(c)
    for i, (im, lab) in enumerate(zip(images, labels)):
        p = im.copy(); p.putpalette(flat + [0] * (768 - len(flat)))
        rgba = p.convert('RGBA'); mask = Image.frombytes('L', im.size, bytes(255 if v else 0 for v in im.tobytes()))
        x, y = (i % cols) * W, (i // cols) * (H + 10)
        out.paste(rgba.convert('RGB'), (x, y + 10), mask)
        d.text((x + 2, y + H - 2), str(lab), fill=(255, 255, 0))
    return out
