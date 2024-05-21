from esp_nvs_editor import check_nvs_crc32, fix_nvs_crc32, read_nvs, read_nvs_edit, write_nvs, write_nvs_edit 

import argparse
import io

def main():
    parser = argparse.ArgumentParser()
    
    subparsers = parser.add_subparsers(help="Command", dest="command")

    json_parser = subparsers.add_parser("json", help="Convert nvs binary partition to json")
    json_parser.add_argument("input", help="Binary file to convert")
    json_parser.add_argument("output", help="Json file output location")

    bin_parser = subparsers.add_parser("bin", help="Convert json to nvs binary partition")
    bin_parser.add_argument("input", help="Json file to convert")
    bin_parser.add_argument("output", help="Binary file output location")
    bin_parser.add_argument("-s", "--size", help="Size of nvs partition", type=int, default=-1)

    check_parser = subparsers.add_parser("check", help="Checks if nvs binary partition is valid")
    check_parser.add_argument("input", help="Binary file to check")

    fix_parser = subparsers.add_parser("fix", help="Attempts to fix an nvs binary partition")
    fix_parser.add_argument("input", help="Binary file to fix")
    fix_parser.add_argument("output", help="Fixed binary file output")

    args = parser.parse_args()

    if args.command == "json":
        with open(args.input, "rb") as h:
            nvs = read_nvs(h)

        with open(args.output, "w") as h:
            write_nvs_edit(nvs, h)
    elif args.command == "bin":
        with open(args.input, "r") as h:
            nvs = read_nvs_edit(h)

        with open(args.output, "wb") as h:
            write_nvs(nvs, h, partition_size=args.size)
    elif args.command == "check":
        with open(args.input, "rb") as h:
            nvs = read_nvs(h)

        print(check_nvs_crc32(nvs))
    elif args.command == "fix":
        with open(args.input, "rb") as h:
            data = h.read()
            nvs = read_nvs(io.BytesIO(data))

        fix_nvs_crc32(nvs)

        with open(args.output, "wb") as h:
            write_nvs(nvs, h, partition_size=len(data))

if __name__ == "__main__":
    main()
