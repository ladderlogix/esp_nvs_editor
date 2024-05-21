import binascii
import struct

from .file_types import *

def crc32(data: bytes) -> int:
    return binascii.crc32(data, 0xffffffff)

def crc32_nvs_page_header(header: NVSPageHeader) -> int:
    crc32_data = (
        struct.pack("I", header.seq_no)
        + struct.pack("B", 0xFF - (header.version - 1))
        + (b"\xFF" * 19)
    )

    return crc32(crc32_data)

def crc32_nvs_page_entry(entry: NVSPageEntry) -> int:
    crc32_data = (
        struct.pack("BBBB", entry.namespace, entry.type.value, entry.span, entry.chunk_index)
        + entry.key.encode().ljust(16, b"\x00")
    )

    if type(entry) == NVSPagePrimitiveEntry:
        crc32_data += struct.pack(ENTRY_TYPE_STRUCT_TYPE_MAP[entry.type], entry.value).ljust(8, b"\xFF")
    elif type(entry) == NVSPageIndexEntry:
        crc32_data += struct.pack("IBBH", entry.data_size, entry.data_chunk_count, entry.data_chunk_start, 0xFFFF)
    elif type(entry) == NVSPageVariableEntry:
        crc32_data += struct.pack("HHI", entry.data_size, 0xFFFF, entry.data_crc32)
    else:
        raise Exception(f"Unhandled {type(entry)}")

    return crc32(crc32_data)

def crc32_nvs_page_variable_entry(entry: NVSPageVariableEntry) -> int:
    return crc32(entry.data)

def check_nvs_crc32(nvs: NVS) -> bool:
    for page in nvs.pages:
        page_crc32 = crc32_nvs_page_header(page.header)
        
        if page_crc32 != page.header.crc32:
            return False

        for entry in page.entries:
            if type(entry) == NVSPageVariableEntry:
                variable_entry_crc32 = crc32_nvs_page_variable_entry(entry)

                if variable_entry_crc32 != entry.data_crc32:
                    return False

            entry_crc32 = crc32_nvs_page_entry(entry)

            if entry_crc32 != entry.crc32:
                return False
            
    return True

def fix_nvs_crc32(nvs: NVS) -> None:
    for page in nvs.pages:
        page.header.crc32 = crc32_nvs_page_header(page.header)

        for entry in page.entries:
            if type(entry) == NVSPageVariableEntry:
                entry.data_crc32 = crc32_nvs_page_variable_entry(entry)

            entry.crc32 = crc32_nvs_page_entry(entry)
