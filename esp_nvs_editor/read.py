import io
import struct

from .file_types import *

def read_nvs_page_header(h: io.BytesIO) -> NVSPageHeader:
    hh = io.BytesIO(h.read(32))

    state = NVSPageState(struct.unpack("I", hh.read(4))[0])
    seq_no = struct.unpack("I", hh.read(4))[0]
    version = 0x100 - hh.read(1)[0]
    _ = hh.read(19)
    crc32 = struct.unpack("I", hh.read(4))[0]

    return NVSPageHeader(
        state=state,
        seq_no=seq_no,
        version=version,
        crc32=crc32
    )

def read_nvs_page_entry(h: io.BytesIO) -> typing.Optional[NVSPageEntry]:
    eh = io.BytesIO(h.read(32))

    namespace, type, span, chunk_index, crc32 = struct.unpack("BBBBI", eh.read(8))
    type = NVSPageEntryType(type)

    if type == NVSPageEntryType.Any:
        return None

    key = eh.read(16).rstrip(b"\x00").decode()

    common = {
        "namespace": namespace,
        "type": type,
        "span": span,
        "chunk_index": chunk_index,
        "crc32": crc32,
        "key": key,
    }

    if type in [NVSPageEntryType.String, NVSPageEntryType.BlobData]:
        data_size, _, data_crc32 = struct.unpack("HHI", eh.read(8))
        data = h.read(32 * (span - 1))[:data_size]

        return NVSPageVariableEntry(
            **common,
            data_size=data_size,
            data_crc32=data_crc32,
            data=data
        )
    elif type == NVSPageEntryType.BlobIndex:
        data_size, data_chunk_count, data_chunk_start, _ = struct.unpack("IBBH", eh.read(8))

        return NVSPageIndexEntry(
            **common,
            data_size=data_size,
            data_chunk_count=data_chunk_count,
            data_chunk_start=data_chunk_start,
        )
    else:
        data = struct.unpack(ENTRY_TYPE_STRUCT_TYPE_MAP[type], eh.read(8)[:ENTRY_TYPE_STRUCT_SIZE_MAP[type]])[0]

        return NVSPagePrimitiveEntry(
            **common,
            value=data
        )

def read_nvs_page(h: io.BytesIO) -> typing.Optional[NVSPage]:
    page_chunk = h.read(32 + 32 + 32 * 126)

    if len(page_chunk) < 32 + 32 + 32 * 126:
        return None

    ph = io.BytesIO(page_chunk)

    header = read_nvs_page_header(ph)

    if header.state == NVSPageState.Empty:
        return None

    bitmap_bits = bin(int(ph.read(32).hex(), 16))[2:].rjust(256, "0")
    bitmap = [NVSPageEntryState(int(bitmap_bits[i:i+2], 2)) for i in range(0, 252, 2)]

    eh = io.BytesIO(ph.read(32 * 126))

    entries = []
    i = 0
    while i < 126:
        entry = read_nvs_page_entry(eh)
        if entry is None:
            break

        i += entry.span

        entries.append(entry)

    return NVSPage(
        header=header,
        bitmap=bitmap,
        entries=entries
    )

def read_nvs(h: io.BytesIO) -> NVS:
    pages = []

    while True:
        page = read_nvs_page(h)

        if page is None:
            break

        pages.append(page)

    return NVS(
        pages=pages
    )
