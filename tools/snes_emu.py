"""Minimal headless libretro frontend (ctypes) for automated SNES checks.

Usage (library):
    emu = Emu(core_so, rom_path)
    emu.run(60)                 # frames
    emu.press(['START'], 2)     # hold buttons for N frames
    emu.screenshot('x.png')
"""
import ctypes as C, os, sys
from PIL import Image

BTN = {'B': 0, 'Y': 1, 'SELECT': 2, 'START': 3, 'UP': 4, 'DOWN': 5, 'LEFT': 6,
       'RIGHT': 7, 'A': 8, 'X': 9, 'L': 10, 'R': 11}

class GameInfo(C.Structure):
    _fields_ = [('path', C.c_char_p), ('data', C.c_void_p), ('size', C.c_size_t), ('meta', C.c_char_p)]

ENV_CB = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
VID_CB = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUD_CB = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
AUDB_CB = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
POLL_CB = C.CFUNCTYPE(None)
STATE_CB = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)


class Emu:
    def __init__(self, core, rom):
        self.lib = C.CDLL(os.path.abspath(core))
        self.pressed = [set(), set()]
        self.frame = None
        self._sysdir = C.c_char_p(os.path.dirname(os.path.abspath(rom)).encode())
        self._cbs = [ENV_CB(self._env), VID_CB(self._vid), AUD_CB(lambda l, r: None),
                     AUDB_CB(lambda d, n: n), POLL_CB(lambda: None), STATE_CB(self._state)]
        L = self.lib
        L.retro_set_environment(self._cbs[0]); L.retro_set_video_refresh(self._cbs[1])
        L.retro_set_audio_sample(self._cbs[2]); L.retro_set_audio_sample_batch(self._cbs[3])
        L.retro_set_input_poll(self._cbs[4]); L.retro_set_input_state(self._cbs[5])
        L.retro_init()
        self._rom = open(rom, 'rb').read()
        self._buf = C.create_string_buffer(self._rom, len(self._rom))
        gi = GameInfo(os.path.abspath(rom).encode(), C.cast(self._buf, C.c_void_p), len(self._rom), None)
        if not L.retro_load_game(C.byref(gi)):
            raise RuntimeError('core refused ROM')
        L.retro_get_memory_data.restype = C.c_void_p
        L.retro_get_memory_size.restype = C.c_size_t

    def _env(self, cmd, data):
        if cmd == 10:      # SET_PIXEL_FORMAT
            self.fmt = C.cast(data, C.POINTER(C.c_int))[0]; return True
        if cmd in (9, 31): # SYSTEM_DIRECTORY / SAVE_DIRECTORY
            C.cast(data, C.POINTER(C.c_char_p))[0] = self._sysdir.value; return True
        if cmd == 3:       # GET_CAN_DUPE
            C.cast(data, C.POINTER(C.c_bool))[0] = True; return True
        return False

    def _vid(self, data, w, h, pitch):
        if not data: return
        raw = C.string_at(data, pitch * h)
        fmt = getattr(self, 'fmt', 0)
        if fmt == 1:   # XRGB8888
            im = Image.frombuffer('RGBX', (w, h), raw, 'raw', 'BGRX', pitch, 1).convert('RGB')
        else:          # RGB565
            im = Image.frombuffer('RGB', (w, h), raw, 'raw', 'BGR;16', pitch, 1)
        self.frame = im

    def _state(self, port, device, index, bid):
        return 1 if port < 2 and bid in self.pressed[port] else 0

    def run(self, n=1):
        for _ in range(n): self.lib.retro_run()

    def press(self, buttons, frames=2, port=0, release=4):
        self.pressed[port] = {BTN[b] for b in buttons}
        self.run(frames)
        self.pressed[port] = set()
        self.run(release)

    def hold(self, buttons, port=0):
        self.pressed[port] = {BTN[b] for b in buttons}

    def memory(self, kind):
        """kind: 0 save RAM, 2 system WRAM, 3 VRAM"""
        p = self.lib.retro_get_memory_data(kind); n = self.lib.retro_get_memory_size(kind)
        return C.string_at(p, n) if p else b''

    def screenshot(self, path):
        self.frame.save(path)
        return self.frame


if __name__ == '__main__':
    e = Emu(sys.argv[1], sys.argv[2]); e.run(int(sys.argv[3]) if len(sys.argv) > 3 else 300)
    e.screenshot(sys.argv[4] if len(sys.argv) > 4 else 'shot.png')


def _serialize(self):
    n = self.lib.retro_serialize_size()
    buf = C.create_string_buffer(n)
    self.lib.retro_serialize(buf, n)
    return buf.raw

def _unserialize(self, data):
    buf = C.create_string_buffer(data, len(data))
    self.lib.retro_unserialize(buf, len(data))

Emu.save_state = _serialize   # dev convenience only; validation always boots fresh
Emu.load_state = _unserialize

def _trace(self, path=None, exec_=False):
    """Requires the instrumented core (tools/emulator/build_core.sh)."""
    self.lib.retro_mk_trace(path.encode() if path else None, int(exec_))
Emu.trace = _trace
