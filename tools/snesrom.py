"""Generic SNES ROM helpers: hashing, header, checksum, BPS create/apply."""
import hashlib, zlib


def hashes(data):
    return {'size': len(data), 'md5': hashlib.md5(data).hexdigest(),
            'sha1': hashlib.sha1(data).hexdigest(), 'sha256': hashlib.sha256(data).hexdigest()}


def fix_checksum(rom, header=0xFFC0):
    """HiROM checksum; handles non-power-of-two sizes by mirroring the tail."""
    n = len(rom)
    rom[header + 0x1C:header + 0x20] = b'\xff\xff\x00\x00'
    p2 = 1
    while p2 * 2 <= n: p2 *= 2
    s = sum(rom[:p2])
    if n > p2:
        tail = rom[p2:]; reps = p2 // len(tail)
        s += sum(tail) * reps
    s &= 0xFFFF
    rom[header + 0x1E:header + 0x20] = bytes([s & 0xFF, s >> 8])
    c = s ^ 0xFFFF
    rom[header + 0x1C:header + 0x1E] = bytes([c & 0xFF, c >> 8])
    return s


def verify_checksum(rom, header=0xFFC0):
    cur = bytes(rom[header + 0x1C:header + 0x20])
    tmp = bytearray(rom); s = fix_checksum(tmp, header)
    return bytes(tmp[header + 0x1C:header + 0x20]) == cur, s


def _num(n):
    out = bytearray()
    while True:
        x = n & 0x7F; n >>= 7
        if n == 0: out.append(0x80 | x); return out
        out.append(x); n -= 1


def bps_create(src, dst, meta=b''):
    """Simple, valid BPS: SourceRead where bytes match at same offset, else TargetRead."""
    out = bytearray(b'BPS1') + _num(len(src)) + _num(len(dst)) + _num(len(meta)) + meta
    i = 0; n = len(dst)
    while i < n:
        same = i < len(src) and src[i] == dst[i]
        j = i
        while j < n and (j < len(src) and src[j] == dst[j]) == same: j += 1
        length = j - i
        out += _num(((length - 1) << 2) | (0 if same else 1))
        if not same: out += dst[i:j]
        i = j
    out += zlib.crc32(src).to_bytes(4, 'little') + zlib.crc32(dst).to_bytes(4, 'little')
    out += zlib.crc32(out).to_bytes(4, 'little')
    return bytes(out)


def bps_apply(src, patch):
    assert patch[:4] == b'BPS1'
    p = 4

    def num():
        nonlocal p
        data, shift = 0, 1
        while True:
            x = patch[p]; p += 1
            data += (x & 0x7F) * shift
            if x & 0x80: return data
            shift <<= 7; data += shift
    ss, ts, ms = num(), num(), num(); p += ms
    out = bytearray(ts); o = 0; sr = tr = 0
    end = len(patch) - 12
    while p < end:
        d = num(); act, ln = d & 3, (d >> 2) + 1
        if act == 0: out[o:o + ln] = src[o:o + ln]; o += ln
        elif act == 1: out[o:o + ln] = patch[p:p + ln]; p += ln; o += ln
        else:
            d2 = num(); off = (-1 if d2 & 1 else 1) * (d2 >> 1)
            if act == 2:
                sr += off
                for _ in range(ln): out[o] = src[sr]; o += 1; sr += 1
            else:
                tr += off
                for _ in range(ln): out[o] = out[tr]; o += 1; tr += 1
    assert zlib.crc32(src) == int.from_bytes(patch[-12:-8], 'little'), 'source CRC mismatch'
    assert zlib.crc32(out) == int.from_bytes(patch[-8:-4], 'little'), 'target CRC mismatch'
    return bytes(out)
