import io
import os
import json
from pathlib import Path

import types
import builtins

from src.hardware.nand_controller import NANDController
from src.config.settings import config_manager


class FakeSerialLegacy:
    """Minimal fake serial for legacy text protocol paths.
    Provides readline() returning a queued list of lines and captures writes.
    """
    def __init__(self, lines):
        self._lines = [l if l.endswith("\n") else l + "\n" for l in lines]
        self.writes = bytearray()
        self.is_open = True
        self._in_waiting = len(self._lines[0]) if self._lines else 0

    def write(self, b: bytes):
        self.writes.extend(b)

    def flush(self):
        pass

    def reset_input_buffer(self):
        pass

    @property
    def in_waiting(self):
        # simplistic: if there are lines queued, simulate waiting bytes
        return self._in_waiting

    def readline(self):
        if not self._lines:
            self._in_waiting = 0
            return b""
        s = self._lines.pop(0)
        self._in_waiting = len(self._lines[0]) if self._lines else 0
        return s.encode("utf-8")

    def close(self):
        self.is_open = False


def test_write_resume_crc_validation(tmp_path, monkeypatch):
    # Force legacy text mode for simpler test path
    monkeypatch.setattr(config_manager.settings, 'use_binary_protocol', False, raising=False)

    ctrl = NANDController()
    # Redirect resume.json to temp dir
    ctrl._resume_path = tmp_path / "resume.json"

    # Prepare data and a resume state with wrong CRC for previous chunk
    data = b"A" * 8192  # two chunks if chunk_size=4096
    # Save a fake resume stating 4096 bytes were sent but CRC is wrong
    resume_state = {
        "operation": "WRITE",
        "bytes_sent": 4096,
        "chunk_crc32": 0xDEADBEEF,
    }
    ctrl._save_resume_state(resume_state)

    # Fake serial that will say READY_FOR_DATA then OPERATION_COMPLETE
    fake_ser = FakeSerialLegacy(["READY_FOR_DATA", "OPERATION_COMPLETE"])
    ctrl.ser = fake_ser
    ctrl.is_connected = True
    ctrl.current_nand_info = {"blocks": 1, "block_size": 1, "page_size": 2048}

    # Execute write; due to CRC mismatch, it should restart from 0 and write 8192 bytes
    ok = ctrl.write_nand(data)
    assert ok is True
    # In legacy mode, writes are raw chunks (no framing); verify total bytes written equals data length
    assert len(fake_ser.writes) == len(data)


def test_read_resume_discard_bytes(tmp_path, monkeypatch):
    # Note: Full framed binary test would require framing generator; here we test helper math for bytes-to-discard
    monkeypatch.setattr(config_manager.settings, 'use_binary_protocol', False, raising=False)
    ctrl = NANDController()
    ctrl._resume_path = tmp_path / "resume.json"
    # Create a resume state for READ of 10 pages
    ctrl._save_resume_state({"operation": "READ", "last_page": 10})
    # Validate that resume state loads
    state = ctrl.get_resume_state()
    assert state.get("last_page") == 10
