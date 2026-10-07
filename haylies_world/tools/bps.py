"""Minimal BPS patch creator/applier (SourceRead / TargetRead / SourceCopy runs)."""
import zlib, sys

def _num(n):
    out = bytearray()
    while True:
        x = n & 0x7F; n >>= 7
        if n == 0: out.append(0x80 | x); return out
        out.append(x); n -= 1

def create(src, dst, meta=b''):
    out = bytearray(b'BPS1') + _num(len(src)) + _num(len(dst)) + _num(len(meta)) + meta
    i, n = 0, len(dst)
    while i < n:
        if i < len(src) and src[i] == dst[i]:
            j = i
            while j < n and j < len(src) and src[j] == dst[j]: j += 1
            out += _num(((j - i - 1) << 2) | 0); i = j          # SourceRead
        else:
            j = i
            while j < n and not (j < len(src) and src[j] == dst[j] and j + 1 < n and j + 1 < len(src) and src[j + 1] == dst[j + 1]): j += 1
            out += _num(((j - i - 1) << 2) | 1) + dst[i:j]; i = j  # TargetRead
    for c in (zlib.crc32(src), zlib.crc32(dst)): out += c.to_bytes(4, 'little')
    out += zlib.crc32(out).to_bytes(4, 'little')
    return bytes(out)

def apply(src, patch):
    p = 4
    def rd():
        nonlocal p; data, shift = 0, 1
        while True:
            x = patch[p]; p += 1; data += (x & 0x7F) * shift
            if x & 0x80: return data
            shift <<= 7; data += shift
    assert patch[:4] == b'BPS1'
    ss, ts, ms = rd(), rd(), rd(); p += ms
    out = bytearray(); so = to = 0
    while p < len(patch) - 12:
        d = rd(); cmd, ln = d & 3, (d >> 2) + 1
        if cmd == 0: out += src[len(out):len(out) + ln]
        elif cmd == 1: out += patch[p:p + ln]; p += ln
        elif cmd == 2:
            o = rd(); so += (-1 if o & 1 else 1) * (o >> 1)
            out += src[so:so + ln]; so += ln
        else:
            o = rd(); to += (-1 if o & 1 else 1) * (o >> 1)
            for _ in range(ln): out.append(out[to]); to += 1
    assert zlib.crc32(src) == int.from_bytes(patch[-12:-8], 'little')
    assert zlib.crc32(out) == int.from_bytes(patch[-8:-4], 'little')
    return bytes(out)

if __name__ == '__main__':
    s, d, o = sys.argv[1:4]
    open(o, 'wb').write(create(open(s, 'rb').read(), open(d, 'rb').read()))
