"""
Unit tests for data compression functionality in Pico NAND Flasher
"""
import os
import sys
import unittest


# Mock MicroPython modules for testing
class MockPin:
    IN = 0
    OUT = 1
    PULL_UP = 2
    IRQ_FALLING = 4
    IRQ_RISING = 8

class MockUART:
    def __init__(self, *args, **kwargs):
        pass

class MockADC:
    def __init__(self, *args):
        pass

    def read_u16(self):
        return 32768  # Mock value

class MockFreq:
    pass

# Add the pico directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'pico'))

# Mock the modules before importing main_performance
sys.modules['machine'] = type(sys)('machine')
sys.modules['machine'].Pin = MockPin
sys.modules['machine'].UART = MockUART
sys.modules['machine'].ADC = MockADC
sys.modules['machine'].freq = MockFreq
sys.modules['machine'].mem32 = 0

sys.modules['uasyncio'] = type(sys)('uasyncio')
sys.modules['uasyncio'].create_task = lambda x: None
sys.modules['uasyncio'].run = lambda: None
sys.modules['uasyncio'].sleep = lambda x: None

sys.modules['rp2'] = type(sys)('rp2')
sys.modules['rp2'].PIO = type('PIO', (), {'OUT_LOW': 0, 'OUT_HIGH': 1})
sys.modules['rp2'].StateMachine = type('StateMachine', (), {
    'active': lambda x: None,
    'put': lambda x: None,
    'get': lambda: 0,
    'rx_fifo': lambda: 0
})
sys.modules['rp2'].asm_pio = lambda *args, **kwargs: lambda func: func

# Now import our module
from main_performance import NANDFlasher


class TestCompression(unittest.TestCase):
    """Test data compression functionality"""

    def setUp(self):
        """Set up test fixture"""
        # Create NANDFlasher without calling __init__ to avoid hardware dependencies
        self.nand_flasher = object.__new__(NANDFlasher)
        # Initialize only the attributes we need for testing
        self.nand_flasher.use_compression = True
        self.nand_flasher.skip_blank_pages = True
        self.nand_flasher.last_block_position = 0
        self.nand_flasher.hash_chunks = {}

    def test_compression_empty_data(self):
        """Test compression of empty data"""
        data = bytearray()
        compressed = self.nand_flasher.compress_data(data)
        self.assertEqual(data, compressed)  # Empty data should not be compressed

    def test_compression_small_data(self):
        """Test compression of small data (should not be compressed)"""
        data = bytearray([0x01, 0x02])  # Less than 10 bytes
        compressed = self.nand_flasher.compress_data(data)
        self.assertEqual(data, compressed)  # Small data should not be compressed

    def test_compression_no_repetition(self):
        """Test compression of data with no repetition"""
        data = bytearray([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A])
        compressed = self.nand_flasher.compress_data(data)
        self.assertEqual(data, compressed)  # No repetition, should not be compressed

    def test_compression_with_repetition(self):
        """Test compression of data with repetition"""
        # Create data with repeated bytes (more than 3 in a row to trigger compression)
        data = bytearray([0xFF] * 10)  # 10 repeated 0xFF bytes
        compressed = self.nand_flasher.compress_data(data)

        # Compressed data should be smaller
        self.assertLess(len(compressed), len(data))

        # First byte should be 0x00 (compression marker)
        self.assertEqual(compressed[0], 0x00)
        # Second byte should be count (10)
        self.assertEqual(compressed[1], 10)
        # Third byte should be the repeated value (0xFF)
        self.assertEqual(compressed[2], 0xFF)
        # Total length should be 3 for this simple RLE
        self.assertEqual(len(compressed), 3)

    def test_compression_mixed_data(self):
        """Test compression of mixed data (some repetition, some not)"""
        # Data: [0x01, 0x02] + [0xFF] * 5 + [0x03, 0x04]
        # This will have 5 repeated bytes which should trigger compression
        data = bytearray([0x01, 0x02] + [0xFF] * 5 + [0x03, 0x04])
        compressed = self.nand_flasher.compress_data(data)

        # The compressed data should be [0x01, 0x02, 0x00, 0x05, 0xFF, 0x03, 0x04] = 7 bytes
        # instead of [0x01, 0x02, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x03, 0x04] = 9 bytes
        # So it should be smaller
        self.assertLess(len(compressed), len(data))

    def test_decompression(self):
        """Test decompression of compressed data"""
        original_data = bytearray([0xFF] * 10)  # 10 repeated 0xFF bytes
        compressed = self.nand_flasher.compress_data(original_data)
        decompressed = self.nand_flasher.decompress_data(compressed)

        self.assertEqual(original_data, decompressed)

    def test_compression_decompression_roundtrip(self):
        """Test that compression followed by decompression gives original data"""
        test_cases = [
            # Non-repetitive data
            bytearray([0x01, 0x02, 0x03, 0x04, 0x05]),
            # Repetitive data
            bytearray([0xAA] * 10),
            # Mixed data
            bytearray([0x01, 0x02, 0x03] + [0xBB] * 7 + [0x04, 0x05]),
            # Edge case: exactly 3 repeated (should not compress)
            bytearray([0xCC] * 3 + [0x01]),
            # Edge case: exactly 4 repeated (should compress)
            bytearray([0xDD] * 4)
        ]

        for original_data in test_cases:
            compressed = self.nand_flasher.compress_data(original_data)
            decompressed = self.nand_flasher.decompress_data(compressed)
            self.assertEqual(original_data, decompressed,
                           f"Round-trip failed for data: {original_data.hex()}")

    def test_compression_disabled(self):
        """Test that compression is disabled when setting is off"""
        self.nand_flasher.use_compression = False
        data = bytearray([0xFF] * 10)  # This would normally be compressed
        compressed = self.nand_flasher.compress_data(data)

        # With compression disabled, data should remain unchanged
        self.assertEqual(data, compressed)


if __name__ == '__main__':
    unittest.main()
