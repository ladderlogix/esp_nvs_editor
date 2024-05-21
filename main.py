from esp_nvs_editor import read_nvs, write_nvs, write_nvs_edit, read_nvs_edit

import argparse

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

if __name__ == "__main__":
    main()
