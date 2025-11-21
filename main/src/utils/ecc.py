

def _crc16_ccitt(data: bytes, poly: int = 0x1021, init: int = 0xFFFF) -> int:
    """Compute CRC16-CCITT over data (standard variant)."""
    crc = init
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) & 0xFFFF) ^ poly
            else:
                crc = (crc << 1) & 0xFFFF
    return crc & 0xFFFF


def _calc_hamming_512_3byte(buf: bytes) -> bytes:
    """Compute 3-byte Hamming ECC for a 512-byte sector (ONFI/vendor-common).

    Algorithm adapted from Linux MTD documentation for 512-byte sectors (3 ECC bytes):
    - Accumulate row/column parities across 512 bytes (or 64 32-bit words)
    - Build 24 parity bits arranged into 3 bytes
    - Invert bytes so that blank (0xFF-filled) sectors yield 0xFF 0xFF 0xFF

    Returns ECC as 3 raw bytes (little-endian storage agnostic; compare as bytes).
    """
    # Ensure 512 bytes input (pad with 0x00 if shorter)
    if len(buf) < 512:
        b = buf + bytes(512 - len(buf))
    else:
        b = buf[:512]

    # Precomputed parity (bitcount mod2) for 0..255
    parity = [0] * 256
    for i in range(256):
        # parity of number of set bits
        parity[i] = bin(i).count("1") & 1

    # Process as 64 little-endian 32-bit words
    rp = [0] * 16  # rp0..rp15
    par = 0
    # Iterate 64 words
    for i in range(64):
        off = i * 4
        cur = b[off] | (b[off + 1] << 8) | (b[off + 2] << 16) | (b[off + 3] << 24)
        par ^= cur
        # Distribute by word index bits (like Linux ecc2)
        if i & 0x01:
            rp[5] ^= cur
        else:
            rp[4] ^= cur
        if i & 0x02:
            rp[7] ^= cur
        else:
            rp[6] ^= cur
        if i & 0x04:
            rp[9] ^= cur
        else:
            rp[8] ^= cur
        if i & 0x08:
            rp[11] ^= cur
        else:
            rp[10] ^= cur
        if i & 0x10:
            rp[13] ^= cur
        else:
            rp[12] ^= cur
        if i & 0x20:
            rp[15] ^= cur
        else:
            rp[14] ^= cur

    # Fold 32-bit accumulators to byte for rp4..rp15
    for idx in range(4, 16):
        v = rp[idx]
        v ^= v >> 16
        v ^= v >> 8
        rp[idx] = v & 0xFF

    # rp0..rp3 derived from par split across bytes
    rp[3] = par >> 16
    rp[3] ^= rp[3] >> 8
    rp[3] &= 0xFF
    rp[2] = par & 0xFFFF
    rp[2] ^= rp[2] >> 8
    rp[2] &= 0xFF
    par ^= par >> 16
    rp[1] = (par >> 8) & 0xFF
    rp[0] = par & 0xFF
    par ^= par >> 8
    par &= 0xFF

    # Build code bytes from parities
    c0 = (
        (parity[rp[7]] << 7)
        | (parity[rp[6]] << 6)
        | (parity[rp[5]] << 5)
        | (parity[rp[4]] << 4)
        | (parity[rp[3]] << 3)
        | (parity[rp[2]] << 2)
        | (parity[rp[1]] << 1)
        | (parity[rp[0]])
    ) & 0xFF
    c1 = (
        (parity[rp[15]] << 7)
        | (parity[rp[14]] << 6)
        | (parity[rp[13]] << 5)
        | (parity[rp[12]] << 4)
        | (parity[rp[11]] << 3)
        | (parity[rp[10]] << 2)
        | (parity[rp[9]] << 1)
        | (parity[rp[8]])
    ) & 0xFF
    # c2 packs various group parities of 'par' (overall column parity)
    c2 = (
        (parity[par & 0xF0] << 7)
        | (parity[par & 0x0F] << 6)
        | (parity[par & 0xCC] << 5)
        | (parity[par & 0x33] << 4)
        | (parity[par & 0xAA] << 3)
        | (parity[par & 0x55] << 2)
    ) & 0xFF

    # Invert to match storage convention; blank sector -> 0xFF 0xFF 0xFF
    c0 ^= 0xFF
    c1 ^= 0xFF
    c2 ^= 0xFF
    return bytes([c0, c1, c2])


def verify_and_correct(
    data: bytes,
    oob: bytes = b"",
    scheme: str = "crc16",
    sector_size: int = 512,
    bytes_per_sector: int = 2,
    oob_offset: int = 0,
) -> tuple[bytes, list[int]]:
    """
    Verify data using a simple ECC rule: compare CRC16(data) with first 2 bytes of OOB (LE).
    This is a pragmatic verifier when OOB stores 2-byte checks; no correction is performed.

    Returns (data, error_markers) where error_markers is non-empty on mismatch.
    """
    errors: list[int] = []
    if scheme == "none":
        return data, errors
    if scheme == "crc16":
        if not oob or len(oob) < 2:
            return data, errors
        calc = _crc16_ccitt(data)
        stored = int.from_bytes(oob[0:2], "little")
        if calc != stored:
            return data, [-1]
        return data, errors
    if scheme == "hamming_512_3byte":
        # Process each 512-byte sector independently (1-bit Hamming ECC, 3 bytes per sector)
        if sector_size <= 0 or bytes_per_sector <= 0:
            return data, errors
        total = len(data)
        sectors = total // sector_size
        for s in range(sectors):
            d0 = s * sector_size
            d1 = d0 + sector_size
            # ECC bytes for this sector
            e0 = oob_offset + s * bytes_per_sector
            e1 = e0 + bytes_per_sector
            if oob is None or e1 > len(oob):
                continue
            ecc_bytes = oob[e0:e1]
            # Compute Hamming ECC (3 bytes) for 512-byte sector
            calc_ecc = _calc_hamming_512_3byte(data[d0:d1])
            if len(ecc_bytes) >= 3:
                stored = ecc_bytes[:3]
                if calc_ecc != stored:
                    errors.append(s)
            else:
                # Not enough ECC bytes for this scheme
                errors.append(s)
        return data, errors
    # Unknown scheme defaults to pass
    return data, errors
