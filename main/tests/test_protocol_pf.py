import struct

from src.config.settings import config_manager
from src.hardware.nand_controller import NANDController


class FakeSerialBinary:
    def __init__(self, data_bytes: bytes):
        self._buf = bytearray(data_bytes)
        self.is_open = True

    def write(self, b: bytes):
        # host writing to device not needed for this test
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
    header = bytes([cmd]) + struct.pack("<I", len(payload))
    import zlib

    crc = zlib.crc32(header + payload) & 0xFFFFFFFF
    return magic + header + payload + struct.pack("<I", crc)


def test_binary_progress_mapping(monkeypatch):
    # Enable binary protocol
    monkeypatch.setattr(config_manager.settings, "use_binary_protocol", True, raising=False)
    ctrl = NANDController()
    # Build a PROGRESS frame with percent=37
    payload = bytes([37, 0])
    data = frame_pf(ctrl.CMD_PROGRESS, payload)
    fake = FakeSerialBinary(data)
    ctrl.ser = fake
    ctrl.is_connected = True
    msg = ctrl.read_response()
    assert msg == "PROGRESS:37"


def test_model_mapping(monkeypatch):
    monkeypatch.setattr(config_manager.settings, "use_binary_protocol", True, raising=False)
    ctrl = NANDController()
    payload = b"Samsung K9F1G08U0A"
    data = frame_pf(ctrl.CMD_MODEL, payload)
    ctrl.ser = FakeSerialBinary(data)
    ctrl.is_connected = True
    msg = ctrl.read_response()
    assert msg.startswith("MODEL:")
    assert "Samsung" in msg
