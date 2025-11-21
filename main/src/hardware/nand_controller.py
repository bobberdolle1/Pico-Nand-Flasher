"""
Hardware abstraction layer for NAND Flash operations
Provides a clean interface between the application logic and hardware communication
"""
import time
import struct
import zlib
import serial
from typing import Optional, Tuple, Dict, List
from pathlib import Path
import json
from ..utils.logging_config import get_logger
from ..utils.ecc import verify_and_correct
from ..config.settings import config_manager
from ..utils.exceptions import (
    ConnectionException, 
    NANDDetectionException, 
    ReadException, 
    WriteException, 
    EraseException,
    OperationException
)


class NANDController:
    """Hardware abstraction layer for NAND Flash operations"""
    
    def __init__(self):
        self.logger = get_logger()
        self.ser: Optional[serial.Serial] = None
        self.is_connected = False
        self.current_nand_info = None
        self.baudrate = config_manager.get('default_baudrate')
        self.timeout = config_manager.get('connection_timeout')
        self.use_binary = bool(config_manager.get('use_binary_protocol', False))
        # Resume state persistence
        self._resume_path = Path(config_manager.config_path).parent / "resume.json"
        # Framed protocol constants
        self.MAGIC = b'PF'  # Pico Flasher
        # Command codes
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
        
        # Supported NAND chips database
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
    
    def connect(self, port: str) -> bool:
        """
        Connect to the Pico device
        
        Args:
            port: Serial port to connect to
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.logger.info(f"Attempting to connect to {port} at {self.baudrate} baud")
            self.ser = serial.Serial(port, self.baudrate, timeout=self.timeout)
            self.ser.flush()
            
            # Small delay for stabilization
            time.sleep(2)
            # Clear input buffer in case of garbage data
            self.ser.reset_input_buffer()
            
            self.is_connected = True
            self.logger.info(f"Successfully connected to {port}")
            return True
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            self.is_connected = False
            raise ConnectionException(f"Failed to connect to {port}: {e}") from e
    
    def disconnect(self) -> None:
        """Disconnect from the Pico device"""
        if self.ser and self.ser.is_open:
            try:
                if self.use_binary:
                    # Send best-effort EXIT via legacy text for backward Pico compatibility
                    self.ser.write(b'EXIT\n')
                else:
                    self.ser.write(b'EXIT\n')
            except:
                pass
            self.ser.close()
            self.is_connected = False
            self.logger.info("Disconnected from device")

    # =====================
    # Framed protocol utils
    # =====================
    def _frame(self, cmd: int, payload: bytes = b"") -> bytes:
        """Build a framed packet: MAGIC(2) + CMD(1) + LEN(4 LE) + PAYLOAD + CRC32(4 LE). CRC over CMD+LEN+PAYLOAD."""
        header = struct.pack('<c', bytes([cmd])) + struct.pack('<I', len(payload))
        crc_input = header + payload
        crc = zlib.crc32(crc_input) & 0xFFFFFFFF
        frame = self.MAGIC + header + payload + struct.pack('<I', crc)
        return frame

    def _send_frame(self, cmd: int, payload: bytes = b"") -> None:
        if not self.ser:
            raise ConnectionException("Serial not connected")
        data = self._frame(cmd, payload)
        self.ser.write(data)

    def _read_exact(self, n: int, timeout: Optional[float] = None) -> Optional[bytes]:
        """Read exactly n bytes or return None on timeout."""
        if not self.ser:
            return None
        start = time.time()
        buf = bytearray()
        to = timeout or self.timeout
        while len(buf) < n and (time.time() - start) < to:
            if self.ser.in_waiting:
                chunk = self.ser.read(n - len(buf))
                if chunk:
                    buf.extend(chunk)
            else:
                time.sleep(0.005)
        return bytes(buf) if len(buf) == n else None

    def _read_frame(self, timeout: Optional[float] = None) -> Optional[Tuple[int, bytes]]:
        """Read one framed packet and verify CRC. Returns (cmd, payload) or None on timeout/error."""
        to = timeout or self.timeout
        start = time.time()
        # Seek MAGIC
        sync = b''
        while time.time() - start < to:
            b1 = self._read_exact(1, to)
            if not b1:
                return None
            sync = (sync + b1)[-2:]
            if sync == self.MAGIC:
                break
        else:
            return None
        # Read CMD(1) + LEN(4)
        header = self._read_exact(5, to)
        if not header:
            return None
        cmd = header[0]
        length = struct.unpack('<I', header[1:5])[0]
        # Read payload and CRC
        payload = self._read_exact(length, to) if length > 0 else b''
        if payload is None:
            return None
        crc_bytes = self._read_exact(4, to)
        if not crc_bytes:
            return None
        recv_crc = struct.unpack('<I', crc_bytes)[0]
        calc_crc = zlib.crc32(header + payload) & 0xFFFFFFFF
        if recv_crc != calc_crc:
            self.logger.warning("CRC mismatch in framed packet")
            return None
        return cmd, payload

    # =====================
    # Resume state helpers
    # =====================
    def _load_resume_state(self) -> Dict:
        try:
            if self._resume_path.exists():
                with open(self._resume_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load resume state: {e}")
        return {}

    def _save_resume_state(self, state: Dict) -> None:
        try:
            self._resume_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._resume_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save resume state: {e}")

    def get_resume_state(self) -> Dict:
        """Expose current resume state (or empty dict)."""
        return self._load_resume_state()

    def clear_resume_state(self) -> None:
        """Clear resume state file."""
        try:
            if self._resume_path.exists():
                self._resume_path.unlink()
        except Exception as e:
            self.logger.warning(f"Failed to clear resume state: {e}")
    
    def send_command(self, command: str) -> None:
        """
        Send a command to the Pico device
        
        Args:
            command: Command string to send
        """
        if not self.is_connected or not self.ser:
            self.logger.error("Not connected to device")
            return
        
        try:
            if self.use_binary:
                cmd_map = {
                    'STATUS': self.CMD_STATUS,
                    'READ': self.CMD_READ,
                    'WRITE': self.CMD_WRITE,
                    'ERASE': self.CMD_ERASE,
                }
                code = cmd_map.get(command)
                if code is None:
                    # Fall back to legacy text if unknown
                    command_bytes = f"{command}\n".encode('utf-8')
                    self.ser.write(command_bytes)
                else:
                    self._send_frame(code)
                    self.logger.debug(f"Sent framed command: {command}")
            else:
                command_bytes = f"{command}\n".encode('utf-8')
                self.ser.write(command_bytes)
                self.logger.debug(f"Sent command: {command}")
        except Exception as e:
            self.logger.error(f"Error sending command: {e}")
    
    def read_response(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Read a response from the Pico device
        
        Args:
            timeout: Optional timeout override
        
        Returns:
            Response string or None if timeout/error
        """
        if not self.is_connected or not self.ser:
            self.logger.error("Not connected to device")
            return None
        
        try:
            if self.use_binary:
                frame = self._read_frame(timeout)
                if frame is None:
                    self.logger.warning("Timeout waiting for framed response")
                    return None
                cmd, payload = frame
                # Map framed responses to string tags for current code until full refactor
                if cmd == self.CMD_PROGRESS:
                    try:
                        progress = int.from_bytes(payload[:2], 'little')
                    except Exception:
                        progress = 0
                    return f"PROGRESS:{progress}"
                if cmd == self.CMD_READY_FOR_DATA:
                    return "READY_FOR_DATA"
                if cmd == self.CMD_COMPLETE:
                    return "OPERATION_COMPLETE"
                if cmd == self.CMD_ERROR:
                    return "OPERATION_FAILED"
                if cmd == self.CMD_MODEL:
                    try:
                        model = payload.decode('utf-8', errors='ignore')
                    except Exception:
                        model = "UNKNOWN"
                    return f"MODEL:{model}"
                if cmd == self.CMD_POWER_WARNING:
                    msg = payload.decode('utf-8', errors='ignore')
                    return f"POWER_WARNING:{msg}"
                if cmd == self.CMD_PAGE_CRC:
                    # page CRC info is only used internally for resume validation; no string mapping
                    return None
                # Unknown framed message; log and ignore
                self.logger.debug(f"Unknown framed response cmd=0x{cmd:02X}, {len(payload)} bytes")
                return None
            else:
                start_time = time.time()
                timeout = timeout or self.timeout
                while time.time() - start_time < timeout:
                    if self.ser.in_waiting > 0:
                        response = self.ser.readline().decode('utf-8', errors='ignore').strip()
                        self.logger.debug(f"Received response: {response}")
                        return response
                    time.sleep(0.01)
                self.logger.warning("Timeout waiting for response")
                return None
        except Exception as e:
            self.logger.error(f"Error reading response: {e}")
            return None
    
    def detect_nand(self) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Detect connected NAND chip
        
        Returns:
            Tuple of (detected, model_name, nand_info)
        """
        self.logger.info("Detecting NAND chip...")
        
        if not self.is_connected:
            return False, None, None
        
        # Send STATUS command to check NAND status
        self.send_command("STATUS")
        
        response = self.read_response()
        if response and response.startswith("MODEL:"):
            model_name = response.split(":", 1)[1]
            nand_info = self.supported_nand.get(model_name)
            self.current_nand_info = nand_info
            self.logger.info(f"NAND detected: {model_name}")
            return True, model_name, nand_info
        
        self.logger.info("NAND not detected, manual selection may be required")
        return False, None, None
    
    def read_nand(self, progress_callback=None) -> Optional[bytes]:
        """
        Read data from NAND
        
        Args:
            progress_callback: Optional callback function for progress updates
            
        Returns:
            NAND data as bytes or None if failed
        """
        self.logger.info("Starting NAND read operation...")
        
        if not self.is_connected or not self.current_nand_info:
            self.logger.error("No connected NAND chip")
            return None
        
        self.send_command("READ")
        
        # Collect data and progress updates
        nand_data = bytearray()
        total_size = (self.current_nand_info["blocks"] * 
                     self.current_nand_info["block_size"] * 
                     self.current_nand_info["page_size"])
        
        self.logger.info(f"Reading {total_size} bytes from NAND")
        
        try:
            if self.use_binary:
                # In framed mode, expect a stream of DATA frames interleaved with PROGRESS and end with COMPLETE
                page_counter = 0
                resume = self._load_resume_state()
                # Determine if we should discard previously read bytes (resume)
                discard_pages = 0
                resume_last_page = 0
                resume_page_crc = None
                if resume.get("operation") == "READ" and self.current_nand_info:
                    resume_last_page = int(resume.get("last_page", 0))
                    discard_pages = resume_last_page
                    resume_page_crc = resume.get("page_crc32")
                page_size = self.current_nand_info["page_size"]
                spare_size = 128 if page_size == 4096 else 64
                page_total = page_size + spare_size
                bytes_to_discard = discard_pages * page_total
                while True:
                    frame = self._read_frame()
                    if not frame:
                        self.logger.error("No framed response from device")
                        return None
                    cmd, payload = frame
                    if cmd == self.CMD_PROGRESS:
                        # Payload layout v2.5+: [percent u16][optional u32 page_idx]
                        progress = int.from_bytes(payload[:2], 'little') if len(payload) >= 2 else 0
                        if progress_callback:
                            progress_callback(progress)
                        if len(payload) >= 6:
                            page_idx = int.from_bytes(payload[2:6], 'little')
                            resume.update({
                                "operation": "READ",
                                "last_page": page_idx,
                                "timestamp": time.time(),
                            })
                            self._save_resume_state(resume)
                    elif cmd == self.CMD_COMPLETE:
                        self.logger.info("NAND read completed successfully")
                        # Save final checkpoint
                        resume.update({
                            "operation": "READ",
                            "model": self.current_nand_info and "known" or "unknown",
                            "last_page": page_counter,
                            "timestamp": time.time(),
                        })
                        self._save_resume_state(resume)
                        break
                    elif cmd == self.CMD_ERROR:
                        self.logger.error("NAND read operation failed")
                        return None
                    elif cmd == self.CMD_PAGE_CRC:
                        # Payload layout: [page_idx u32][crc u32]
                        if len(payload) >= 8:
                            page_idx = int.from_bytes(payload[0:4], 'little')
                            crc = int.from_bytes(payload[4:8], 'little')
                            resume.update({
                                "operation": "READ",
                                "last_page": page_idx,
                                "page_crc32": crc,
                                "timestamp": time.time(),
                            })
                            self._save_resume_state(resume)
                            # Validate resume checkpoint when encountering stored last_page
                            if resume_page_crc is not None and page_idx == resume_last_page:
                                if int(resume_page_crc) != crc:
                                    self.logger.warning("Resume CRC mismatch for READ; restarting from beginning")
                                    # Reset resume and discard logic
                                    self.clear_resume_state()
                                    discard_pages = 0
                                    resume_last_page = 0
                                    resume_page_crc = None
                                    bytes_to_discard = 0
                                    nand_data = bytearray()
                    else:
                        # Treat any other cmd as raw data payload for now
                        # Optional ECC verification (no correction)
                        try:
                            if bool(config_manager.get('enable_ecc', False)) and self.current_nand_info:
                                page_size = self.current_nand_info["page_size"]
                                spare_size = 128 if page_size == 4096 else 64
                                page_total = page_size + spare_size
                                if len(payload) >= page_size:
                                    data_part = payload[:page_size]
                                    oob_part = payload[page_size:page_total] if len(payload) >= page_total else b""
                                    scheme = str(config_manager.get('ecc_scheme', 'crc16'))
                                    sector_size = int(config_manager.get('ecc_sector_size', 512))
                                    bytes_per_sector = int(config_manager.get('ecc_bytes_per_sector', 2))
                                    oob_offset = int(config_manager.get('ecc_oob_offset', 0))
                                    _, corrected = verify_and_correct(
                                        data_part,
                                        oob_part,
                                        scheme=scheme,
                                        sector_size=sector_size,
                                        bytes_per_sector=bytes_per_sector,
                                        oob_offset=oob_offset,
                                    )
                                    if corrected:
                                        self.logger.warning(f"ECC: errors detected sectors={corrected[:5]} ...")
                        except Exception:
                            # ECC is best-effort; ignore errors
                            pass

                        if bytes_to_discard > 0:
                            # Discard resumed portion
                            if len(payload) <= bytes_to_discard:
                                bytes_to_discard -= len(payload)
                                # do not append
                            else:
                                # append the remaining after discard
                                start = bytes_to_discard
                                nand_data.extend(payload[start:])
                                bytes_to_discard = 0
                        else:
                            nand_data.extend(payload)
                        # Save checkpoint periodically (every 64 pages)
                        page_counter += 1
                        if page_counter % 64 == 0:
                            crc = zlib.crc32(payload) & 0xFFFFFFFF
                            resume.update({
                                "operation": "READ",
                                "last_page": page_counter,
                                "page_crc32": crc,
                            })
                            self._save_resume_state(resume)
            else:
                while True:
                    response = self.read_response()
                    if not response:
                        self.logger.error("No response from device")
                        return None
                    if response.startswith("PROGRESS:"):
                        try:
                            progress = int(response.split(":")[1])
                            self.logger.debug(f"Read progress: {progress}%")
                            if progress_callback:
                                progress_callback(progress)
                        except ValueError:
                            pass
                    elif response == "OPERATION_COMPLETE":
                        self.logger.info("NAND read completed successfully")
                        break
                    elif response == "OPERATION_FAILED":
                        self.logger.error("NAND read operation failed")
                        return None
                    elif response == "NAND_NOT_CONNECTED":
                        self.logger.error("NAND not connected")
                        return None
                    else:
                        # Legacy fallback cannot reliably receive binary here; this path was already fragile
                        # We skip appending textual lines as data in v2.5
                        pass
        except Exception as e:
            self.logger.error(f"Error during NAND read: {e}")
            return None
        
        # Optionally strip OOB (spare) area from pages if not requested
        try:
            include_oob = bool(config_manager.get('include_oob', False))
            if (not include_oob) and self.current_nand_info and nand_data:
                page_size = self.current_nand_info["page_size"]
                spare_size = 128 if page_size == 4096 else 64
                page_total = page_size + spare_size
                if len(nand_data) % page_total == 0:
                    out = bytearray()
                    for i in range(0, len(nand_data), page_total):
                        out.extend(nand_data[i:i+page_size])
                    return bytes(out)
        except Exception:
            pass
        return bytes(nand_data)
    
    def write_nand(self, data: bytes, progress_callback=None) -> bool:
        """
        Write data to NAND
        
        Args:
            data: Data to write
            progress_callback: Optional callback function for progress updates
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Starting NAND write operation with {len(data)} bytes...")
        
        if not self.is_connected or not self.current_nand_info:
            self.logger.error("No connected NAND chip")
            return False
        
        self.send_command("WRITE")
        
        # Wait for ready signal
        ready_response = self.read_response()
        if ready_response != "READY_FOR_DATA":
            self.logger.error(f"Device not ready for data: {ready_response}")
            return False
        
        # Send data in chunks
        chunk_size = config_manager.get('chunk_size')
        total_size = len(data)
        
        resume = self._load_resume_state()
        start_offset = 0
        if resume.get("operation") == "WRITE":
            start_offset = int(resume.get("bytes_sent", 0))
            if start_offset > total_size:
                start_offset = 0
            # Validate CRC of last sent chunk; if mismatch, restart from zero
            last_crc = resume.get("chunk_crc32")
            chunk_size = config_manager.get('chunk_size')
            if last_crc is not None and start_offset >= chunk_size:
                prev_chunk = data[start_offset - chunk_size:start_offset]
                calc_crc = zlib.crc32(prev_chunk) & 0xFFFFFFFF
                if calc_crc != int(last_crc):
                    self.logger.warning("Resume CRC mismatch for WRITE; restarting from beginning")
                    start_offset = 0
                    self.clear_resume_state()
        for i in range(start_offset, total_size, chunk_size):
            chunk = data[i:i + chunk_size]
            try:
                if self.use_binary:
                    # Send data as framed packets with CMD_WRITE as data carrier
                    self._send_frame(self.CMD_WRITE, chunk)
                else:
                    self.ser.write(chunk)
            except Exception as e:
                self.logger.error(f"Error sending data chunk: {e}")
                return False
            
            # Calculate and report progress
            progress = int((i + len(chunk)) / total_size * 100)
            if progress_callback:
                progress_callback(progress)
            # Save checkpoint periodically (every 1MB)
            if (i % (1024 * 1024)) == 0:
                crc = zlib.crc32(chunk) & 0xFFFFFFFF
                resume.update({
                    "operation": "WRITE",
                    "bytes_sent": i + len(chunk),
                    "chunk_crc32": crc,
                    "timestamp": time.time(),
                })
                self._save_resume_state(resume)
        
        # Wait for completion
        while True:
            response = self.read_response()
            if not response:
                self.logger.error("No response from device")
                return False
            
            if response.startswith("PROGRESS:"):
                try:
                    progress = int(response.split(":")[1])
                    self.logger.debug(f"Write progress: {progress}%")
                    if progress_callback:
                        progress_callback(progress)
                except ValueError:
                    pass
            elif response == "OPERATION_COMPLETE":
                self.logger.info("NAND write completed successfully")
                return True
            elif response == "OPERATION_FAILED":
                self.logger.error("NAND write operation failed")
                return False
            elif response == "NAND_NOT_CONNECTED":
                self.logger.error("NAND not connected")
                return False
    
    def erase_nand(self, progress_callback=None) -> bool:
        """
        Erase NAND chip
        
        Args:
            progress_callback: Optional callback function for progress updates
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info("Starting NAND erase operation...")
        
        if not self.is_connected or not self.current_nand_info:
            self.logger.error("No connected NAND chip")
            return False
        
        self.send_command("ERASE")
        
        try:
            # Host-side ERASE resume handling by tracking progress
            resume = self._load_resume_state()
            last_block = int(resume.get("erase_block", 0)) if resume.get("operation") == "ERASE" else 0
            if self.use_binary:
                while True:
                    frame = self._read_frame()
                    if not frame:
                        self.logger.error("No framed response from device")
                        return False
                    cmd, payload = frame
                    if cmd == self.CMD_PROGRESS:
                        # Payload layout v2.5+: [percent u16][optional u32 block_idx]
                        progress = int.from_bytes(payload[:2], 'little') if len(payload) >= 2 else 0
                        if progress_callback:
                            progress_callback(progress)
                        if len(payload) >= 6:
                            block_idx = int.from_bytes(payload[2:6], 'little')
                            resume.update({"operation": "ERASE", "erase_block": block_idx, "timestamp": time.time()})
                            self._save_resume_state(resume)
                        elif self.current_nand_info:
                            total_blocks = self.current_nand_info["blocks"]
                            approx_block = int(progress * total_blocks / 100)
                            resume.update({"operation": "ERASE", "erase_block": approx_block, "timestamp": time.time()})
                            self._save_resume_state(resume)
                    elif cmd == self.CMD_COMPLETE:
                        self.logger.info("NAND erase completed successfully")
                        return True
                    elif cmd == self.CMD_ERROR:
                        self.logger.error("NAND erase operation failed")
                        return False
            else:
                while True:
                    response = self.read_response()
                    if not response:
                        self.logger.error("No response from device")
                        return False
                    if response.startswith("PROGRESS:"):
                        try:
                            progress = int(response.split(":")[1])
                            self.logger.debug(f"Erase progress: {progress}%")
                            if progress_callback:
                                progress_callback(progress)
                            if self.current_nand_info:
                                total_blocks = self.current_nand_info["blocks"]
                                approx_block = int(progress * total_blocks / 100)
                                resume.update({"operation": "ERASE", "erase_block": approx_block, "timestamp": time.time()})
                                self._save_resume_state(resume)
                        except ValueError:
                            pass
                    elif response == "OPERATION_COMPLETE":
                        self.logger.info("NAND erase completed successfully")
                        return True
                    elif response == "OPERATION_FAILED":
                        self.logger.error("NAND erase operation failed")
                        return False
                    elif response == "NAND_NOT_CONNECTED":
                        self.logger.error("NAND not connected")
                        return False
        except Exception as e:
            self.logger.error(f"Error during NAND erase: {e}")
            return False