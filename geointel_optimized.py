#!/usr/bin/env python3
"""
GeoIntel - Proxy fetch + verify + IP intelligence & optional OpenCage reverse geocode.

Requirements:
    pip install requests beautifulsoup4 rich tqdm

Usage:
    python geointel_optimized.py
"""

import requests
import socket
import random
import os
from typing import List
from bs4 import BeautifulSoup
from tqdm import tqdm
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from concurrent.futures import ThreadPoolExecutor, as_completed

console = Console()

os.system('cls' if os.name == 'nt' else 'clear')

# --- CONFIGURATION ---
OPENCAGE_API_KEY = ""
OPENCAGE_URL = "https://api.opencagedata.com/geocode/v1/json"

PROXY_SOURCES = [
    "https://free-proxy-list.net/",
    "https://www.sslproxies.org/",
    "https://us-proxy.org/",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://www.proxy-list.download/api/v1/get?type=https",
]

MAX_WORKERS = 50 

# -------------------------
# Banner
# -------------------------
def print_banner():
    """Prints the GeoIntel ASCII art banner."""

    banner = r"""
                     .__        __         .__       
   ____   ____  ____ |__| _____/  |_  ____ |  |      
  / ___\_/ __ \/  _ \|  |/    \   __\/ __ \|  |      
 / /_/  >  ___(  <_> )  |   |  \  | \  ___/|  |__    
 \___  / \___  >____/|__|___|  /__|  \___  >____/ /\ 
/_____/      \/              \/          \/       \/ 

    """
    console.print(f"[bold magenta]{banner}[/bold magenta]")
    console.print("[bold cyan]      GeoIntel: Proxy-Assisted IP Intelligence[/bold cyan]\n")


# -------------------------
# Utilities
# -------------------------
def safe_str(x):
    return str(x) if x is not None else "N/A"


def resolve_hostname(target: str) -> str:
    """Resolve hostname to IP, return input if resolution fails."""
    try:
        return socket.gethostbyname(target)
    except Exception:
        return target


# -------------------------
# Proxy Scraping & Verification
# -------------------------
def scrape_proxies_from_html(url: str) -> List[str]:
    """Scrape proxies from HTML table pages."""
    proxies = []
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table", {"id": "proxylisttable"}) or soup.find("table")
        if not table:
            return proxies
        rows = table.find_all("tr")
        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) >= 2:
                ip = cols[0].get_text(strip=True)
                port = cols[1].get_text(strip=True)
                proxies.append(f"{ip}:{port}")
    except Exception:
        pass
    return proxies


def scrape_proxies_from_plain(url: str) -> List[str]:
    """Scrape proxies from plain-text endpoints."""
    proxies = []
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        for line in r.text.splitlines():
            line = line.strip()
            if line and ":" in line:
                proxies.append(line)
    except Exception:
        pass
    return proxies


def fetch_proxies() -> List[str]:
    """Aggregate proxies from multiple sources (deduplicated)."""
    console.print("[cyan]Scraping free proxy sources...[/cyan]")
    all_proxies = []
    for src in PROXY_SOURCES:
        if src.endswith(".download") or "api/v1" in src:
            found = scrape_proxies_from_plain(src)
        else:
            found = scrape_proxies_from_html(src)
        count = len(found)
        if count:
            console.print(f"  [green]Fetched {count} proxies from[/green] {src}")
        all_proxies.extend(found)
    dedup = list(dict.fromkeys(all_proxies))
    console.print(f"[cyan]Total unique proxies scraped: [bold]{len(dedup)}[/bold][/cyan]")
    return dedup


def is_proxy_responsive(proxy_ipport: str, timeout: float = 2.0) -> bool:
    """Quick TCP connect test: True if ip:port accepts connection."""
    try:
        host, port_s = proxy_ipport.split(":")
        port = int(port_s)
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True
    except Exception:
        return False


def verify_proxies(proxies: List[str]) -> List[str]:
    """Verify proxies concurrently using ThreadPoolExecutor."""
    if not proxies:
        console.print("[yellow]No proxies to verify.[/yellow]")
        return []
        
    console.print(f"\n[cyan]Verifying scraped proxies concurrently (up to {MAX_WORKERS} threads)...[/cyan]")
    verified = []
    failed = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_proxy = {executor.submit(is_proxy_responsive, p): p for p in proxies}
        
        for future in tqdm(as_completed(future_to_proxy), 
                           total=len(proxies), 
                           desc="Verifying", 
                           colour="green"):
            
            proxy = future_to_proxy[future]
            try:
                if future.result():
                    verified.append(proxy)
                else:
                    failed += 1
            except Exception:
                failed += 1 
                
    console.print(f"[green]Verified proxies:[/green] {len(verified)} | [red]Failed:[/red] {failed}")
    return verified


