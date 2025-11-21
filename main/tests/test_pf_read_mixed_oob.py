import struct
import zlib

from src.config.settings import config_manager
from src.hardware.nand_controller import NANDController


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


def build_mixed_sequence(ctrl: NANDController, pages: int, page_len: int):
    data = bytearray()
    for page in range(pages):
        payload = bytes([(page + i) % 251 for i in range(page_len)])
        page_crc = zlib.crc32(payload) & 0xFFFFFFFF
        # Mixed order: sometimes PAGE_CRC -> PROGRESS -> DATA, sometimes PROGRESS -> DATA -> PAGE_CRC
        if page % 2 == 0:
            data += frame_pf(ctrl.CMD_PAGE_CRC, struct.pack('<II', page, page_crc))
            percent = int((page + 1) * 100 / pages)
            data += frame_pf(ctrl.CMD_PROGRESS, bytes([percent & 0xFF, (percent >> 8) & 0xFF]) + struct.pack('<I', page))
            data += frame_pf(ctrl.CMD_READ, payload)
        else:
            percent = int((page + 1) * 100 / pages)
            data += frame_pf(ctrl.CMD_PROGRESS, bytes([percent & 0xFF, (percent >> 8) & 0xFF]) + struct.pack('<I', page))
            data += frame_pf(ctrl.CMD_READ, payload)
            data += frame_pf(ctrl.CMD_PAGE_CRC, struct.pack('<II', page, page_crc))
    data += frame_pf(ctrl.CMD_COMPLETE, b"")
    return bytes(data)


def test_pf_read_mixed_frames(tmp_path, monkeypatch):
    monkeypatch.setattr(config_manager.settings, 'use_binary_protocol', True, raising=False)
    ctrl = NANDController()
    ctrl._resume_path = tmp_path / "resume.json"
    # Use small page geometry to keep payloads short and allow OOB stripping logic to be skipped here
    ctrl.current_nand_info = {"blocks": 1, "block_size": 2, "page_size": 64}
    ctrl.is_connected = True

    seq = build_mixed_sequence(ctrl, pages=3, page_len=32)
    ctrl.ser = FakeSerialBinary(seq)
    data = ctrl.read_nand()
    assert data is not None
    # We sent 3 DATA payloads of 32 bytes each, controller should accumulate them
    assert len(data) == 32 * 3


def test_oob_stripping(tmp_path, monkeypatch):
    monkeypatch.setattr(config_manager.settings, 'use_binary_protocol', True, raising=False)
    # Also ensure include_oob is False
    monkeypatch.setattr(config_manager.settings, 'include_oob', False, raising=False)

    ctrl = NANDController()
    ctrl._resume_path = tmp_path / "resume.json"
    # Tiny geometry to make test light-weight
    page_size = 4
    ctrl.current_nand_info = {"blocks": 1, "block_size": 2, "page_size": page_size}
    ctrl.is_connected = True

    # Build two pages with data (4 bytes) + OOB (2 bytes)
    pages = 2
    seq = bytearray()
    for page in range(pages):
        data_bytes = bytes([page, page+1, page+2, page+3])
        oob_bytes = b"\xEE\xEE"
        payload = data_bytes + oob_bytes
        # Send as DATA frame (treated as raw payload by host)
        seq += frame_pf(ctrl.CMD_READ, payload)
        # Add progress and CRC frames to complete flow
        percent = int((page + 1) * 100 / pages)
        seq += frame_pf(ctrl.CMD_PROGRESS, bytes([percent & 0xFF, (percent >> 8) & 0xFF]) + struct.pack('<I', page))
        page_crc = zlib.crc32(payload) & 0xFFFFFFFF
        seq += frame_pf(ctrl.CMD_PAGE_CRC, struct.pack('<II', page, page_crc))
    seq += frame_pf(ctrl.CMD_COMPLETE, b"")

    ctrl.ser = FakeSerialBinary(bytes(seq))
    data = ctrl.read_nand()
    assert data is not None
    # OOB stripping should remove 2 bytes per page from the end of each page
    # two pages * 4 data bytes = 8 bytes expected
    assert len(data) == pages * page_size
