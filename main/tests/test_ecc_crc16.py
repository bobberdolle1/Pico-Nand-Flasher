"""
Unit tests for CRC16-based ECC scheme verification (no correction)
"""
import unittest
import os

from src.utils.ecc import verify_and_correct, _crc16_ccitt


class TestEccCRC16(unittest.TestCase):
    def test_crc16_match_simple(self):
        # Simple data buffer
        data = bytes(range(256)) * 8  # 2048 bytes
        crc = _crc16_ccitt(data)
        oob = crc.to_bytes(2, 'little') + b"\xFF" * 62
        out, errors = verify_and_correct(
            data,
            oob,
            scheme="crc16",
        )
        self.assertEqual(out, data)
        self.assertEqual(errors, [])

    def test_crc16_mismatch_simple(self):
        data = bytes(range(256)) * 8  # 2048 bytes
        crc = _crc16_ccitt(data)
        # Corrupt the stored CRC in OOB
        oob = ((crc ^ 0x1234) & 0xFFFF).to_bytes(2, 'little') + b"\xFF" * 62
        out, errors = verify_and_correct(
            data,
            oob,
            scheme="crc16",
        )
        self.assertEqual(out, data)
        self.assertEqual(errors, [-1])

    def test_crc16_page_layout(self):
        # Simulate page data and spare region as Analyzer would pass
        page_size = 2048
        spare_size = 64
        page = os.urandom(page_size)
        crc = _crc16_ccitt(page)
        spare = crc.to_bytes(2, 'little') + b"\xFF" * (spare_size - 2)
        # Analyzer calls verify_and_correct(data=page, oob=spare, scheme='crc16')
        _, errors = verify_and_correct(page, spare, scheme="crc16")
        self.assertEqual(errors, [])
        # Now flip one byte in page; CRC should not match stored
        corrupt = bytearray(page)
        corrupt[0] ^= 0x01
        _, errors2 = verify_and_correct(bytes(corrupt), spare, scheme="crc16")
        self.assertEqual(errors2, [-1])


@unittest.skip("Enable after real Hamming(512)->3-byte ECC is implemented")
class TestEccHamming512Scaffold(unittest.TestCase):
    def test_hamming_512_placeholder(self):
        # Placeholder scaffold for future real Hamming verifier tests
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