# -------------------------
# Request Logic
# -------------------------
def _requests_with_optional_proxy(url: str, proxies: List[str] = None, timeout: int = 10):
    """
    Try a direct request. Fallback to a random proxy on connection error (Exception) 
    or rate-limiting response (429/402).
    """
    r = None
    need_proxy = False
    
    # 1. Attempt Direct Connection
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if r is not None and r.status_code in (402, 429):
            console.print(f"[yellow]Direct request encountered rate limit ({r.status_code}).[/yellow]")
            need_proxy = True
        else:
            return r
    except requests.exceptions.ConnectionError:
        console.print("[yellow]Direct request failed due to connection error.[/yellow]")
        need_proxy = True
    except requests.exceptions.RequestException as e:
        console.print(f"[yellow]Direct request failed due to general error: {type(e).__name__}.[/yellow]")
        need_proxy = True
    
    # Check for direct success (200-299)
    if r is not None and 200 <= r.status_code < 300:
        return r

    # 2. Proxy Fallback if Needed
    if need_proxy and proxies:
        console.print("[yellow]Retrying with verified proxies...[/yellow]")
        to_try = proxies.copy()
        random.shuffle(to_try)
        
        for p in to_try:
            proxy_dict = {"http": f"http://{p}", "https": f"http://{p}"}
            try:
                r2 = requests.get(url, proxies=proxy_dict, timeout=timeout)
                if r2 is not None and 200 <= r2.status_code < 300:
                    return r2
                if r2 is not None and r2.status_code in (402, 429):
                    continue
            except Exception:
                continue
    
    return r


# -------------------------
# Geolocation API wrappers
# -------------------------
def fetch_ipapi(ip: str, verified_proxies: List[str] = None):
    url = f"http://ip-api.com/json/{ip}?fields=66846719"
    r = _requests_with_optional_proxy(url, proxies=verified_proxies)
    if r is None:
        return {"error": "No response"}
    try:
        return r.json()
    except Exception:
        return {"error": "Invalid JSON"}


def fetch_ipwhois(ip: str, verified_proxies: List[str] = None):
    url = f"https://ipwho.is/{ip}"
    r = _requests_with_optional_proxy(url, proxies=verified_proxies)
    if r is None:
        return {"error": "No response"}
    try:
        return r.json()
    except Exception:
        return {"error": "Invalid JSON"}


def fetch_opencage(lat, lon, verified_proxies: List[str] = None):
    if not OPENCAGE_API_KEY:
        return {"error": "No OpenCage key configured"}
    url = f"{OPENCAGE_URL}?q={lat}+{lon}&key={OPENCAGE_API_KEY}"
    r = _requests_with_optional_proxy(url, proxies=verified_proxies)
    if r is None:
        return {"error": "No response"}
    try:
        return r.json()
    except Exception:
        return {"error": "Invalid JSON"}


# -------------------------
# Display helpers
# -------------------------
def display_summary(verified: List[str], total_scraped: int):
    failed = total_scraped - len(verified)
    panel = Panel.fit(f"[green]Verified:[/green] {len(verified)}    [red]Failed:[/red] {failed}",
                      title="Proxy Verification Summary", border_style="blue")
    console.print(panel)


