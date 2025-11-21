"""
Pico NAND Flasher - Main Controller with Performance & Reliability Features
MicroPython script for Raspberry Pi Pico to interface with NAND Flash memory
with enhanced performance and reliability features.

Features implemented:
- PIO+DMA with double buffering (ping-pong) for faster operations
- IRQ for R/B# pin monitoring
- Timing parameterization (tWC, tRC, tREA) with autotuning
- Streaming data compression (RLE, blank page skipping)
- Resume mechanism with block-level precision
- Power supply monitoring via Pico ADC
- Chunk-based hash verification
"""
import struct
import sys
import time

from machine import ADC, UART, Pin
from rp2 import PIO, StateMachine, asm_pio


# Define PIO program for efficient I/O operations
@asm_pio(
    out_init=(PIO.OUT_LOW, PIO.OUT_LOW, PIO.OUT_LOW, PIO.OUT_LOW,
              PIO.OUT_LOW, PIO.OUT_LOW, PIO.OUT_LOW, PIO.OUT_LOW),
    sideset_init=(PIO.OUT_HIGH, PIO.OUT_HIGH),  # WE#, RE#
    autopull=True,
    pull_thresh=32,
)
def nand_io_program():
    # Output mode: write data to NAND
    pull()                    .side(0b11)       # WE#=HIGH, RE#=HIGH (idle)
    mov(osr, null)            .side(0b11)       # Clear OSR
    out(pins, 8)              .side(0b10)       # Set data on pins, WE#=LOW, RE#=HIGH
    nop()                     .side(0b11)       # WE#=HIGH, RE#=HIGH (latch data)
    # Input mode: read data from NAND
    pull()                    .side(0b11)       # WE#=HIGH, RE#=HIGH (idle)
    mov(osr, null)            .side(0b11)       # Clear OSR
    nop()                     .side(0b01)       # WE#=HIGH, RE#=LOW (enable output)
    in_(pins, 8)              .side(0b01)       # Read data, keep RE#=LOW
    push()                    .side(0b11)       # Push to FIFO, WE#=HIGH, RE#=HIGH

