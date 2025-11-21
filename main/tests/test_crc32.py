"""
Unit tests for CRC32 implementation in Pico NAND Flasher
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


class TestCRC32(unittest.TestCase):
    """Test CRC32 implementation"""

    def setUp(self):
        """Set up test fixture"""
        # Create NANDFlasher without calling __init__ to avoid hardware dependencies
        self.nand_flasher = object.__new__(NANDFlasher)
        # Initialize only the attributes we need for testing
        self.nand_flasher.use_compression = True
        self.nand_flasher.skip_blank_pages = True
        self.nand_flasher.last_block_position = 0
        self.nand_flasher.hash_chunks = {}

    def test_crc32_empty_data(self):
        """Test CRC32 calculation for empty data"""
        data = bytearray()
        expected_crc = 0x00000000  # CRC32 of empty data should be 0 according to zlib
        actual_crc = self.nand_flasher.calculate_chunk_hash(data)
        self.assertEqual(actual_crc, expected_crc)

    def test_crc32_single_byte(self):
        """Test CRC32 calculation for single byte"""
        # Test with known values
        data = bytearray([0x00])
        actual_crc = self.nand_flasher.calculate_chunk_hash(data)
        # Expected CRC32 for [0x00] is 0xD202EF8D according to zlib
        expected_crc = 0xD202EF8D
        self.assertEqual(actual_crc, expected_crc)

        # Test with another single byte
        data = bytearray([0xFF])
        actual_crc = self.nand_flasher.calculate_chunk_hash(data)
        # Expected CRC32 for [0xFF] is 0xFF000000 according to zlib
        expected_crc = 0xFF000000
        self.assertEqual(actual_crc, expected_crc)

    def test_crc32_known_data(self):
        """Test CRC32 calculation for known data"""
        # Test with "123456789" as a standard test case
        # In bytes, this is [0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39]
        data = bytearray([0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39])
        actual_crc = self.nand_flasher.calculate_chunk_hash(data)
        # Expected CRC32 for "123456789" is 0xCBF43926
        expected_crc = 0xCBF43926
        self.assertEqual(actual_crc, expected_crc)

    def test_crc32_multiple_bytes(self):
        """Test CRC32 calculation for multiple bytes"""
        data = bytearray([0xDE, 0xAD, 0xBE, 0xEF])
        actual_crc = self.nand_flasher.calculate_chunk_hash(data)
        # Expected CRC32 for [0xDE, 0xAD, 0xBE, 0xEF] is 0x7C9CA35A according to zlib
        expected_crc = 0x7C9CA35A
        self.assertEqual(actual_crc, expected_crc)

    def test_crc32_consistency(self):
        """Test that CRC32 is consistent for the same data"""
        data = bytearray([0x01, 0x02, 0x03, 0x04, 0x05])
        crc1 = self.nand_flasher.calculate_chunk_hash(data)
        crc2 = self.nand_flasher.calculate_chunk_hash(data)
        self.assertEqual(crc1, crc2)

    def test_crc32_different_data(self):
        """Test that different data produces different CRC32"""
        data1 = bytearray([0x01, 0x02, 0x03])
        data2 = bytearray([0x01, 0x02, 0x04])  # Different last byte
        crc1 = self.nand_flasher.calculate_chunk_hash(data1)
        crc2 = self.nand_flasher.calculate_chunk_hash(data2)
        self.assertNotEqual(crc1, crc2)


if __name__ == '__main__':
    unittest.main()
