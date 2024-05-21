import io
import json
import math
import typing

from .crc32 import fix_nvs_crc32
from .file_types import *

def nvs_to_json(nvs: NVS) -> typing.Mapping[str, typing.Any]:
    out = {
        "version": nvs.pages[0].header.version,
        "namespaces": {},
        "entries": []
    }

    for page in nvs.pages:
        for entry in page.entries:
            if entry.namespace == 0 and type(entry) == NVSPagePrimitiveEntry:
                out["namespaces"][entry.value] = entry.key

    for page in nvs.pages:

        i = 0
        for entry in page.entries:
            if entry.namespace != 0:
                out_entry = {
                    "state": page.bitmap[i].name,
                    "namespace": entry.namespace,
                    "key": entry.key,
                    "type": entry.type.name,
                }

                if entry.type == NVSPageEntryType.BlobData:
                    out_entry["chunk"] = entry.chunk_index

                if type(entry) == NVSPageVariableEntry:
                    out_entry["data"] = entry.data.hex()
                elif type(entry) == NVSPageIndexEntry:
                    out_entry["start"] = entry.data_chunk_start
                    out_entry["count"] = entry.data_chunk_count
                    out_entry["size"] = entry.data_size
                elif type(entry) == NVSPagePrimitiveEntry:
                    out_entry["data"] = entry.value

                out["entries"].append(out_entry)

            i += entry.span

    return out

def write_nvs_edit(nvs: NVS, h: io.StringIO) -> None:
    json.dump(nvs_to_json(nvs), h, indent=2)

def json_to_nvs(j: typing.Mapping[str, typing.Any]) -> NVS:
    version = j["version"]

    pages = []

    page: NVSPage = None

    def new_page() -> NVSPage:
        if page:
            page.header.state = NVSPageState.Full
            seq_no = page.header.seq_no + 1

            pages.append(page)
        else:
            seq_no = 0

        return NVSPage(
            header=NVSPageHeader(state=NVSPageState.Active, seq_no=seq_no, version=version, crc32=0),
            bitmap=[],
            entries=[]
        )

    page = new_page()

    for namespace_id, namespace_key in j["namespaces"].items():
        page.entries.append(NVSPagePrimitiveEntry(
            namespace=0,
            type=NVSPageEntryType.U8,
            span=1,
            chunk_index=0xFF,
            crc32=0,
            key=namespace_key,
            value=int(namespace_id)
        ))

        page.bitmap.append(NVSPageEntryState.Written)

        if len(page.bitmap) >= 126:
            page = new_page()

    for e in j["entries"]:
        dt = NVSPageEntryType[e["type"]]

        common = {
            "namespace": int(e["namespace"]),
            "type": dt,
            "crc32": 0,
            "key": e["key"]
        }

        if dt == NVSPageEntryType.BlobData:
            data = bytes.fromhex(e["data"])

            entry = NVSPageVariableEntry(
                **common,
                span=math.ceil(len(data) / 32) + 1,
                chunk_index=e["chunk"],
                data_crc32=0,
                data_size=len(data),
                data=data
            )
        elif dt == NVSPageEntryType.String:
            data = bytes.fromhex(e["data"])

            entry = NVSPageVariableEntry(
                **common,
                span=math.ceil(len(data) / 32) + 1,
                chunk_index=0xFF,
                data_crc32=0,
                data_size=len(data),
                data=data
            )
        elif dt == NVSPageEntryType.BlobIndex:
            entry = NVSPageIndexEntry(
                **common,
                span=1,
                chunk_index=0xFF,
                data_size=e["size"],
                data_chunk_count=e["count"],
                data_chunk_start=e["start"]
            )
        else:
            entry = NVSPagePrimitiveEntry(
                **common,
                span=1,
                chunk_index=0xFF,
                value=e["data"]
            )

        page.entries.append(entry)

        state = NVSPageEntryState[e["state"]]
        page.bitmap += [state] + [NVSPageEntryState.Written] * (entry.span - 1)

        if len(page.bitmap) >= 126:
            page = new_page()

    page.bitmap += [NVSPageEntryState.Empty] * (126 - len(page.bitmap))

    pages.append(page)

    nvs = NVS(pages)

    fix_nvs_crc32(nvs)

    return nvs

def read_nvs_edit(h: io.StringIO) -> NVS:
    return json_to_nvs(json.load(h))
