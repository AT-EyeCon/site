"""LC_LZ2 (Super Mario World graphics) compression / decompression."""

def decompress(data, pos=0):
    out = bytearray()
    start = pos
    while True:
        b = data[pos]; pos += 1
        if b == 0xFF:
            break
        cmd = b >> 5
        if cmd == 7:
            cmd = (b >> 2) & 7
            n = ((b & 3) << 8 | data[pos]) + 1; pos += 1
        else:
            n = (b & 0x1F) + 1
        if cmd == 0:
            out += data[pos:pos + n]; pos += n
        elif cmd == 1:
            out += bytes([data[pos]]) * n; pos += 1
        elif cmd == 2:
            w = data[pos:pos + 2]; pos += 2
            out += (w * ((n + 1) // 2))[:n]
        elif cmd == 3:
            v = data[pos]; pos += 1
            out += bytes((v + i) & 0xFF for i in range(n))
        elif cmd == 4:
            off = data[pos] << 8 | data[pos + 1]; pos += 2
            for i in range(n):
                out.append(out[off + i])
        else:
            raise ValueError("bad cmd %d at %x" % (cmd, pos))
    return bytes(out), pos - start


def _hdr(cmd, n):
    n -= 1
    if n < 32 and cmd != 7:
        return bytes([cmd << 5 | n])
    return bytes([0xE0 | cmd << 2 | n >> 8, n & 0xFF])


def compress(data):
    """Greedy LZ2 compressor (fill / word fill / increasing fill / repeat)."""
    data = bytes(data)
    out = bytearray()
    lit = bytearray()
    i, L = 0, len(data)
    MAXN = 1024
    # index for repeats: map 3-byte key -> positions
    idx = {}

    def flush():
        nonlocal lit
        p = 0
        while p < len(lit):
            n = min(MAXN, len(lit) - p)
            out.extend(_hdr(0, n)); out.extend(lit[p:p + n]); p += n
        lit = bytearray()

    def add_idx(upto):
        for k in range(add_idx.done, upto):
            if k + 3 <= L:
                idx.setdefault(data[k:k + 3], []).append(k)
        add_idx.done = max(add_idx.done, upto)
    add_idx.done = 0

    while i < L:
        best = (0, None, 0)  # gain, cmd, n, arg
        # byte fill
        n = 1
        while i + n < L and n < MAXN and data[i + n] == data[i]:
            n += 1
        cands = [(n - 2, 1, n, data[i:i + 1])]
        # word fill
        if i + 1 < L:
            n = 2
            while i + n < L and n < MAXN and data[i + n] == data[i + (n & 1)]:
                n += 1
            cands.append((n - 3, 2, n, data[i:i + 2]))
        # increasing fill
        n = 1
        while i + n < L and n < MAXN and data[i + n] == (data[i] + n) & 0xFF:
            n += 1
        cands.append((n - 2, 3, n, data[i:i + 1]))
        # repeat
        add_idx(i)
        key = data[i:i + 3]
        for p in reversed(idx.get(key, [])[-64:]):
            n = 0
            while i + n < L and n < MAXN and data[p + n] == data[i + n]:
                n += 1
            if n - 3 > cands[-1][0] if cands[-1][1] == 4 else True:
                cands.append((n - 3, 4, n, bytes([p >> 8, p & 0xFF])))
        g, cmd, n, arg = max(cands, key=lambda c: c[0])
        if g > 0 and (n > 1):
            # header overhead difference for long runs is minor
            flush()
            out.extend(_hdr(cmd, n)); out.extend(arg)
            i += n
        else:
            lit.append(data[i]); i += 1
            if len(lit) == MAXN:
                flush()
    flush()
    out.append(0xFF)
    return bytes(out)
