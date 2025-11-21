import struct
import zlib
from src.hardware.nand_controller import NANDController
from src.config.settings import config_manager

class FakeSerialBinary:
    def __init__(self, data_bytes: bytes):
        self._buf = bytearray(data_bytes)
        self.is_open = True
    def write(self, b: bytes):
        pass
    def flush(self):
        pass
    def reset_input_buffer(self):
        pass
    @property
    def in_waiting(self):
        return len(self._buf)
    def read(self, n: int) -> bytes:
        n = min(n, len(self._buf))
        out = bytes(self._buf[:n])
        del self._buf[:n]
        return out


def frame_pf(cmd: int, payload: bytes = b"") -> bytes:
    magic = b"PF"
    header = bytes([cmd]) + struct.pack('<I', len(payload))
    crc = zlib.crc32(header + payload) & 0xFFFFFFFF
    return magic + header + payload + struct.pack('<I', crc)


def test_erase_progress_saves_block(tmp_path, monkeypatch):
    monkeypatch.setattr(config_manager.settings, 'use_binary_protocol', True, raising=False)
    ctrl = NANDController()
    ctrl._resume_path = tmp_path / "resume.json"
    ctrl.current_nand_info = {"blocks": 100, "block_size": 1, "page_size": 2048}
    ctrl.is_connected = True

    # Build ERASE progress frames with block indices 0..2 and COMPLETE
    seq = bytearray()
    for block in range(3):
        percent = int((block + 1) * 100 / 100)
        payload = bytes([percent & 0xFF, (percent >> 8) & 0xFF]) + struct.pack('<I', block)
        seq += frame_pf(ctrl.CMD_PROGRESS, payload)
    seq += frame_pf(ctrl.CMD_COMPLETE)

    ctrl.ser = FakeSerialBinary(bytes(seq))
    ok = ctrl.erase_nand()
    assert ok is True
    state = ctrl.get_resume_state()
    assert state.get('operation') == 'ERASE'
    # Last saved block should be >= 2 because of last progress
    assert state.get('erase_block', 0) >= 2
