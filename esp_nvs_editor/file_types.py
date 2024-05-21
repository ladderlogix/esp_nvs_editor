import abc
import dataclasses
import enum
import typing

class NVSPageState(enum.Enum):
    Empty = 0xFFFF_FFFF
    Full = 0xFFFF_FFFC
    Active = 0xFFFF_FFFE

@dataclasses.dataclass
class NVSPageHeader:
    state: NVSPageState
    seq_no: int
    version: int
    crc32: int

class NVSPageEntryState(enum.Enum):
    Empty = 0b11
    Written = 0b10
    Erased = 0b00

class NVSPageEntryType(enum.Enum):
    U8 = 0x01
    I8 = 0x11
    U16 = 0x02
    I16 = 0x12
    U32 = 0x04
    I32 = 0x14
    U64 = 0x08
    I64 = 0x18
    String = 0x21
    Blob = 0x41
    BlobData = 0x42
    BlobIndex = 0x48
    Any = 0xFF

ENTRY_TYPE_STRUCT_TYPE_MAP = {
    NVSPageEntryType.U8: "B",
    NVSPageEntryType.I8: "b",
    NVSPageEntryType.U16: "H",
    NVSPageEntryType.I16: "h",
    NVSPageEntryType.U32: "I",
    NVSPageEntryType.I32: "i",
    NVSPageEntryType.U64: "q",
    NVSPageEntryType.I64: "Q"
}

ENTRY_TYPE_STRUCT_SIZE_MAP = {
    NVSPageEntryType.U8: 1,
    NVSPageEntryType.I8: 1,
    NVSPageEntryType.U16: 2,
    NVSPageEntryType.I16: 2,
    NVSPageEntryType.U32: 4,
    NVSPageEntryType.I32: 4,
    NVSPageEntryType.U64: 8,
    NVSPageEntryType.I64: 8
}

@dataclasses.dataclass
class NVSPageEntry(abc.ABC):
    namespace: int
    type: NVSPageEntryType
    span: int
    chunk_index: int
    crc32: int
    key: str

@dataclasses.dataclass
class NVSPagePrimitiveEntry(NVSPageEntry):
    value: int

@dataclasses.dataclass
class NVSPageIndexEntry(NVSPageEntry):
    data_size: int
    data_chunk_count: int
    data_chunk_start: int

@dataclasses.dataclass
class NVSPageVariableEntry(NVSPageEntry):
    data_size: int
    data_crc32: int
    data: bytes

@dataclasses.dataclass
class NVSPage:
    header: NVSPageHeader
    bitmap: typing.List[NVSPageEntryState]
    entries: typing.List[typing.Optional[NVSPageEntry]]

@dataclasses.dataclass
class NVS:
    pages: typing.Sequence[NVSPage]
