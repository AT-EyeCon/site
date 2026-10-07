"""Minimal headless libretro frontend (snes9x core) for automated ROM testing."""
import ctypes as C, os
from PIL import Image

CORE = '/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so'
BTN = dict(B=0, Y=1, SELECT=2, START=3, UP=4, DOWN=5, LEFT=6, RIGHT=7, A=8, X=9, L=10, R=11)

class GameInfo(C.Structure):
    _fields_ = [('path', C.c_char_p), ('data', C.c_void_p), ('size', C.c_size_t), ('meta', C.c_char_p)]

ENV = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
VID = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUD = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
AUDB = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
POLL = C.CFUNCTYPE(None)
INST = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)

class Emu:
    def __init__(self, rom_path):
        self.lib = C.CDLL(CORE)
        self.pressed = set()
        self.frame = None
        self._sysdir = C.c_char_p(b'/tmp')
        def env(cmd, data):
            if cmd == 10:  # SET_PIXEL_FORMAT
                self.fmt = C.cast(data, C.POINTER(C.c_int))[0]
                return True
            if cmd in (9, 31):
                C.cast(data, C.POINTER(C.c_char_p))[0] = self._sysdir.value
                return True
            return False
        def vid(data, w, h, pitch):
            if data:
                buf = C.string_at(data, pitch * h)
                self.frame = (bytes(buf), w, h, pitch)
        self._cbs = [ENV(env), VID(vid), AUD(lambda l, r: None), AUDB(lambda d, f: f), POLL(lambda: None),
                     INST(lambda p, d, i, b: 1 if (p == 0 and d == 1 and b in self.pressed) else 0)]
        L = self.lib
        L.retro_set_environment(self._cbs[0])
        L.retro_init()
        L.retro_set_video_refresh(self._cbs[1]); L.retro_set_audio_sample(self._cbs[2])
        L.retro_set_audio_sample_batch(self._cbs[3]); L.retro_set_input_poll(self._cbs[4])
        L.retro_set_input_state(self._cbs[5])
        self.romdata = open(rom_path, 'rb').read()
        self._rb = C.create_string_buffer(self.romdata)
        gi = GameInfo(rom_path.encode(), C.cast(self._rb, C.c_void_p), len(self.romdata), None)
        L.retro_load_game.restype = C.c_bool; L.retro_serialize.restype = C.c_bool; L.retro_unserialize.restype = C.c_bool
        assert L.retro_load_game(C.byref(gi)), 'load failed'
        L.retro_get_memory_data.restype = C.c_void_p
        L.retro_get_memory_size.restype = C.c_size_t
        L.retro_serialize_size.restype = C.c_size_t

    def run(self, n=1, buttons=()):
        self.pressed = {BTN[b] for b in buttons}
        for _ in range(n):
            self.lib.retro_run()
        self.pressed = set()

    def ram(self):
        p = self.lib.retro_get_memory_data(2); n = self.lib.retro_get_memory_size(2)
        return (C.c_ubyte * n).from_address(p)

    def save_state(self):
        n = self.lib.retro_serialize_size(); b = C.create_string_buffer(n)
        assert self.lib.retro_serialize(b, n); return b.raw
    def load_state(self, s):
        b = C.create_string_buffer(s); assert self.lib.retro_unserialize(b, len(s))

    def shot(self, path=None, scale=1):
        data, w, h, pitch = self.frame
        if self.fmt == 1:
            im = Image.frombuffer('RGBA', (w, h), data, 'raw', 'BGRA', pitch, 1).convert('RGB')
        else:
            im = Image.frombuffer('RGB', (w, h), data, 'raw', 'BGR;16' if self.fmt == 2 else 'BGR;15', pitch, 1)
        if scale > 1: im = im.resize((w * scale, h * scale), Image.NEAREST)
        if path: im.save(path)
        return im

def boot_to_level(e, max_frames=6000, log=False):
    """From power-on, mash START/A until game mode $0100 == $14 (in level)."""
    f = 0; seen = []
    while f < max_frames:
        m = e.ram()[0x100]
        if not seen or seen[-1] != m: seen.append(m)
        if m == 0x14 and f > 200:
            break
        e.run(6, ('START',) if (f // 6) % 4 == 0 else (('A',) if (f // 6) % 4 == 2 else ()))
        f += 6
    if log: print('modes', [hex(x) for x in seen], 'frames', f)
    return e.ram()[0x100] == 0x14


def wait_mode(e, mode, max_frames=4000, press=('A',)):
    f = 0
    while f < max_frames:
        if e.ram()[0x100] == mode and f > 30: return True
        e.run(5, press if (f // 5) % 3 == 0 else ()); f += 5
    return False

def boot_to_playable(e):
    """Power on -> intro -> overworld -> Yoshi's House (fresh boot, no save states)."""
    ok = boot_to_level(e) and wait_mode(e, 0x0E)
    e.run(60); ok = ok and wait_mode(e, 0x14)
    e.run(120); return ok
