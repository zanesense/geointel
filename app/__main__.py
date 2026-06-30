import argparse
import csv
import io
import json
import os
import shutil
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from app.services.scanner import (
    SCAN_TYPES, full_scan,
)

VERSION = "1.0.0"
HISTORY_FILE = Path.home() / ".geointel_history"
CONFIG_DIR = Path.home() / ".geointel"
CONFIG_FILE = CONFIG_DIR / "config.json"
ALL_TYPES = list(SCAN_TYPES.keys())
console = Console()

class _S:
    R = "\x1b[0m"
    BOLD = "\x1b[1m"
    DIM = "\x1b[2m"
    GRAY = "\x1b[90m"
    CYAN = "\x1b[36m"
    BLUE = "\x1b[34m"
    GREEN = "\x1b[32m"
    YELLOW = "\x1b[33m"
    RED = "\x1b[31m"

s = _S
LOGO = (
    f"{s.CYAN}                ██████╗ ███████╗ ██████╗ ██╗███╗   ██╗████████╗███████╗██╗     {s.R}\n"
    f"{s.CYAN}                ██╔════╝ ██╔════╝██╔═══██╗██║████╗  ██║╚══██╔══╝██╔════╝██║     {s.R}\n"
    f"{s.CYAN}                ██║  ███╗█████╗  ██║   ██║██║██╔██╗ ██║   ██║   █████╗  ██║     {s.R}\n"
    f"{s.CYAN}                ██║   ██║██╔══╝  ██║   ██║██║██║╚██╗██║   ██║   ██╔══╝  ██║     {s.R}\n"
    f"{s.CYAN}                ╚██████╔╝███████╗╚██████╔╝██║██║ ╚████║   ██║   ███████╗███████╗{s.R}\n"
    f"{s.CYAN}                 ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚══════╝{s.R}"
)


def load_config() -> dict:
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text())
    except Exception:
        pass
    return {}


