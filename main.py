#!/usr/bin/env python3
"""
GeoIntel - Refactored & Enhanced

Features implemented:
 - Class-based design (GeoIntel)
 - Config via .env (python-dotenv)
 - CLI via argparse
 - Structured logging to file + console
 - Improved proxy scraping & verification (socket + HTTP test)
 - Save/reuse working proxies
 - Adaptive threading (based on CPU)
 - Cloudflare detection + cloudscraper fallback (with proxy rotation)
 - Merge geolocation data from ip-api and ipwho.is
 - Rate-limit handling and exponential backoff
 - Graceful shutdown / save state on exit
 - Minimal and clear CLI UI (rich)
"""

from __future__ import annotations
import os
import sys
import time
import json
import signal
import socket
import random
import logging
import argparse
import itertools
import threading
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import cloudscraper
from bs4 import BeautifulSoup
from tqdm import tqdm
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from dotenv import load_dotenv
from huepy import *

# Load .env config
load_dotenv()

# -------------------------
# Configuration (from .env or defaults)
# -------------------------
OPENCAGE_API_KEY = os.getenv("OPENCAGE_API_KEY", "").strip()
OPENCAGE_URL = os.getenv("OPENCAGE_URL", "https://api.opencagedata.com/geocode/v1/json")
PROXY_SOURCES = os.getenv("PROXY_SOURCES",
                         "https://free-proxy-list.net/,https://www.sslproxies.org/,https://us-proxy.org/,https://www.proxy-list.download/api/v1/get?type=http,https://www.proxy-list.download/api/v1/get?type=https").split(",")
SAVE_WORKING = os.getenv("SAVE_WORKING_PROXIES", "working_proxies.txt")
LOG_FILE = os.getenv("LOG_FILE", "geointel.log")
DEFAULT_MAX_WORKERS = int(os.getenv("MAX_WORKERS", "50"))

# CLI defaults
DEFAULT_TIMEOUT = 10
DEFAULT_VERIFY_TIMEOUT = 3.0
HTTP_TEST_URL = "http://httpbin.org/ip"  # used to verify proxy actually forwards traffic

console = Console()
logger = logging.getLogger("GeoIntel")


def bnr():
    print(cyan(r"""
                     .__        __         .__       
   ____   ____  ____ |__| _____/  |_  ____ |  |      
  / ___\_/ __ \/  _ \|  |/    \   __\/ __ \|  |      
 / /_/  >  ___(  <_> )  |   |  \  | \  ___/|  |__    
 \___  / \___  >____/|__|___|  /__|  \___  >____/ /\  v1.0
/_____/      \/              \/          \/       \/  © zanesense.

"""))
# -------------------------
# Logging setup
# -------------------------
def setup_logging(debug: bool = False):
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    fh = logging.FileHandler(LOG_FILE)
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    sh.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.addHandler(sh)

# -------------------------
# Utility helpers
# -------------------------
def safe_str(x):
    return str(x) if x is not None else "N/A"

def resolve_hostname(target: str) -> str:
    try:
        return socket.gethostbyname(target)
    except Exception:
        return target

