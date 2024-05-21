import io
import math
import struct

from .file_types import *

def write_nvs_page_header(header: NVSPageHeader, h: io.BytesIO) -> None:
    h.write(struct.pack("IIB", header.state.value, header.seq_no, 0xFF - (header.version - 1)))
    h.write(b"\xFF" * 19)
    h.write(struct.pack("I", header.crc32))

def write_nvs_page_entry(entry: NVSPageEntry, h: io.BytesIO) -> None:
    h.write(struct.pack("BBBBI", entry.namespace, entry.type.value, entry.span, entry.chunk_index, entry.crc32))
    h.write(entry.key.encode().ljust(16, b"\x00"))

    if type(entry) == NVSPageVariableEntry:
        h.write(struct.pack("HHI", entry.data_size, 0xFFFF, entry.data_crc32))

        h.write(entry.data)

        raw_size = math.ceil(entry.data_size / 32) * 32

        pad_len = raw_size - entry.data_size
        h.write(b"\xFF" * pad_len)
    elif type(entry) == NVSPageIndexEntry:
        h.write(struct.pack("IBBH", entry.data_size, entry.data_chunk_count, entry.data_chunk_start, 0xFFFF))
    elif type(entry) == NVSPagePrimitiveEntry:
        data = struct.pack(ENTRY_TYPE_STRUCT_TYPE_MAP[entry.type], entry.value)
        data_len = ENTRY_TYPE_STRUCT_SIZE_MAP[entry.type]

        h.write(data)

        pad_len = 8 - data_len
        h.write(b"\xFF" * pad_len)
    else:
        raise Exception(f"Unhandled {entry}")

def write_nvs_page(page: NVSPage, h: io.BytesIO) -> None:
    write_nvs_page_header(page.header, h)

    if page.header.state == NVSPageState.Active:
        padding = "1111"
    else:
        padding = "0000"

    bitmap_bits = ("".join([bin(state.value)[2:].rjust(2, "0") for state in page.bitmap]) + padding)

    bitmap_bytes = []
    for i in range(0, 256, 8):
        bitmap_bytes.append(int(bitmap_bits[i:i+8], 2))
    bitmap_raw = bytes(bitmap_bytes)

    h.write(bitmap_raw)

    i = 0
    for entry in page.entries:
        i += entry.span

        write_nvs_page_entry(entry, h)

    for _ in range(i, 126):
        h.write(b"\xFF" * 32)

def write_nvs(nvs: NVS, h: io.BytesIO, partition_size: typing.Optional[int] = None) -> None:
    for page in nvs.pages:
        write_nvs_page(page, h)

    if partition_size is not None and partition_size > 0:
        h.write(b"\xFF" * (partition_size - h.tell()))
