# ESP NVS Editor

Tool to edit ESP NVS partitions.

## Disclaimer

This repository only supports unencrypted ESP NVS partitions. Additionally, this was only tested on an ESP32. Output might not be 100% replicated, make sure to keep a copy of your partition.

## Usage

```bash
git clone https://github.com/ladderlogix/esp_nvs_editor
```

Get NVS.bin from ESP32_image_parser

```bash
python main.py json nvs.bin nvs.json
```

Open JSON strings are hex encoded

```bash
python main.py bin nvs.json nvs.patched
```

flash to chip (run from esp-idf 5.3, under components\partition_table)

```bash
python .\parttool.py --port COM5 write_partition --partition-name=nvs --input "D:\NVSReplacing\nvs.patched.bin"
```