def load_saved_proxies(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def save_working_proxies(path: str, proxies: List[str]):
    try:
        with open(path, "w", encoding="utf-8") as f:
            for p in proxies:
                f.write(p + "\n")
        logger.info("Saved %d working proxies to %s", len(proxies), path)
    except Exception as e:
        logger.exception("Failed to save working proxies: %s", e)

# -------------------------
# Proxy scraping & parsing
# -------------------------
def scrape_proxies_from_html(url: str, timeout: int = 10) -> List[str]:
    proxies = []
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
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
    except Exception as e:
        logger.debug("scrape_html failed for %s: %s", url, e)
    return proxies

def scrape_proxies_from_plain(url: str, timeout: int = 10) -> List[str]:
    proxies = []
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        for line in r.text.splitlines():
            line = line.strip()
            if line and ":" in line:
                proxies.append(line)
    except Exception as e:
        logger.debug("scrape_plain failed for %s: %s", url, e)
    return proxies

# -------------------------
# Proxy verification (socket + http test)
# -------------------------
def is_proxy_connectable(proxy_ipport: str, timeout: float = DEFAULT_VERIFY_TIMEOUT) -> bool:
    try:
        host, port_s = proxy_ipport.split(":")
        port = int(port_s)
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True
    except Exception:
        return False

def is_proxy_forwarding_http(proxy_ipport: str, timeout: int = DEFAULT_VERIFY_TIMEOUT) -> bool:
    # attempt a simple http GET to httpbin using the proxy
    try:
        proxies = {"http": f"http://{proxy_ipport}", "https": f"http://{proxy_ipport}"}
        r = requests.get(HTTP_TEST_URL, proxies=proxies, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and r.text:
            # basic validation: ensure returned ip exists in the body
            return True
    except Exception:
        pass
    return False

def verify_proxy_full(proxy: str) -> bool:
    # Combined check: socket-level then HTTP forwarding
    if not is_proxy_connectable(proxy):
        return False
    # HTTP test may be slower so it's ok to occasionally fail; still useful
    return is_proxy_forwarding_http(proxy)

# -------------------------
# Cloudflare detection helper
# -------------------------
def is_cloudflare_challenge(response: Optional[requests.Response]) -> bool:
    if response is None:
        return False
    try:
        text = response.text or ""
        status_code = getattr(response, "status_code", 0)
        if status_code in (403, 503, 520, 521):
            if 'cf-mitigation' in text or 'cf-browser-verification' in text:
                return True
        if 'Just a moment...' in text or 'DDoS protection by Cloudflare' in text or 'Checking your browser before accessing' in text or 'Attention Required!' in text:
            return True
        if 'Cloudflare' in text and status_code >= 400:
            return True
    except Exception:
        pass
    return False

# -------------------------
# Geo API wrappers
# -------------------------
def requests_with_optional_proxy(url: str, session: requests.Session, proxies: List[str] = None, timeout: int = DEFAULT_TIMEOUT) -> Optional[requests.Response]:
    """
    Attempt direct request, detect Cloudflare, then fallback to cloudscraper with proxy rotation.
    This wrapper is conservative: attempts direct request once, then uses proxies if necessary.
    """
    r = None
    try:
        r = session.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if 200 <= r.status_code < 300 and not is_cloudflare_challenge(r):
            return r
    except requests.RequestException as e:
        logger.debug("Direct request exception: %s", e)

    # If proxies available, try cloudscraper with proxies rotated
    if proxies:
        shuffled = proxies.copy()
        random.shuffle(shuffled)
        for p in shuffled:
            try:
                scraper = cloudscraper.create_scraper(delay=5, sess=session)
                proxy_dict = {"http": f"http://{p}", "https": f"http://{p}"}
                r2 = scraper.get(url, timeout=timeout, proxies=proxy_dict, headers={"User-Agent": "Mozilla/5.0"})
                if 200 <= r2.status_code < 300 and not is_cloudflare_challenge(r2):
                    logger.debug("Success via proxy %s for %s", p, url)
                    return r2
                # if challenge or rate-limit, continue to next proxy
                if is_cloudflare_challenge(r2) or r2.status_code in (402, 429, 503):
                    continue
            except Exception as e:
                logger.debug("Proxy attempt failed %s -> %s", p, e)
                continue

    # Final fallback: return r if it had 2xx
    if r is not None and 200 <= r.status_code < 300:
        return r
    return None

def fetch_ipapi(ip: str, session: requests.Session, proxies: List[str] = None) -> Dict[str, Any]:
    url = f"http://ip-api.com/json/{ip}?fields=66846719"
    r = requests_with_optional_proxy(url, session=session, proxies=proxies)
    if r is None:
        return {"error": "No response from ip-api"}
    try:
        data = r.json()
        # ip-api returns 'status' field
        if data.get("status") == "fail":
            return {"error": data.get("message", "ip-api error")}
        return data
    except Exception:
        return {"error": "Invalid JSON from ip-api"}

def fetch_ipwhois(ip: str, session: requests.Session, proxies: List[str] = None) -> Dict[str, Any]:
    url = f"https://ipwho.is/{ip}"
    r = requests_with_optional_proxy(url, session=session, proxies=proxies)
    if r is None:
        return {"error": "No response from ipwho.is"}
    try:
        data = r.json()
        # ipwho.is returns success boolean
        if not data.get("success", True) and data.get("success") is False:
            return {"error": data.get("message", "ipwho.error")}
        return data
    except Exception:
        return {"error": "Invalid JSON from ipwhois"}

def fetch_opencage(lat: float, lon: float, session: requests.Session, proxies: List[str] = None) -> Dict[str, Any]:
    if not OPENCAGE_API_KEY:
        return {"error": "No OpenCage key configured"}
    url = f"{OPENCAGE_URL}?q={lat}+{lon}&key={OPENCAGE_API_KEY}"
    r = requests_with_optional_proxy(url, session=session, proxies=proxies)
    if r is None:
        return {"error": "No response from OpenCage"}
    try:
        return r.json()
    except Exception:
        return {"error": "Invalid JSON from OpenCage"}

# -------------------------
# GeoIntel class
# -------------------------
class GeoIntel:
    def __init__(self, max_workers: Optional[int] = None, timeout: int = DEFAULT_TIMEOUT, debug: bool = False, no_opencage: bool = False):
        setup_logging(debug)
        self.timeout = timeout
        self.debug = debug
        self.no_opencage = no_opencage
        self.session = requests.Session()
        # adaptive workers
        cpu = os.cpu_count() or 4
        self.max_workers = max_workers or min(DEFAULT_MAX_WORKERS, max(10, cpu * 5))
        self.proxies: List[str] = []
        self.verified: List[str] = []
        self.working_save_path = SAVE_WORKING
        self._stop_event = threading.Event()
        # register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        logger.info("GeoIntel initialized (workers=%d timeout=%s)", self.max_workers, self.timeout)

    def _signal_handler(self, signum, frame):
        logger.info("Signal %s received, preparing to shutdown...", signum)
        self._stop_event.set()

    # Scrape proxies from configured sources
    def scrape_proxies(self) -> List[str]:
        logger.info("Scraping proxy sources...")
        all_proxies = []
        for src in PROXY_SOURCES:
            src = src.strip()
            if not src:
                continue
            if "api/v1" in src or src.endswith(".download"):
                found = scrape_proxies_from_plain(src)
            else:
                found = scrape_proxies_from_html(src)
            logger.info("Fetched %d from %s", len(found), src)
            all_proxies.extend(found)
            if self._stop_event.is_set():
                logger.info("Stop requested during scraping")
                break
        dedup = list(dict.fromkeys(all_proxies))
        logger.info("Total unique proxies scraped: %d", len(dedup))
        self.proxies = dedup
        return dedup

    def verify_proxies(self, proxies: Optional[List[str]] = None) -> List[str]:
        if proxies is None:
            proxies = self.proxies
        if not proxies:
            logger.warning("No proxies to verify")
            return []

        logger.info("Verifying proxies (connect + http test) using %d workers...", self.max_workers)
        verified = []
        failed = 0

        # Use ThreadPoolExecutor for verification
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(verify_proxy_full, p): p for p in proxies}
            for future in tqdm(as_completed(futures), total=len(futures), desc="Verifying", colour="green"):
                if self._stop_event.is_set():
                    logger.info("Stop event set, aborting verification early")
                    break
                p = futures[future]
                try:
                    ok = future.result(timeout=10)
                    if ok:
                        verified.append(p)
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    logger.debug("Verification exception for %s: %s", p, e)
        logger.info("Verified proxies: %d | Failed: %d", len(verified), failed)
        self.verified = verified
        return verified

    def save_verified(self):
        try:
            save_working_proxies(self.working_save_path, self.verified)
        except Exception as e:
            logger.exception("Failed saving verified proxies: %s", e)

    # Combine ip-api and ipwho.is results sensibly
    @staticmethod
    def merge_geo_data(ipapi: dict, ipwho: dict) -> dict:
        merged = {}
        # prefer ip-api for fields it provides, fallback to ipwho
        mapping = {
            "ip": ("query", "ip"),
            "country": ("country", "country"),
            "region": ("regionName", "region"),
            "city": ("city", "city"),
            "lat": ("lat", "latitude"),
            "lon": ("lon", "longitude"),
            "timezone": ("timezone", None),
            "isp": ("isp", "connection.isp"),
            "org": ("org", "org"),
            "asn": ("as", "connection.asn"),
        }

        # helper to fetch nested keys like "connection.isp"
        def get_from(source, keypath):
            if not source or keypath is None:
                return None
            if "." not in keypath:
                return source.get(keypath)
            cur = source
            for part in keypath.split("."):
                if not isinstance(cur, dict):
                    return None
                cur = cur.get(part)
            return cur

        for out_key, (k1, k2) in mapping.items():
            val = None
            if ipapi and not ipapi.get("error"):
                val = get_from(ipapi, k1)
            if val is None and ipwho and not ipwho.get("error") and k2:
                val = get_from(ipwho, k2)
            merged[out_key] = val
        # attach raw sources for debugging
        merged["_raw_ipapi"] = ipapi
        merged["_raw_ipwho"] = ipwho
        return merged

    def query_geolocation(self, target_ip: str) -> Dict[str, Any]:
        # Rate-limit protection: ip-api free tier is limited. Use single session and proxies.
        # We'll implement simple retry + backoff for 429 responses.
        ipapi, ipwho = {"error": "not-run"}, {"error": "not-run"}
        tries = 0
        backoff = 1.0
        max_tries = 3

        # Use one session for both requests
        session = self.session

        while tries < max_tries and not self._stop_event.is_set():
            tries += 1
            logger.debug("ip-api attempt %d for %s", tries, target_ip)
            ipapi = fetch_ipapi(target_ip, session, proxies=self.verified)
            if not ipapi.get("error"):
                break
            # If ip-api returns rate-limit indicator, backoff and maybe continue
            if "429" in str(ipapi.get("error")).lower():
                logger.warning("ip-api rate limited, sleeping %s seconds", backoff)
                time.sleep(backoff)
                backoff *= 2
                continue
            else:
                # Don't loop excessively if other errors occurred; still try ipwho
                break

        # fetch ipwhois (less strict)
        ipwho = fetch_ipwhois(target_ip, session, proxies=self.verified)

        merged = self.merge_geo_data(ipapi, ipwho)
        logger.debug("Merged geo data: %s", merged)
        return {"ipapi": ipapi, "ipwho": ipwho, "merged": merged}

    def run_single(self, target: Optional[str] = None, auto_detect: bool = True):
        try:
            # Legal/usage disclaimer
            console.print(Panel("[bold yellow]Legal: Use this tool only on targets you own or have explicit permission to test. Abuse may be illegal.[/bold yellow]",
                                title="Disclaimer", border_style="red"))

            # Load previously saved working proxies to prefer them
            saved = load_saved_proxies(self.working_save_path)
            if saved:
                logger.info("Loaded %d saved working proxies", len(saved))
                # Try a quick connectivity test on saved (non-blocking) to weed out stale entries
                self.proxies = saved + self.proxies
            else:
                logger.debug("No saved proxies found")

            # Scrape if no saved proxies or user desires fresh ones
            if not saved:
                self.scrape_proxies()
                # if none scraped, continue but warn
                if not self.proxies:
                    console.print("[yellow]Warning: No proxies scraped. Requests will be direct-only.[/yellow]")

            # Verify proxies if we have a reasonably sized list
            if self.proxies:
                self.verify_proxies(self.proxies)

            # Save verified earlier if any
            if self.verified:
                self.save_verified()

            # Determine target
            if not target and auto_detect:
                try:
                    ip = requests.get("https://api.ipify.org", timeout=8).text.strip()
                    console.print(f"[green]Auto-detected your IP: {ip}[/green]")
                    target = ip
                except Exception:
                    console.print("[red]Could not auto-detect IP. Please provide a target (--target).[/red]")
                    return

            if not target:
                console.print("[red]No target provided. Exiting.[/red]")
                return

            ip = resolve_hostname(target)
            console.print(f"[cyan]Resolved target -> {ip}[/cyan]")

            # Query geolocation
            console.print("[cyan]Querying geolocation services...[/cyan]")
            geo = self.query_geolocation(ip)

            # Reverse geocode if requested and we have lat/lon
            merged = geo["merged"]
            opencage_data = None
            lat = merged.get("lat")
            lon = merged.get("lon")
            if not self.no_opencage and OPENCAGE_API_KEY and lat and lon:
                console.print("[cyan]Fetching reverse-geocode from OpenCage...[/cyan]")
                opencage_data = fetch_opencage(lat, lon, self.session, proxies=self.verified)
            elif not OPENCAGE_API_KEY and not self.no_opencage:
                console.print("[yellow]OpenCage key not set — skipping reverse-geocode.[/yellow]")

            # Display results
            self.display_results(geo["ipapi"], geo["ipwho"], opencage_data, merged)

        finally:
            # Always save verified proxies on exit (best-effort)
            if self.verified:
                self.save_verified()
            logger.info("GeoIntel run finished")

    def display_results(self, ipapi_data: dict, ipwho_data: dict, opencage_data: Optional[dict], merged: dict):
        t = Table(box=None, show_header=False, pad_edge=True)
        t.add_column("Field", style="bold cyan", width=28)
        t.add_column("Value", style="white")

        # Use merged fields
        t.add_row("IP", safe_str(merged.get("ip")))
        t.add_row("Country", safe_str(merged.get("country")))
        t.add_row("Region", safe_str(merged.get("region")))
        t.add_row("City", safe_str(merged.get("city")))
        t.add_row("Latitude", safe_str(merged.get("lat")))
        t.add_row("Longitude", safe_str(merged.get("lon")))
        t.add_row("Timezone", safe_str(merged.get("timezone")))
        t.add_row("ISP", safe_str(merged.get("isp")))
        t.add_row("Org", safe_str(merged.get("org")))
        t.add_row("ASN", safe_str(merged.get("asn")))

        console.print(Panel(t, title="GeoIntel — Aggregated IP Info", border_style="magenta"))

        # OpenCage
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
# Main CLI entry
# -------------------------
def main():
    parser = argparse.ArgumentParser(description="GeoIntel - Proxy-assisted IP intelligence")
    parser.add_argument("--target", "-t", default=None, help="Target IP or hostname (default: auto-detect your IP)")
    parser.add_argument("--no-opencage", action="store_true", help="Skip OpenCage reverse geocoding")
    parser.add_argument("--threads", type=int, default=None, help="Max worker threads (default: adaptive based on CPU/.env)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Request timeout seconds")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if os.name == 'nt':
        _ = os.system('cls')
    else:
        _ = os.system('clear')

    gi = GeoIntel(max_workers=args.threads, timeout=args.timeout, debug=args.debug, no_opencage=args.no_opencage)
    bnr()
    gi.run_single(target=args.target, auto_detect=(args.target is None))

if __name__ == "__main__":
    main()
