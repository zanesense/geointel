import argparse
import json
import sys
from app.services.scanner import (
    SCAN_TYPES, full_scan,
)


def print_result(data: dict, fmt: str):
    if fmt == "json":
        print(json.dumps(data, indent=2, default=str))
        return

    if "error" in data:
        print(f"error: {data['error']}")
        return

    if fmt == "simple":
        for k, v in data.items():
            if isinstance(v, list):
                for item in v:
                    print(f"  {k}: {item}")
            elif isinstance(v, dict):
                for sk, sv in v.items():
                    print(f"  {k}.{sk}: {sv}")
            else:
                print(f"  {k}: {v}")
        return

    # pretty format (default)
    width = max((len(k) for k in data.keys()), default=0) + 2
    for k, v in data.items():
        key = k.replace("_", " ").title()
        if isinstance(v, list):
            print(f"  \033[90m{key.ljust(width)}\033[0m", end="")
            if not v:
                print("\033[2m(none)\033[0m")
            else:
                print(v[0])
                for item in v[1:]:
                    print(f"  {' ' * width}{item}")
        elif isinstance(v, dict):
            print(f"  \033[90m{key}:\033[0m")
            for sk, sv in v.items():
                print(f"    \033[90m{sk}:\033[0m {sv}")
        else:
            val = str(v) if v is not None else "\033[2m-\033[0m"
            print(f"  \033[90m{key.ljust(width)}\033[0m{val}")


def main():
    parser = argparse.ArgumentParser(
        description="GeoIP — IP Geolocation and Intelligence CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m app 8.8.8.8\n"
            "  python -m app 8.8.8.8 -t dns\n"
            "  python -m app google.com -t full\n"
            "  python -m app 8.8.8.8 --json\n"
            "  python -m app 8.8.8.8 -t quick --simple\n"
        ),
    )
    parser.add_argument("target", help="IP address or domain name to look up")
    parser.add_argument(
        "-t", "--type",
        default="quick",
        choices=list(SCAN_TYPES.keys()) + ["full"],
        help="Scan type (default: quick)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON",
    )
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Simple flat key: value output",
    )

    args = parser.parse_args()

    fmt = "json" if args.json else ("simple" if args.simple else "pretty")

    try:
        if args.type == "full":
            output = full_scan(args.target)
            results, errors = output["results"], output["errors"]

            if fmt == "pretty":
                print(f"\n  \033[1mGeoIP Full Scan — {args.target}\033[0m")
                print(f"  \033[90mResolved IP: {output['resolved_ip']}\033[0m\n")
                for name, result in results.items():
                    label = name.replace("_", " ").title()
                    print(f"  \033[33m{label}\033[0m")
                    print_result(result, fmt)
                    print()
                if errors:
                    print("  \033[31mErrors:\033[0m")
                    for name, msg in errors.items():
                        print(f"    {name}: {msg}")
            elif fmt == "simple":
                for name, result in results.items():
                    print(f"=== {name} ===")
                    print_result(result, fmt)
                if errors:
                    print("=== errors ===")
                    for name, msg in errors.items():
                        print(f"  {name}: {msg}")
            else:
                print(json.dumps(output, indent=2, default=str))
        else:
            fn = SCAN_TYPES[args.type]
            data = fn(args.target)

            if fmt == "pretty":
                label = args.type.replace("_", " ").title()
                print(f"\n  \033[1m{label} — {args.target}\033[0m\n")
                print_result(data, fmt)
                print()
            else:
                print_result(data, fmt)

    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