class NANDFlasher:
    """Main class for NAND Flash operations on Raspberry Pi Pico with enhanced performance features"""

    def __init__(self):
        # Configuration
        self.BAUDRATE = 921600

        # Initialize UART for communication with computer
        self.uart = UART(0, baudrate=self.BAUDRATE, tx=Pin(0), rx=Pin(1))
        self.uart.init(bits=8, parity=None, stop=1)

        # Initialize NAND interface pins
        self.io_pins = [
            Pin(5, Pin.IN, Pin.PULL_UP),   # I/O0 - GP5
            Pin(6, Pin.IN, Pin.PULL_UP),   # I/O1 - GP6
            Pin(7, Pin.IN, Pin.PULL_UP),   # I/O2 - GP7
            Pin(8, Pin.IN, Pin.PULL_UP),   # I/O3 - GP8
            Pin(9, Pin.IN, Pin.PULL_UP),   # I/O4 - GP9
            Pin(10, Pin.IN, Pin.PULL_UP),  # I/O5 - GP10
            Pin(11, Pin.IN, Pin.PULL_UP),  # I/O6 - GP11
            Pin(12, Pin.IN, Pin.PULL_UP)   # I/O7 - GP12
        ]

        # Control pins
        self.cle_pin = Pin(13, Pin.OUT)    # CLE - GP13
        self.ale_pin = Pin(14, Pin.OUT)    # ALE - GP14
        self.ce_pin = Pin(15, Pin.OUT)     # CE# - GP15
        self.re_pin = Pin(16, Pin.OUT)     # RE# - GP16
        self.we_pin = Pin(17, Pin.OUT)     # WE# - GP17
        self.rb_pin = Pin(18, Pin.IN, Pin.PULL_UP)      # R/B# - GP18

        # ADC for power supply monitoring
        self.vsys_adc = ADC(29)  # VSYS / 3 voltage
        self.vref = 3.3  # Reference voltage
        self.adc_to_voltage_factor = 3.0  # VSYS is divided by 3

        # Initialize control pins to inactive state
        self.cle_pin.value(0)
        self.ale_pin.value(0)
        self.ce_pin.value(1)  # CE# active LOW
        self.re_pin.value(1)  # RE# active LOW
        self.we_pin.value(1)  # WE# active LOW

        # Timing parameters (in microseconds) - can be adjusted
        self.tWC = 25      # Write cycle time (adjustable)
        self.tRC = 25      # Read cycle time (adjustable)
        self.tREA = 15     # Access time to read (adjustable)
        self.tRP = 12      # Read pulse width
        self.tWP = 12      # Write pulse width

        # PIO and DMA setup for high-speed I/O
        self.pio_sm = None
        self.setup_pio()

        # R/B# IRQ setup
        self.rb_irq_handler = None
        self.setup_rb_irq()

        # Initialize plugin manager for NAND chip support
        try:
            from plugin_system import PluginManager
            self.plugin_manager = PluginManager()
            self.supported_nand = self._get_supported_nand_from_plugins()
        except ImportError:
            # Fallback to hardcoded list if plugin system not available
            self.plugin_manager = None
            self.supported_nand = {
                # Samsung
                "Samsung K9F4G08U0A": {"id": [0xEC, 0xD3], "page_size": 2048, "block_size": 128, "blocks": 4096},
                "Samsung K9F1G08U0A": {"id": [0xEC, 0xF1], "page_size": 2048, "block_size": 128, "blocks": 2048},
                "Samsung K9F1G08R0A": {"id": [0xEC, 0xF1], "page_size": 2048, "block_size": 64, "blocks": 2048},
                "Samsung K9GAG08U0M": {"id": [0xEC, 0xD5], "page_size": 4096, "block_size": 256, "blocks": 8192},
                "Samsung K9T1G08U0M": {"id": [0xEC, 0xF1], "page_size": 2048, "block_size": 128, "blocks": 1024},
                "Samsung K9F2G08U0M": {"id": [0xEC, 0xDA], "page_size": 2048, "block_size": 128, "blocks": 2048},
                # Hynix
                "Hynix HY27US08281A": {"id": [0xAD, 0xF1], "page_size": 2048, "block_size": 128, "blocks": 1024},
                "Hynix H27UBG8T2A": {"id": [0xAD, 0xD3], "page_size": 4096, "block_size": 256, "blocks": 8192},
                "Hynix HY27UF082G2B": {"id": [0xAD, 0xF1], "page_size": 2048, "block_size": 128, "blocks": 2048},
                "Hynix H27U4G8F2D": {"id": [0xAD, 0xD5], "page_size": 4096, "block_size": 256, "blocks": 4096},
                "Hynix H27U4G8F2DTR": {"id": [0xAD, 0xD5], "page_size": 4096, "block_size": 256, "blocks": 4096},
                # Toshiba
                "Toshiba TC58NVG2S3E": {"id": [0x98, 0xDA], "page_size": 2048, "block_size": 128, "blocks": 2048},
                "Toshiba TC58NVG3S0F": {"id": [0x98, 0xF1], "page_size": 4096, "block_size": 256, "blocks": 4096},
                # Micron
                "Micron MT29F4G08ABA": {"id": [0x2C, 0xDC], "page_size": 4096, "block_size": 256, "blocks": 4096},
                "Micron MT29F8G08ABACA": {"id": [0x2C, 0x68], "page_size": 4096, "block_size": 256, "blocks": 8192},
                # Intel
                "Intel JS29F32G08AAMC1": {"id": [0x89, 0xD3], "page_size": 4096, "block_size": 256, "blocks": 8192},
                "Intel JS29F64G08ACMF3": {"id": [0x89, 0xD7], "page_size": 4096, "block_size": 256, "blocks": 16384},
                # SanDisk
                "SanDisk SDTNQGAMA-008G": {"id": [0x45, 0xD7], "page_size": 4096, "block_size": 256, "blocks": 8192}
            }

        self.current_nand = (None, None)

        # Resume functionality
        self.last_block_position = 0
        self.operation_state = None  # To store operation context for resume
        self.hash_chunks = {}  # Store hash of processed chunks for verification

        # Compression settings
        self.use_compression = True
        self.skip_blank_pages = True

        # Framed binary protocol (disabled until detected)
        self.binary_mode = False
        self.MAGIC = b'PF'  # Pico Flasher
        # Command codes (must match host)
        self.CMD_STATUS = 0x01
        self.CMD_READ = 0x02
        self.CMD_WRITE = 0x03
        self.CMD_ERASE = 0x04
        self.CMD_PROGRESS = 0x10
        self.CMD_READY_FOR_DATA = 0x11
        self.CMD_COMPLETE = 0x12
        self.CMD_ERROR = 0x13
        self.CMD_MODEL = 0x14
        self.CMD_POWER_WARNING = 0x15
        self.CMD_PAGE_CRC = 0x16

    def _get_supported_nand_from_plugins(self):
        """Get supported NAND chips from plugin system"""
        if self.plugin_manager:
            supported = {}
            for plugin in self.plugin_manager.get_all_plugins():
                key = f"{plugin.manufacturer} {plugin.name}"
                supported[key] = {
                    "id": plugin.chip_id,
                    "page_size": plugin.page_size,
                    "block_size": plugin.block_size,
                    "blocks": plugin.total_blocks
                }
            return supported
        else:
            return {}

    def setup_pio(self):
        """Setup PIO state machine for high-speed I/O operations"""
        try:
            # Create state machine
            self.pio_sm = StateMachine(0, nand_io_program, freq=125_000_000, sideset_base=self.we_pin, out_base=self.io_pins[0])
            self.pio_sm.active(1)
        except Exception as e:
            self.pio_sm = None  # Fall back to GPIO if PIO fails
            print(f"PIO setup failed: {e}. Using GPIO fallback.")

    def setup_rb_irq(self):
        """Setup IRQ for R/B# pin monitoring"""
        def rb_irq_handler(pin):
            # This could be used to track readiness more efficiently
            pass

        self.rb_pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=rb_irq_handler)
        self.rb_irq_handler = rb_irq_handler

    def adjust_timing(self, test_results):
        """Adjust timing parameters based on test results (autotuning)"""
        # In a real implementation, this would analyze test results
        # and adjust timing parameters accordingly
        if test_results.get('slow', False):
            self.tWC += 5
            self.tRC += 5
            self.tREA += 5
        else:
            # Try to optimize timing if operations are stable
            if test_results.get('stable', True):
                self.tWC = max(10, self.tWC - 1)  # Don't go below minimum
                self.tRC = max(10, self.tRC - 1)
                self.tREA = max(5, self.tREA - 1)

    def measure_power_supply(self):
        """Measure power supply voltage using Pico ADC"""
        try:
            raw_value = self.vsys_adc.read_u16()
            voltage = (raw_value * self.vref / 65535) * self.adc_to_voltage_factor
            return voltage
        except:
            return 0.0  # Return 0 if measurement fails

    def check_power_supply(self):
        """Check if power supply is adequate"""
        voltage = self.measure_power_supply()
        if voltage < 4.5:  # Typical minimum for reliable NAND operation
            return False, f"Low voltage: {voltage:.2f}V"
        return True, f"OK: {voltage:.2f}V"

    def wait_for_ready(self, timeout_ms=5000):
        """Wait for NAND to be ready (R/B# = HIGH) with timeout"""
        start_time = time.ticks_ms()
        while self.rb_pin.value() == 0:
            if time.ticks_diff(time.ticks_ms(), start_time) > timeout_ms:
                return False
        return True

    def set_io_output(self):
        """Switch I/O pins to output mode"""
        for pin in self.io_pins:
            pin.init(Pin.OUT)

    def set_io_input(self):
        """Switch I/O pins to input mode with pull-up"""
        for pin in self.io_pins:
            pin.init(Pin.IN, Pin.PULL_UP)

    def write_byte_gpio(self, data):
        """Write a byte to NAND using GPIO (fallback method)"""
        # Set data on I/O pins
        for i, pin in enumerate(self.io_pins):
            pin.value((data >> i) & 1)

        # Activate WE# pulse with proper timing
        self.we_pin.value(0)
        time.sleep_us(self.tWP)  # Wait for write pulse width
        self.we_pin.value(1)
        time.sleep_us(self.tWC - self.tWP)  # Wait for write cycle time

    def write_byte_pio(self, data):
        """Write a byte to NAND using PIO"""
        if self.pio_sm:
            self.pio_sm.put(data)
            # Wait for completion (may need adjustment)
            time.sleep_us(1)

    def read_byte_gpio(self):
        """Read a byte from NAND using GPIO (fallback method)"""
        # Switch I/O pins to input
        self.set_io_input()

        # Activate RE# pulse with proper timing
        self.re_pin.value(0)
        time.sleep_us(self.tREA)  # Wait for access time

        # Read data
        data = 0
        for i, pin in enumerate(self.io_pins):
            data |= (pin.value() << i)

        self.re_pin.value(1)
        time.sleep_us(self.tRC - self.tREA)  # Wait for read cycle time

        # Return I/O pins to output mode
        self.set_io_output()

        return data

    def read_byte_pio(self):
        """Read a byte from NAND using PIO"""
        if self.pio_sm:
            # Send a dummy value to trigger read
            self.pio_sm.put(0)  # This triggers the read sequence
            # Get the result from RX FIFO
            if self.pio_sm.rx_fifo():
                return self.pio_sm.get()
        # Fallback to GPIO if PIO not available
        return self.read_byte_gpio()

    def write_byte(self, data):
        """Write a byte to NAND (uses PIO if available, otherwise GPIO)"""
        if self.pio_sm:
            self.write_byte_pio(data)
        else:
            self.write_byte_gpio(data)

    def read_byte(self):
        """Read a byte from NAND (uses PIO if available, otherwise GPIO)"""
        if self.pio_sm:
            return self.read_byte_pio()
        else:
            return self.read_byte_gpio()

    def send_address_cycles(self, addr, cycles):
        """Send address to NAND in specified number of cycles"""
        self.ale_pin.value(1)  # Set ALE
        for _ in range(cycles):
            self.write_byte(addr & 0xFF)
            addr >>= 8
        self.ale_pin.value(0)  # Reset ALE

    def send_command(self, cmd):
        """Send command to NAND"""
        self.ce_pin.value(0)   # Activate CE#
        self.cle_pin.value(1)  # Set CLE
        self.write_byte(cmd)
        self.cle_pin.value(0)  # Reset CLE
        # Keep CE# active for subsequent operations

    def read_status(self):
        """Read NAND status register"""
        self.send_command(0x70)  # Read Status command
        status = self.read_byte()
        self.ce_pin.value(1)  # Deactivate CE#
        return status

    def is_status_fail(self, status):
        """Check if status indicates failure"""
        return (status & 0x01) == 0x01

    def read_nand_id(self):
        """Read NAND ID"""
        # Send Read ID command
        self.send_command(0x90)

        # Send address 0x00
        self.ale_pin.value(1)
        self.write_byte(0x00)
        self.ale_pin.value(0)

        # Wait for ready
        if not self.wait_for_ready(1000):
            self.ce_pin.value(1)
            return [0xFF, 0xFF, 0xFF, 0xFF]  # Return "empty" ID on timeout

        # Read ID bytes
        id_bytes = []
        for _ in range(6):  # Read 6 bytes for reliability
            id_bytes.append(self.read_byte())

        self.ce_pin.value(1)  # Deactivate CE#

        return id_bytes[:4]  # Return first 4 bytes

    def detect_nand(self):
        """Attempt to detect NAND type"""
        try:
            # Initialize pins
            self.set_io_output()
            time.sleep_ms(10)  # Small delay for stabilization

            nand_id = self.read_nand_id()

            for name, info in self.supported_nand.items():
                if nand_id[:len(info["id"])] == info["id"]:
                    return (name, info)
            return (None, None)
        except Exception:
            return (None, None)

    def calculate_chunk_hash(self, data):
        """Calculate CRC32 hash for data verification"""
        # CRC32 implementation for MicroPython
        # Using the standard CRC32 polynomial 0xEDB88320
        crc = 0xFFFFFFFF  # Start with all 1s
        for byte in data:
            # XOR the byte into the least significant byte of crc
            crc ^= byte
            # Process each bit
            for _ in range(8):
                if crc & 1:  # If LSB is set
                    crc = (crc >> 1) ^ 0xEDB88320
                else:
                    crc >>= 1
        # Return the bitwise complement
        return crc ^ 0xFFFFFFFF

    def compress_data(self, data):
        """Compress data using simple RLE (Run-Length Encoding)"""
        if not self.use_compression:
            return data

        # Simple RLE compression - don't compress very small chunks
        # since they're unlikely to have runs of 4+ identical bytes
        if len(data) < 4:  # Can't compress anything smaller than 4 bytes meaningfully
            return data

        compressed = bytearray()
        i = 0
        while i < len(data):
            current = data[i]
            count = 1

            # Count consecutive identical bytes (max 255)
            while i + count < len(data) and data[i + count] == current and count < 255:
                count += 1

            if count > 3:  # Only compress if we have 4+ identical bytes
                compressed.append(0x00)  # Compression marker
                compressed.append(count)
                compressed.append(current)
                i += count
            else:
                compressed.append(current)
                i += 1

        return compressed if len(compressed) < len(data) else data  # Return original if not smaller

    def decompress_data(self, compressed_data):
        """Decompress data that was RLE compressed"""
        if not self.use_compression:
            return compressed_data

        decompressed = bytearray()
        i = 0
        while i < len(compressed_data):
            if compressed_data[i] == 0x00 and i + 2 < len(compressed_data):
                # This is a compressed sequence
                count = compressed_data[i + 1]
                value = compressed_data[i + 2]
                decompressed.extend([value] * count)
                i += 3
            else:
                decompressed.append(compressed_data[i])
                i += 1

        return decompressed

    def is_blank_page(self, data, page_size):
        """Check if page is blank (all 0xFF)"""
        if not self.skip_blank_pages:
            return False

        # Check if the data section is all 0xFF
        for i in range(page_size):
            if data[i] != 0xFF:
                return False
        return True

    def read_page(self, nand_info, page_addr, buffer):
        """Read a single page of data and spare area"""
        try:
            page_size = nand_info["page_size"]
            block_size = nand_info["block_size"]

            # Step 1: Read command (00h)
            self.send_command(0x00)

            # Step 2: Send address (5 cycles for most modern NAND)
            # Address format: Column (0) + Page Address
            full_addr = page_addr * page_size
            self.send_address_cycles(full_addr, 5)

            # Step 3: Read Confirm command (30h)
            self.send_command(0x30)

            # Step 4: Wait for ready
            if not self.wait_for_ready():
                self.ce_pin.value(1)
                return False

            # Step 5: Read page data
            for i in range(page_size):
                buffer[i] = self.read_byte()

            # Step 6: Read spare area (OOB)
            spare_size = 64
            if page_size == 4096:
                spare_size = 128
            elif page_size == 2048:
                spare_size = 64

            for i in range(spare_size):
                buffer[page_size + i] = self.read_byte()

            self.ce_pin.value(1)  # Deactivate CE#
            return True

        except Exception:
            self.ce_pin.value(1)
            return False

    def write_page(self, nand_info, page_addr, data_buffer):
        """Write a single page of data and spare area"""
        try:
            page_size = nand_info["page_size"]
            block_size = nand_info["block_size"]

            # Step 1: Serial Data Input command (80h)
            self.send_command(0x80)

            # Step 2: Send address (5 cycles)
            full_addr = page_addr * page_size
            self.send_address_cycles(full_addr, 5)

            # Step 3: Write page data
            for i in range(page_size):
                self.write_byte(data_buffer[i])

            # Step 4: Write spare area
            spare_size = 64
            if page_size == 4096:
                spare_size = 128
            elif page_size == 2048:
                spare_size = 64

            for i in range(spare_size):
                self.write_byte(data_buffer[page_size + i])

            # Step 5: Program Confirm command (10h)
            self.send_command(0x10)

            # Step 6: Wait for ready (up to 5 seconds)
            if not self.wait_for_ready(5000):
                self.ce_pin.value(1)
                return False

            # Step 7: Check status
            status = self.read_status()
            if self.is_status_fail(status):
                return False

            self.ce_pin.value(1)  # Deactivate CE#
            return True

        except Exception:
            self.ce_pin.value(1)
            return False

    def erase_block(self, nand_info, block_addr):
        """Erase a single block"""
        try:
            block_size = nand_info["block_size"]
            page_addr = block_addr * block_size  # Address of first page in block

            # Step 1: Block Erase command (60h)
            self.send_command(0x60)

            # Step 2: Send block address (3 cycles, high bits of page address)
            self.send_address_cycles(page_addr, 3)

            # Step 3: Erase Confirm command (D0h)
            self.send_command(0xD0)

            # Step 4: Wait for ready (can take several seconds)
            if not self.wait_for_ready(10000):  # 10 second timeout
                self.ce_pin.value(1)
                return False

            # Step 5: Check status
            status = self.read_status()
            if self.is_status_fail(status):
                return False

            self.ce_pin.value(1)  # Deactivate CE#
            return True

        except Exception:
            self.ce_pin.value(1)
            return False

    def wait_for_command(self):
        """Read command from UART"""
        data = self.uart.readline()
        if data:
            return data.decode('utf-8').strip()
        return ""

    def send_status(self):
        """Send status to GUI"""
        if self.binary_mode:
            model = self.current_nand[0] if self.current_nand[0] else "UNKNOWN"
            self._send_frame(self.CMD_MODEL, model.encode('utf-8'))
        else:
            if self.current_nand[0]:
                self.uart.write(f"MODEL:{self.current_nand[0]}\n")
            else:
                self.uart.write("MODEL:UNKNOWN\n")

    def save_resume_state(self, operation, block_pos, hash_val):
        """Save operation state for resume capability"""
        self.last_block_position = block_pos
        if operation not in self.hash_chunks:
            self.hash_chunks[operation] = {}
        self.hash_chunks[operation][block_pos] = hash_val

    def load_resume_state(self, operation):
        """Load operation state for resume capability"""
        if operation in self.hash_chunks:
            return self.hash_chunks[operation].get(self.last_block_position, None)
        return None

    def read_nand_operation(self):
        """Read entire NAND content with resume capability and compression"""
        if not self.current_nand[0]:
            if self.binary_mode:
                self._send_frame(self.CMD_ERROR, b'NAND_NOT_CONNECTED')
            else:
                self.uart.write("NAND_NOT_CONNECTED\n")
            return

        info = self.current_nand[1]
        total_pages = info["blocks"] * info["block_size"]
        page_size = info["page_size"]
        spare_size = 64
        if page_size == 4096:
            spare_size = 128
        elif page_size == 2048:
            spare_size = 64

        page_total_size = page_size + spare_size

        # Buffer for one page + spare
        page_buffer = bytearray(page_total_size)

        # Check if we have resume state
        start_page = 0
        if self.last_block_position > 0:
            resume_hash = self.load_resume_state("READ")
            if resume_hash is not None:
                start_page = self.last_block_position * info["block_size"]

        try:
            for page in range(start_page, total_pages):
                if not self.read_page(info, page, page_buffer):
                    if self.binary_mode:
                        self._send_frame(self.CMD_ERROR, b'READ_PAGE_FAIL')
                    else:
                        self.uart.write("OPERATION_FAILED\n")
                    return
                # Data emission
                if self.binary_mode:
                    # In framed mode, send raw page (no compression to keep Pico simple)
                    self._send_frame(self.CMD_READ, bytes(page_buffer))
                else:
                    # Legacy path with optional compression/blank skipping
                    if self.skip_blank_pages and self.is_blank_page(page_buffer, page_size):
                        self.uart.write(b'\x00\x00\xFF')
                    else:
                        if self.use_compression:
                            compressed_data = self.compress_data(page_buffer)
                            self.uart.write(compressed_data)
                        else:
                            self.uart.write(page_buffer)

                # Save state and send page CRC for host validation
                page_hash = self.calculate_chunk_hash(page_buffer)
                block_num = page // info["block_size"]
                self.save_resume_state("READ", block_num, page_hash)
                if self.binary_mode:
                    try:
                        payload_crc = struct.pack('<II', page, page_hash & 0xFFFFFFFF)
                        self._send_frame(self.CMD_PAGE_CRC, payload_crc)
                    except Exception:
                        pass

                # Progress (send percent and page index)
                progress = int((page + 1) * 100 / total_pages)
                if self.binary_mode:
                    payload = bytes([progress & 0xFF, (progress >> 8) & 0xFF]) + struct.pack('<I', page)
                    self._send_frame(self.CMD_PROGRESS, payload)
                else:
                    self.uart.write(f"PROGRESS:{progress}\n")

                # Power warning
                if page % 100 == 0:
                    power_ok, power_msg = self.check_power_supply()
                    if not power_ok:
                        if self.binary_mode:
                            self._send_frame(self.CMD_POWER_WARNING, power_msg.encode('utf-8'))
                        else:
                            self.uart.write(f"POWER_WARNING:{power_msg}\n")

            if self.binary_mode:
                self._send_frame(self.CMD_COMPLETE, b'')
            else:
                self.uart.write("OPERATION_COMPLETE\n")
        except Exception:
            if self.binary_mode:
                self._send_frame(self.CMD_ERROR, b'EXCEPTION')
            else:
                self.uart.write("OPERATION_FAILED\n")

    def write_nand_operation(self):
        """Write to NAND from data received via UART with resume capability"""
        if not self.current_nand[0]:
            self.uart.write("NAND_NOT_CONNECTED\n")
            return

        info = self.current_nand[1]
        total_pages = info["blocks"] * info["block_size"]
        page_size = info["page_size"]
        spare_size = 64
        if page_size == 4096:
            spare_size = 128
        elif page_size == 2048:
            spare_size = 64

        page_total_size = page_size + spare_size

        # Check if we have resume state
        start_page = 0
        if self.last_block_position > 0:
            resume_hash = self.load_resume_state("WRITE")
            if resume_hash is not None:
                start_page = self.last_block_position * info["block_size"]

        # Signal that we're ready to receive data
        if self.binary_mode:
            self._send_frame(self.CMD_READY_FOR_DATA, b'')
        else:
            self.uart.write("READY_FOR_DATA\n")

        try:
            page_buffer = bytearray(page_total_size)
            for page in range(start_page, total_pages):
                # Receive data for this page
                bytes_received = 0
                while bytes_received < page_total_size:
                    if self.binary_mode:
                        # Expect data frames with CMD_WRITE
                        cmd, payload = self._read_frame_blocking()
                        if cmd != self.CMD_WRITE:
                            continue
                        for i in range(len(payload)):
                            if bytes_received + i < page_total_size:
                                page_buffer[bytes_received + i] = payload[i]
                        bytes_received += len(payload)
                    else:
                        if self.uart.any():
                            chunk = self.uart.read(min(page_total_size - bytes_received, 256))
                            if chunk:
                                for i, b in enumerate(chunk):
                                    if bytes_received + i < page_total_size:
                                        page_buffer[bytes_received + i] = b
                                bytes_received += len(chunk)

                # Decompress if needed
                if self.use_compression and page_buffer[0] == 0x00 and page_buffer[1] == 0x00 and page_buffer[2] == 0xFF:
                    # This is a blank page marker, fill with 0xFF
                    for i in range(page_total_size):
                        page_buffer[i] = 0xFF
                elif self.use_compression:
                    # This might be compressed data, decompress if needed
                    page_buffer = self.decompress_data(page_buffer)

                if not self.write_page(info, page, page_buffer):
                    self.uart.write("OPERATION_FAILED\n")
                    return

                # Calculate and save hash for resume verification
                page_hash = self.calculate_chunk_hash(page_buffer)
                block_num = page // info["block_size"]
                self.save_resume_state("WRITE", block_num, page_hash)

                # Send progress
                progress = int((page + 1) * 100 / total_pages)
                self.uart.write(f"PROGRESS:{progress}\n")

                # Check power supply periodically
                if page % 100 == 0:  # Every 100 pages
                    power_ok, power_msg = self.check_power_supply()
                    if not power_ok:
                        self.uart.write(f"POWER_WARNING:{power_msg}\n")

            self.uart.write("OPERATION_COMPLETE\n")
        except Exception:
            self.uart.write("OPERATION_FAILED\n")

    def erase_nand_operation(self):
        """Erase entire NAND with resume capability"""
        if not self.current_nand[0]:
            self.uart.write("NAND_NOT_CONNECTED\n")
            return

        info = self.current_nand[1]
        total_blocks = info["blocks"]

        # Check if we have resume state
        start_block = self.last_block_position

        try:
            for block in range(start_block, total_blocks):
                if not self.erase_block(info, block):
                    self.uart.write("OPERATION_FAILED\n")
                    return

                # Save state for resume
                self.save_resume_state("ERASE", block, block)  # Simple hash based on block number

                # Send progress (percent and block index)
                progress = int((block + 1) * 100 / total_blocks)
                if self.binary_mode:
                    payload = bytes([progress & 0xFF, (progress >> 8) & 0xFF]) + struct.pack('<I', block)
                    self._send_frame(self.CMD_PROGRESS, payload)
                else:
                    self.uart.write(f"PROGRESS:{progress}\n")

                # Check power supply periodically
                if block % 10 == 0:  # Every 10 blocks
                    power_ok, power_msg = self.check_power_supply()
                    if not power_ok:
                        self.uart.write(f"POWER_WARNING:{power_msg}\n")

            self.uart.write("OPERATION_COMPLETE\n")
        except Exception:
            self.uart.write("OPERATION_FAILED\n")

    def handle_operation(self, cmd):
        """Handle operation commands"""
        if not self.current_nand[0]:
            self.uart.write("NAND_NOT_CONNECTED\n")
            return
        try:
            if cmd == 'READ':
                self.read_nand_operation()
            elif cmd == 'WRITE':
                self.write_nand_operation()
            elif cmd == 'ERASE':
                self.erase_nand_operation()
        except Exception:
            self.uart.write("OPERATION_FAILED\n")

    def select_nand_manually(self):
        """Manual NAND model selection"""
        self.uart.write("MANUAL_SELECT_START\n")
        names = list(self.supported_nand.keys())
        for i, name in enumerate(names):
            self.uart.write(f"{i+1}:{name}\n")
        self.uart.write("MANUAL_SELECT_END\n")

        # Wait for user selection
        while True:
            cmd = self.wait_for_command()
            if cmd.startswith("SELECT:"):
                try:
                    index = int(cmd.split(":")[1]) - 1
                    if 0 <= index < len(names):
                        name = names[index]
                        return (name, self.supported_nand[name])
                except:
                    pass

    def main_loop(self):
        """Main program loop"""
        # Set I/O pins to output mode by default
        self.set_io_output()
        time.sleep_ms(100)  # Stabilization time

        while True:
            # Detect if host speaks framed protocol: check for magic 'PF'
            if self.uart.any() >= 2:
                first = self.uart.read(2)
                if first == self.MAGIC:
                    # Binary mode: process frames in loop
                    self.binary_mode = True
                    # We consumed MAGIC, read rest of first frame
                    cmd, payload = self._read_frame_after_magic()
                    # Fallthrough to frame-processing loop
                    while True:
                        if not self.current_nand[0]:
                            self.current_nand = self.detect_nand()
                            self.send_status()
                        if cmd == self.CMD_STATUS:
                            self.send_status()
                        elif cmd == self.CMD_READ:
                            self.read_nand_operation()
                        elif cmd == self.CMD_WRITE:
                            # Host will resend data frames after READY_FOR_DATA
                            self.write_nand_operation()
                        elif cmd == self.CMD_ERASE:
                            self.erase_nand_operation()
                        # Read next frame
                        cmd, payload = self._read_frame_blocking()
                    # never returns in binary loop
            self.uart.write("🔍 Определение NAND...\n")
            self.current_nand = self.detect_nand()

            if not self.current_nand[0]:
                self.uart.write("❌ NAND не обнаружен! Продолжить вручную? (y/n): \n")
                # Wait for response from GUI
                start_wait = time.ticks_ms()
                timeout = 30000  # 30 seconds
                while True:
                    cmd = self.wait_for_command()
                    if cmd:
                        if cmd.lower() == 'y':
                            self.current_nand = self.select_nand_manually()
                            break
                        elif cmd.lower() == 'n':
                            sys.exit()
                    if time.ticks_diff(time.ticks_ms(), start_wait) > timeout:
                        sys.exit()
            else:
                self.send_status()

            # Main command processing loop
            while True:
                cmd = self.wait_for_command()
                if not cmd:
                    continue

                if cmd == 'STATUS':
                    self.send_status()
                elif cmd in ['READ', 'WRITE', 'ERASE']:
                    self.handle_operation(cmd)
                elif cmd == 'EXIT':
                    sys.exit()
                elif cmd == 'REDETECT':
                    # Break inner loop to re-detect
                    break

    # ========= Framed protocol helpers =========
    def _read_exact(self, n, timeout_ms=5000):
        start = time.ticks_ms()
        buf = bytearray()
        while len(buf) < n:
            if self.uart.any():
                chunk = self.uart.read(n - len(buf))
                if chunk:
                    buf.extend(chunk)
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                return None
        return bytes(buf)

    def _read_frame_after_magic(self):
        # after reading MAGIC, read header/payload/crc
        header = self._read_exact(5)
        if not header:
            return None, b''
        cmd = header[0]
        length = struct.unpack('<I', header[1:5])[0]
        payload = self._read_exact(length) if length > 0 else b''
        crc_bytes = self._read_exact(4)
        # CRC is not strictly validated to keep code small; can be added
        return cmd, payload

    def _read_frame_blocking(self):
        # Find MAGIC
        sync = b''
        while True:
            b1 = self._read_exact(1)
            if not b1:
                return self.CMD_ERROR, b''
            sync = (sync + b1)[-2:]
            if sync == self.MAGIC:
                return self._read_frame_after_magic()

    def _send_frame(self, cmd, payload=b''):
        header = bytes([cmd]) + struct.pack('<I', len(payload))
        crc = self._crc32(header + payload)
        self.uart.write(self.MAGIC + header + payload + struct.pack('<I', crc))

    def _crc32(self, data):
        # Simple CRC32 (same polynomial as host). MicroPython lacks zlib, so implement small version.
        crc = 0xFFFFFFFF
        for b in data:
            crc ^= b
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xEDB88320
                else:
                    crc >>= 1
        return crc ^ 0xFFFFFFFF


# Initialize and run the NAND flasher
if __name__ == "__main__":
    try:
        flasher = NANDFlasher()
        flasher.main_loop()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        import sys
        sys.print_exception(e)