def display_results(ipapi_data: dict, ipwho_data: dict, opencage_data: dict = None):
    t = Table(box=None, show_header=False, pad_edge=True)
    t.add_column("Field", style="bold cyan", width=24)
    t.add_column("Value", style="white")

    # Use ip-api data if available, otherwise fall back to ipwhois
    data_source = None
    if ipapi_data and not ipapi_data.get("error"):
        data_source = ipapi_data
        t.add_row("IP", safe_str(data_source.get("query")))
        t.add_row("Country", safe_str(data_source.get("country")))
        t.add_row("Region", safe_str(data_source.get("regionName")))
        t.add_row("City", safe_str(data_source.get("city")))
        t.add_row("Timezone", safe_str(data_source.get("timezone")))
        t.add_row("ISP", safe_str(data_source.get("isp")))
        t.add_row("Org", safe_str(data_source.get("org")))
        t.add_row("AS", safe_str(data_source.get("as")))
        t.add_row("Latitude", safe_str(data_source.get("lat")))
        t.add_row("Longitude", safe_str(data_source.get("lon")))
    elif ipwho_data and not ipwho_data.get("error"):
        data_source = ipwho_data
        t.add_row("IP", safe_str(data_source.get("ip")))
        t.add_row("Country", safe_str(data_source.get("country")))
        t.add_row("Region", safe_str(data_source.get("region")))
        t.add_row("City", safe_str(data_source.get("city")))
        t.add_row("Latitude", safe_str(data_source.get("latitude")))
        t.add_row("Longitude", safe_str(data_source.get("longitude")))
        conn = data_source.get("connection", {})
        t.add_row("ASN", safe_str(conn.get("asn")))
        t.add_row("ISP", safe_str(conn.get("isp")))
        t.add_row("Org", safe_str(conn.get("org")))
    else:
        t.add_row("Error", "No usable geolocation data returned")

    console.print(Panel(t, title="GeoIntel — Aggregated IP Info", border_style="magenta"))

    # Show opencage details if present
    if opencage_data:
        if opencage_data.get("error"):
            console.print(Panel(f"[yellow]OpenCage: {opencage_data['error']}[/yellow]", title="OpenCage", border_style="yellow"))
        elif opencage_data.get("results"):
            best = opencage_data["results"][0]
            comp = best.get("components", {})
            tt = Table(box=None, show_header=False)
            tt.add_column("Field", style="bold cyan", width=24)
            tt.add_column("Value", style="white")
            tt.add_row("Formatted", safe_str(best.get("formatted")))
            tt.add_row("Country", safe_str(comp.get("country")))
            tt.add_row("State/Region", safe_str(comp.get("state")))
            tt.add_row("City", safe_str(comp.get("city", comp.get("town"))))
            tt.add_row("Postal Code", safe_str(comp.get("postcode")))
            tt.add_row("Confidence", safe_str(best.get("confidence")))
            console.print(Panel(tt, title="OpenCage Reverse Geocode", border_style="green"))
        else:
            console.print(Panel("[yellow]OpenCage returned no results[/yellow]", title="OpenCage", border_style="yellow"))


# -------------------------
# Main flow
# -------------------------
def main():
    try:
        print_banner()

        scraped = fetch_proxies()
        verified = verify_proxies(scraped)

        display_summary(verified, total_scraped=len(scraped))

        target = console.input("\n[bold yellow]Enter target IP or hostname (leave empty to auto-detect your IP):[/bold yellow] ").strip()
        if not target:
            try:
                target = requests.get("https://api.ipify.org", timeout=8).text.strip()
                console.print(f"[green]Auto-detected your IP: {target}[/green]")
            except Exception:
                console.print("[red]Could not auto-detect IP. Please enter target manually.[/red]")
                target = console.input("Target IP/hostname: ").strip()
                if not target:
                    console.print("[red]No target provided. Exiting.[/red]")
                    return

        ip = resolve_hostname(target)
        console.print(f"[cyan]Resolved target -> {ip}[/cyan]")

        console.print("\n[cyan]Querying geolocation services (direct request preferred)...[/cyan]")
        ipapi = fetch_ipapi(ip, verified_proxies=verified)
        ipwho = fetch_ipwhois(ip, verified_proxies=verified)

        # Reverse geocode setup
        lat = ipapi.get("lat") if ipapi and not ipapi.get("error") else ipwho.get("latitude") if ipwho and not ipwho.get("error") else None
        lon = ipapi.get("lon") if ipapi and not ipapi.get("error") else ipwho.get("longitude") if ipwho and not ipwho.get("error") else None

        opencage = None
        if OPENCAGE_API_KEY and lat and lon:
            console.print("[cyan]Fetching reverse-geocode from OpenCage...[/cyan]")
            opencage = fetch_opencage(lat, lon, verified_proxies=verified)
        elif not OPENCAGE_API_KEY:
            console.print("[yellow]OpenCage key not set — skipping reverse-geocode.[/yellow]")

        display_results(ipapi, ipwho, opencage)

    except KeyboardInterrupt:
        console.print("\n[red]Interrupted by user. Exiting.[/red]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")


if __name__ == "__main__":
    main()
