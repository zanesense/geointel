import argparse
import csv
import io
import json
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.services.scanner import (
    SCAN_TYPES, full_scan, resolve_domain,
)

HISTORY_FILE = Path.home() / ".geointel_history"
console = Console()

LOGO = r"""
[cyan]                ██████╗ ███████╗ ██████╗ ██╗███╗   ██╗████████╗███████╗██╗     
               ██╔════╝ ██╔════╝██╔═══██╗██║████╗  ██║╚══██╔══╝██╔════╝██║     
               ██║  ███╗█████╗  ██║   ██║██║██╔██╗ ██║   ██║   █████╗  ██║     
               ██║   ██║██╔══╝  ██║   ██║██║██║╚██╗██║   ██║   ██╔══╝  ██║     
               ╚██████╔╝███████╗╚██████╔╝██║██║ ╚████║   ██║   ███████╗███████╗
                ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚══════╝[/cyan]
"""


def opencage_enrich(lat: float, lon: float, api_key: str) -> dict:
    import requests
    try:
        r = requests.get(
            "https://api.opencagedata.com/geocode/v1/json",
            params={"q": f"{lat},{lon}", "key": api_key},
            timeout=10,
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


def print_result_pretty(data: dict, title: str):
    if "error" in data:
        console.print(f"  [red]✗ {data['error']}[/red]")
        return
    table = Table(title=title, title_style="bold cyan", border_style="dim", padding=(0, 1))
    table.add_column("Field", style="dim", no_wrap=True, min_width=20)
    table.add_column("Value", style="")
    for k, v in data.items():
        key = k.replace("_", " ").title()
        if isinstance(v, dict):
            table.add_row(f"[dim]{key}[/dim]", "")
            for sk, sv in v.items():
                sval = str(sv) if sv is not None else "[dim]-[/dim]"
                table.add_row(f"  [dim]{sk}[/dim]", sval)
        elif isinstance(v, list):
            if not v:
                table.add_row(f"[dim]{key}[/dim]", "[dim](none)[/dim]")
            else:
                first = str(v[0]) if not isinstance(v[0], dict) else json.dumps(v[0], default=str)
                table.add_row(f"[dim]{key}[/dim]", first)
                for item in v[1:]:
                    s = str(item) if not isinstance(item, dict) else json.dumps(item, default=str)
                    table.add_row("", s)
        else:
            val = str(v) if v is not None else "[dim]-[/dim]"
            table.add_row(f"[dim]{key}[/dim]", val)
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
                console.print(Panel(
                    "\n".join(f"  [cyan]{i+1}.[/cyan] {t}" for i, t in enumerate(history)),
                    title="[bold yellow]Recent Targets[/bold yellow]",
                    border_style="yellow",
                ))
                return
        console.print("[dim]No history yet.[/dim]")
    except Exception:
        console.print("[dim]No history yet.[/dim]")


def main():
    parser = argparse.ArgumentParser(
        description="[bold]GeoIntel[/bold] \u2014 OSINT intelligence from your terminal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m app 8.8.8.8\n"
            "  python -m app 8.8.8.8 -t dns\n"
            "  python -m app google.com -t full\n"
            "  python -m app 8.8.8.8 --json\n"
            "  python -m app 8.8.8.8 -t quick --csv\n"
        ),
    )
    parser.add_argument("target", nargs="?", help="IP address or domain name to look up")
    parser.add_argument("-t", "--type", default="quick",
                        choices=list(SCAN_TYPES.keys()) + ["full"],
                        help="Scan type (default: quick)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--simple", action="store_true", help="Flat key: value output")
    parser.add_argument("--csv", action="store_true", help="Export results as CSV")
    parser.add_argument("--opencage-key",
                        help="OpenCage API key for reverse geocoding "
                             "(also: OPENCAGE_API_KEY env var)")
    parser.add_argument("--history", action="store_true",
                        help="Show recent scan history")
    parser.add_argument("--no-logo", action="store_true",
                        help="Skip logo on startup")

    args = parser.parse_args()

    if args.history:
        show_history()
        return

    if not args.target:
        parser.print_help()
        sys.exit(1)

    if not args.no_logo and not args.json and not args.simple:
        console.print(LOGO)

    opencage_key = args.opencage_key or os.environ.get("OPENCAGE_API_KEY")

    fmt = "json" if args.json else ("simple" if args.simple else ("csv" if args.csv else "pretty"))

    try:
        with console.status("[cyan]Scanning...[/cyan]", spinner="dots") as status:
            if args.type == "full":
                output = full_scan(args.target)
                results, errors = output["results"], output["errors"]
                save_history(args.target)

                if fmt == "json":
                    status.update("")
                    print(json.dumps(output, indent=2, default=str))
                elif fmt == "simple":
                    status.update("")
                    for name, result in results.items():
                        print(f"=== {name} ===")
                        _print_simple(result)
                    if errors:
                        print("=== errors ===")
                        for name, msg in errors.items():
                            print(f"  {name}: {msg}")
                elif fmt == "csv":
                    status.update("")
                    for name, result in results.items():
                        if isinstance(result, dict) and "error" not in result:
                            print(f"# {name}")
                            print(export_csv(result))
                else:
                    status.update("")
                    console.print()
                    console.print(Panel(
                        f"[cyan]{args.target}[/cyan] \u2022 [dim]Resolved: {output['resolved_ip']}[/dim]",
                        title="[bold]Full Recon[/bold]",
                        border_style="cyan",
                    ))
                    console.print()
                    for name, result in results.items():
                        label = name.replace("_", " ").title()
                        print_result_pretty(result, label)
                        console.print()
                    if errors:
                        console.print("[bold yellow]Errors:[/bold yellow]")
                        for name, msg in errors.items():
                            console.print(f"  [red]{name}:[/red] {msg}")
            else:
                fn = SCAN_TYPES[args.type]
                data = fn(args.target)
                save_history(args.target)

                if fmt == "json":
                    status.update("")
                    print(json.dumps(data, indent=2, default=str))
                elif fmt == "simple":
                    status.update("")
                    _print_simple(data)
                elif fmt == "csv":
                    status.update("")
                    print(export_csv(data))
                else:
                    status.update("")
                    label = args.type.replace("_", " ").title()
                    console.print()
                    resolve_ip = ""
                    if args.type == "quick":
                        resolve_ip = f" \u2022 [dim]{resolve_domain(args.target)}[/dim]"
                    console.print(Panel(
                        f"[cyan]{args.target}[/cyan]{resolve_ip}",
                        title=f"[bold]{label}[/bold]",
                        border_style="cyan",
                    ))
                    console.print()
                    print_result_pretty(data, "")
                    console.print()

                if args.type == "quick" and opencage_key and "lat" in data and "lon" in data:
                    enriched = opencage_enrich(data["lat"], data["lon"], opencage_key)
                    if enriched:
                        console.print()
                        print_result_pretty(enriched, "OpenCage Enrichment")

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)


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


if __name__ == "__main__":
    main()