def save_config(cfg: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def opencage_enrich(lat: float, lon: float, api_key: str) -> dict:
    import requests
    try:
        r = requests.get(
            "https://api.opencagedata.com/geocode/v1/json",
            params={"q": f"{lat},{lon}", "key": api_key},
            timeout=15,
        )
        data = r.json()
        if data.get("status", {}).get("code") == 200 and data.get("results"):
            annot = data["results"][0].get("annotations", {})
            tz = annot.get("timezone", {})
            return {
                "formatted_address": data["results"][0].get("formatted", ""),
                "timezone": tz.get("name", ""),
                "utc_offset": tz.get("offset_string", ""),
                "currency": annot.get("currency", {}).get("name", ""),
                "confidence": data["results"][0].get("confidence", ""),
            }
    except Exception:
        return {}


def print_result_pretty(data, target="", title=""):
    if "error" in data:
        console.print(f"[red]{data['error']}[/red]")
        return
    table = Table(border_style="dim", padding=(0, 1))
    table.add_column("Key", style="dim", no_wrap=True)
    table.add_column("Value", style="")
    for k, v in data.items():
        key = k.replace("_", " ").title()
        if isinstance(v, dict):
            for sk, sv in v.items():
                val = str(sv) if sv is not None else "[dim]-[/dim]"
                table.add_row(f"  {key} {sk.replace('_', ' ').title()}", val)
        elif isinstance(v, list):
            if not v:
                table.add_row(f"  {key}", "[dim](none)[/dim]")
            else:
                for item in v:
                    s_item = str(item) if not isinstance(item, dict) else json.dumps(item, default=str)
                    table.add_row(f"  {key}", s_item)
        else:
            val = str(v) if v is not None else "[dim]-[/dim]"
            table.add_row(f"  {key}", val)
    if title:
        console.print(Panel(f"[cyan]{target}[/cyan]", title=f"[bold]{title}[/bold]", border_style="cyan"))
    console.print(table)


def export_csv(data: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    flat = [(k.replace("_", " ").title(), v) for k, v in data.items()]
    writer.writerow([f[0] for f in flat])
    row = []
    for _, v in flat:
        if isinstance(v, (list, dict)):
            row.append(json.dumps(v, default=str))
        else:
            row.append(str(v) if v is not None else "")
    writer.writerow(row)
    return output.getvalue()


def save_history(target: str):
    try:
        if HISTORY_FILE.exists():
            history = json.loads(HISTORY_FILE.read_text())
        else:
            history = []
        history = [t for t in history if t != target]
        history.insert(0, target)
        HISTORY_FILE.write_text(json.dumps(history[:10]))
    except Exception:
        pass


def show_history():
    try:
        if HISTORY_FILE.exists():
            history = json.loads(HISTORY_FILE.read_text())
            if history:
                console.print("  [bold yellow]\u25c6 Recent Targets[/bold yellow]")
                for i, t in enumerate(history):
                    console.print(f"    [cyan]{i+1}.[/cyan] {t}")
                return
        console.print("  [dim]No history yet.[/dim]")
    except Exception:
        console.print("  [dim]No history yet.[/dim]")


def _print_simple(data: dict):
    for k, v in data.items():
        if isinstance(v, list):
            for item in v:
                print(f"  {k}: {item}")
        elif isinstance(v, dict):
            for sk, sv in v.items():
                print(f"  {k}.{sk}: {sv}")
        else:
            print(f"  {k}: {v}")


def run_lookup(args):
    if not args.no_logo and not args.json and not args.simple:
        print(LOGO)

    config = load_config()
    opencage_key = args.opencage_key or os.environ.get("OPENCAGE_API_KEY") or config.get("opencage_key")

    fmt = args.output
    if not fmt:
        fmt = "json" if args.json else ("simple" if args.simple else ("csv" if args.csv else "pretty"))

    types = [t.strip() for t in args.type.split(",")]
    for t in types:
        if t not in ALL_TYPES and t != "full":
            console.print(f"[red]Unknown scan type:[/red] {t}")
            console.print(f"[dim]Available: {', '.join(ALL_TYPES)}, full[/dim]")
            sys.exit(1)

    run_opencage = opencage_key and any(t == "quick" for t in types)

    try:
        if "full" in types:
            with console.status("[cyan]Running full scan...[/cyan]", spinner="dots") as status:
                output = full_scan(args.target)
                results, errors = output["results"], output["errors"]
                save_history(args.target)
                status.update("")

            if fmt == "json":
                print(json.dumps(output, indent=2, default=str))
            elif fmt == "simple":
                for name, result in results.items():
                    print(f"=== {name} ===")
                    _print_simple(result)
                if errors:
                    print("=== errors ===")
                    for name, msg in errors.items():
                        print(f"  {name}: {msg}")
            elif fmt == "csv":
                for name, result in results.items():
                    if isinstance(result, dict) and "error" not in result:
                        print(f"# {name}")
                        print(export_csv(result))
            else:
                console.print()
                for name, result in results.items():
                    print_result_pretty(result, args.target, name.replace("_", " ").title())
                if errors:
                    console.print("[bold red]Errors:[/bold red]")
                    for name, msg in errors.items():
                        console.print(f"  [red]{name}:[/red] {msg}")

        else:
            results = {}
            errors = {}

            if len(types) == 1:
                with console.status(f"[cyan]Running {types[0]}...[/cyan]", spinner="dots") as status:
                    data = SCAN_TYPES[types[0]](args.target)
                    status.update("")

                if "error" in data:
                    errors[types[0]] = data["error"]
                else:
                    results[types[0]] = data
                save_history(args.target)

                if fmt == "json":
                    print(json.dumps(data, indent=2, default=str))
                elif fmt == "simple":
                    if "error" in data:
                        print(f"  error: {data['error']}")
                    else:
                        _print_simple(data)
                elif fmt == "csv":
                    if "error" in data:
                        print(f"error: {data['error']}")
                    else:
                        print(export_csv(data))
                else:
                    label = types[0].replace("_", " ").title()
                    console.print()
                    print_result_pretty(data, args.target, label)
                    console.print()
            else:
                with console.status("[cyan]Running scans...[/cyan]", spinner="dots") as status:
                    with ThreadPoolExecutor(max_workers=min(4, len(types))) as pool:
                        futures = {pool.submit(SCAN_TYPES[t], args.target): t for t in types}
                        for future in as_completed(futures):
                            t = futures[future]
                            try:
                                data = future.result()
                                if "error" in data:
                                    errors[t] = data["error"]
                                else:
                                    results[t] = data
                            except Exception as e:
                                errors[t] = str(e)
                    status.update("")

                save_history(args.target)

                if fmt == "json":
                    print(json.dumps({
                        "target": args.target,
                        "results": results,
                        "errors": errors or None,
                    }, indent=2, default=str))
                elif fmt == "simple":
                    for t, result in results.items():
                        print(f"=== {t} ===")
                        _print_simple(result)
                    if errors:
                        print("=== errors ===")
                        for name, msg in errors.items():
                            print(f"  {name}: {msg}")
                elif fmt == "csv":
                    for t, result in results.items():
                        if "error" not in result:
                            print(f"# {t}")
                            print(export_csv(result))
                else:
                    console.print()
                    for t, result in results.items():
                        print_result_pretty(result, args.target, t.replace("_", " ").title())
                    if errors:
                        console.print("[bold red]Errors:[/bold red]")
                        for name, msg in errors.items():
                            console.print(f"  [red]{name}:[/red] {msg}")

            if run_opencage:
                qdata = results.get("quick", {})
                if "lat" in qdata and "lon" in qdata:
                    enriched = opencage_enrich(qdata["lat"], qdata["lon"], opencage_key)
                    if enriched:
                        console.print()
                        print_result_pretty(enriched, args.target, "OpenCage Enrichment")

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)


def cmd_info(args):
    if not args.no_logo:
        console.print(LOGO)
    console.print()
    console.print(f"  [bold green]\u25c6 GeoIntel v{VERSION}[/bold green]")
    console.print(f"  [dim]Python:[/dim] {sys.version.split()[0]}")
    console.print()
    console.print("  [bold cyan]\u25c6 Available scan types[/bold cyan]")
    for sid in ALL_TYPES:
        console.print(f"    [cyan]{sid}[/cyan] \u2014 {SCAN_TYPES[sid].__doc__ or ''}")


def cmd_config(args):
    cfg = load_config()
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if args.show:
        if cfg:
            print(json.dumps(cfg, indent=2))
        else:
            console.print("  [dim]No configuration set.[/dim]")
        return

    if args.set:
        key, _, value = args.set.partition("=")
        key = key.strip()
        value = value.strip()
        if not key or not value:
            console.print("  [red]Usage: --set key=value[/red]")
            sys.exit(1)
        cfg[key] = value
        save_config(cfg)
        console.print(f"  [green]\u2714[/green] Set [cyan]{key}[/cyan] = {value}")
        return

    if args.unset:
        if args.unset in cfg:
            del cfg[args.unset]
            save_config(cfg)
            console.print(f"  [green]\u2714[/green] Unset [cyan]{args.unset}[/cyan]")
        else:
            console.print(f"  [yellow]Key not found:[/yellow] {args.unset}")
        return

    if args.reset:
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
            console.print("  [green]\u2714[/green] Configuration reset.")
        else:
            console.print("  [dim]No configuration to reset.[/dim]")
        return

    console.print()
    console.print("  [bold yellow]\u25c6 Current Configuration[/bold yellow]")
    if cfg:
        for k, v in cfg.items():
            console.print(f"    [cyan]{k}[/cyan] = {v}")
    else:
        console.print("    [dim](empty)[/dim]")
    console.print("  [dim]Set values with:[/dim] [cyan]geointel config --set key=value[/cyan]")


def cmd_completion(args):
    shell = args.shell
    if not shutil.which(shell):
        print(f"{s.RED}Shell '{shell}' not found on this system.{s.R}")
        sys.exit(1)

    if shell == "bash":
        print("""# GeoIntel completion for bash
_geointel_completions() {
    local cur="${COMP_WORDS[$COMP_CWORD]}"
    local prev="${COMP_WORDS[$COMP_CWORD-1]}"
    local commands="lookup scan fullscan history info config completion"
    local options="--target -t --type --json --simple --csv --output --opencage-key --no-logo --help"

    if [[ $COMP_CWORD -eq 1 ]]; then
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
    elif [[ $COMP_CWORD -ge 2 ]]; then
        case "${COMP_WORDS[1]}" in
            lookup|scan|fullscan)
                COMPREPLY=($(compgen -W "$options" -- "$cur"))
                ;;
            config)
                COMPREPLY=($(compgen -W "--show --set --unset --reset --help" -- "$cur"))
                ;;
            completion)
                COMPREPLY=($(compgen -W "bash zsh fish" -- "$cur"))
                ;;
        esac
    fi
}
complete -F _geointel_completions geointel
""")
    elif shell == "zsh":
        print("""# GeoIntel completion for zsh
_geointel() {
    local -a cmds
    cmds=(
        'lookup:Look up an IP address or domain'
        'scan:Run one or more scan types'
        'fullscan:Run all scan types'
        'history:Show recent scan history'
        'info:Show version and system information'
        'config:Manage configuration'
        'completion:Generate shell completion scripts'
    )
    _describe 'command' cmds
}
compdef _geointel geointel
""")
    elif shell == "fish":
        print("""# GeoIntel completion for fish
complete -c geointel -f
complete -c geointel -n "not __fish_seen_subcommand_from lookup scan fullscan history info config completion" -a lookup -d "Look up an IP address or domain"
complete -c geointel -n "not __fish_seen_subcommand_from lookup scan fullscan history info config completion" -a scan -d "Run one or more scan types"
complete -c geointel -n "not __fish_seen_subcommand_from lookup scan fullscan history info config completion" -a fullscan -d "Run all scan types"
complete -c geointel -n "not __fish_seen_subcommand_from lookup scan fullscan history info config completion" -a history -d "Show recent scan history"
complete -c geointel -n "not __fish_seen_subcommand_from lookup scan fullscan history info config completion" -a info -d "Show version and system information"
complete -c geointel -n "not __fish_seen_subcommand_from lookup scan fullscan history info config completion" -a config -d "Manage configuration"
complete -c geointel -n "not __fish_seen_subcommand_from lookup scan fullscan history info config completion" -a completion -d "Generate shell completion scripts"
""")
    else:
        print(f"{s.RED}Unsupported shell: {shell}{s.R}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        prog="geointel",
        description="GeoIntel \u2014 OSINT intelligence from your terminal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"GeoIntel v{VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    lookup = sub.add_parser("lookup", help="Look up an IP address or domain",
        epilog=(
            "Examples:\n"
            "  geointel lookup --target 8.8.8.8\n"
            "  geointel lookup --target 8.8.8.8 --type dns\n"
            "  geointel lookup --target 8.8.8.8 --type dns,whois,ssl\n"
            "  geointel lookup --target google.com --type full\n"
            "  geointel lookup --target 8.8.8.8 --json\n"
            "  geointel lookup --target 8.8.8.8 --type quick --csv\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    lookup.add_argument("--target", required=True, help="IP address or domain name to look up")
    lookup.add_argument("-t", "--type", default="quick",
                        help="Scan type(s), comma-separated (default: quick)")
    lookup.add_argument("--output", choices=["json", "simple", "csv", "pretty"],
                        help="Output format")
    lookup.add_argument("--json", action="store_true", help="Output raw JSON (shorthand)")
    lookup.add_argument("--simple", action="store_true", help="Flat key: value output (shorthand)")
    lookup.add_argument("--csv", action="store_true", help="Export results as CSV (shorthand)")
    lookup.add_argument("--opencage-key",
                        help="OpenCage API key for reverse geocoding "
                             "(also: OPENCAGE_API_KEY env var, or set with: geointel config --set opencage_key=...)")
    lookup.add_argument("--no-logo", action="store_true", help="Skip logo on startup")

    scan = sub.add_parser("scan", help="Run one or more scan types",
        epilog=(
            "Examples:\n"
            "  geointel scan --target 8.8.8.8 --type dns\n"
            "  geointel scan --target 8.8.8.8 --type dns,whois\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    scan.add_argument("--target", required=True, help="IP address or domain name")
    scan.add_argument("-t", "--type", required=True, help="Scan type(s), comma-separated")
    scan.add_argument("--output", choices=["json", "simple", "csv", "pretty"],
                      help="Output format")
    scan.add_argument("--json", action="store_true", help="Output raw JSON")
    scan.add_argument("--simple", action="store_true", help="Flat key: value output")
    scan.add_argument("--csv", action="store_true", help="Export results as CSV")
    scan.add_argument("--no-logo", action="store_true", help="Skip logo on startup")

    fullscan = sub.add_parser("fullscan", help="Run all scan types",
        epilog="Example:  geointel fullscan --target example.com",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    fullscan.add_argument("--target", required=True, help="IP address or domain name")
    fullscan.add_argument("--output", choices=["json", "simple", "csv", "pretty"],
                          help="Output format")
    fullscan.add_argument("--json", action="store_true", help="Output raw JSON")
    fullscan.add_argument("--simple", action="store_true", help="Flat key: value output")
    fullscan.add_argument("--csv", action="store_true", help="Export results as CSV")
    fullscan.add_argument("--no-logo", action="store_true", help="Skip logo on startup")

    history = sub.add_parser("history", help="Show recent scan history")
    history.add_argument("--no-logo", action="store_true", help="Skip logo on startup")

    info = sub.add_parser("info", help="Show version and available scan types",
                          formatter_class=argparse.RawDescriptionHelpFormatter)
    info.add_argument("--no-logo", action="store_true", help="Skip logo on startup")

    config = sub.add_parser("config", help="Manage configuration",
                            formatter_class=argparse.RawDescriptionHelpFormatter)
    config.add_argument("--show", action="store_true", help="Show current configuration")
    config.add_argument("--set", metavar="KEY=VALUE",
                        help="Set a configuration value (e.g. --set opencage_key=abc123)")
    config.add_argument("--unset", metavar="KEY", help="Remove a configuration key")
    config.add_argument("--reset", action="store_true", help="Reset all configuration")

    completion = sub.add_parser("completion", help="Generate shell completion scripts",
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    completion.add_argument("shell", choices=["bash", "zsh", "fish"],
                            help="Target shell")

    args = parser.parse_args()

    os.system("cls" if os.name == "nt" else "clear")

    if args.command == "history":
        if not args.no_logo:
            print(LOGO)
        show_history()
        return

    if args.command == "info":
        cmd_info(args)
        return

    if args.command == "config":
        cmd_config(args)
        return

    if args.command == "completion":
        cmd_completion(args)
        return

    if args.command in ("scan", "fullscan"):
        if args.command == "fullscan":
            args.type = "full"
        args.no_logo = getattr(args, "no_logo", False)
        args.opencage_key = getattr(args, "opencage_key", None)

    run_lookup(args)


if __name__ == "__main__":
    main()
