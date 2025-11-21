"""
Data integrity verification module for Pico NAND Flasher
Provides checksum and verification capabilities for data validation
"""

import hashlib
import zlib
from pathlib import Path
from typing import Tuple, Union


class DataIntegrity:
    """Data integrity verification utilities"""

    @staticmethod
    def calculate_md5(data: Union[bytes, str]) -> str:
        """
        Calculate MD5 checksum of data

        Args:
            data: Input data as bytes or string

        Returns:
            MD5 checksum as hexadecimal string
        """
        if isinstance(data, str):
            data = data.encode("utf-8")

        md5_hash = hashlib.md5()
        md5_hash.update(data)
        return md5_hash.hexdigest()

    @staticmethod
    def calculate_sha256(data: Union[bytes, str]) -> str:
        """
        Calculate SHA-256 checksum of data

        Args:
            data: Input data as bytes or string

        Returns:
            SHA-256 checksum as hexadecimal string
        """
        if isinstance(data, str):
            data = data.encode("utf-8")

        sha256_hash = hashlib.sha256()
        sha256_hash.update(data)
        return sha256_hash.hexdigest()

    @staticmethod
    def calculate_crc32(data: Union[bytes, str]) -> int:
        """
        Calculate CRC32 checksum of data

        Args:
            data: Input data as bytes or string

        Returns:
            CRC32 checksum as integer
        """
        if isinstance(data, str):
            data = data.encode("utf-8")

        return zlib.crc32(data) & 0xFFFFFFFF

    @staticmethod
    def verify_file_integrity(
        file_path: Union[str, Path], expected_checksum: str, algorithm: str = "md5"
    ) -> Tuple[bool, str]:
        """
        Verify the integrity of a file against an expected checksum

        Args:
            file_path: Path to the file to verify
            expected_checksum: Expected checksum value
            algorithm: Algorithm to use ('md5', 'sha256', 'crc32')

        Returns:
            Tuple of (is_valid, actual_checksum)
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File does not exist: {file_path}")

        with open(file_path, "rb") as f:
            data = f.read()

        if algorithm.lower() == "md5":
            actual_checksum = DataIntegrity.calculate_md5(data)
        elif algorithm.lower() == "sha256":
            actual_checksum = DataIntegrity.calculate_sha256(data)
        elif algorithm.lower() == "crc32":
            actual_checksum = format(DataIntegrity.calculate_crc32(data), "08x")
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        is_valid = actual_checksum.lower() == expected_checksum.lower()
        return is_valid, actual_checksum

    @staticmethod
    def compare_files(file1_path: Union[str, Path], file2_path: Union[str, Path]) -> bool:
        """
        Compare two files for equality using checksums

        Args:
            file1_path: Path to first file
            file2_path: Path to second file

        Returns:
            True if files are identical, False otherwise
        """
        file1_path = Path(file1_path)
        file2_path = Path(file2_path)

        if not file1_path.exists() or not file2_path.exists():
            return False

        # For large files, we can compare checksums instead of reading entire files
        try:
            checksum1 = DataIntegrity.calculate_md5(file1_path.read_bytes())
            checksum2 = DataIntegrity.calculate_md5(file2_path.read_bytes())
            return checksum1 == checksum2
        except Exception:
            # If reading entire files is not feasible, we can implement chunked comparison
            return DataIntegrity._compare_files_chunked(file1_path, file2_path)

    @staticmethod
    def _compare_files_chunked(file1_path: Path, file2_path: Path, chunk_size: int = 8192) -> bool:
        """
        Compare two files chunk by chunk to handle large files efficiently

        Args:
            file1_path: Path to first file
            file2_path: Path to second file
            chunk_size: Size of chunks to read at a time

        Returns:
            True if files are identical, False otherwise
        """
        if file1_path.stat().st_size != file2_path.stat().st_size:
            return False

        try:
            with open(file1_path, "rb") as f1, open(file2_path, "rb") as f2:
                while True:
                    chunk1 = f1.read(chunk_size)
                    chunk2 = f2.read(chunk_size)

                    if chunk1 != chunk2:
                        return False

                    if not chunk1:  # End of file
                        break

            return True
        except Exception:
            return False
