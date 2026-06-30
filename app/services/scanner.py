import socket
import ipaddress
import re
import time
import dns.resolver
import dns.reversename
import dns.query
import dns.zone
import ssl
import whois
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests


HIGH_VALUE_TCP_PORTS = (1433, 1521, 2049, 2375, 3000, 3306, 3389, 5432, 5900, 6379, 8000, 8080, 8443, 8888, 9200, 11211, 27017)
TCP_SCAN_PORTS = tuple(range(1, 1025)) + HIGH_VALUE_TCP_PORTS


def normalize_target(target: str) -> str:
    """Return a hostname/IP from a hostname, IP, or URL."""
    value = target.strip()
    if not value:
        raise ValueError("Target is required")
    parsed = urlparse(value if "://" in value else f"//{value}")
    host = parsed.hostname
    if not host or len(host) > 253:
        raise ValueError("Enter a valid IP address, domain, or URL")
    return host.rstrip(".").lower()


def _is_ip(target: str) -> bool:
    try:
        ipaddress.ip_address(target)
        return True
    except ValueError:
        return False


def _require_public_host(target: str) -> str:
    host = normalize_target(target)
    addresses = {item[4][0] for item in socket.getaddrinfo(host, None)}
    if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
        raise ValueError("Web probes are limited to public internet targets")
    return host


def _public_get(url: str, **kwargs):
    """GET while re-validating every redirect to avoid probing private hosts."""
    for _ in range(6):
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
            raise ValueError("Unsafe web URL")
        _require_public_host(parsed.hostname or "")
        response = requests.get(url, allow_redirects=False, **kwargs)
        if response.is_redirect:
            url = urljoin(url, response.headers["location"])
            continue
        return response
    raise ValueError("Too many redirects")


def resolve_domain(target: str) -> str:
    try:
        return socket.gethostbyname(normalize_target(target))
    except Exception:
        return target


def quick_scan(target: str) -> dict:
    import requests as http
    ip = resolve_domain(target)
    url = f"http://ip-api.com/json/{ip}?fields=status,message,continent,country,regionName,city,lat,lon,isp,org,as,query"
    r = http.get(url, timeout=10)
    data = r.json()
    if data.get("status") != "success":
        return {"error": data.get("message", "GeoIP lookup failed")}
    return {
        "ip": data.get("query"),
        "continent": data.get("continent"),
        "country": data.get("country"),
        "region": data.get("regionName"),
        "city": data.get("city"),
        "lat": data.get("lat"),
        "lon": data.get("lon"),
        "isp": data.get("isp"),
        "org": data.get("org"),
        "asn": data.get("as"),
    }


DNS_RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME", "PTR"]


def dns_lookup(target: str) -> dict:
    results = {}
    hostname = normalize_target(target)
    for rtype in DNS_RECORD_TYPES:
        try:
            if rtype == "PTR":
                try:
                    ip = resolve_domain(target)
                    rev = dns.reversename.from_address(ip)
                    answers = dns.resolver.resolve(rev, "PTR")
                    results["PTR"] = [str(a) for a in answers]
                except Exception:
                    results["PTR"] = []
                continue
            answers = dns.resolver.resolve(hostname, rtype)
            vals = [str(a) for a in answers]
            if rtype == "MX":
                vals = [str(a) for a in sorted(answers, key=lambda x: x.preference)]
            elif rtype == "SOA":
                vals = [str(a).replace(" ", "  ") for a in answers]
            results[rtype] = vals
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
            results[rtype] = []
        except Exception as e:
            results[rtype] = [f"error: {str(e)}"]
    return results


def whois_lookup(target: str) -> dict:
    try:
        target = normalize_target(target)
        if _is_ip(target):
            return {"error": "WHOIS lookup requires a domain; use RDAP for IP registration"}
        w = whois.whois(target)
        result = {}
        for key in ["domain_name", "registrar", "whois_server", "creation_date",
                     "expiration_date", "updated_date", "name_servers", "status",
                     "emails", "org", "country", "city", "address"]:
            val = getattr(w, key, None)
            if val:
                if isinstance(val, list):
                    result[key] = [str(v) for v in val]
                elif isinstance(val, datetime):
                    result[key] = val.isoformat()
                else:
                    result[key] = str(val)
        return result
    except Exception as e:
        return {"error": str(e)}


def ssl_lookup(target: str) -> dict:
    try:
        hostname = _require_public_host(target)
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
            s.settimeout(8)
            s.connect((hostname, 443))
            cert = s.getpeercert()
        if not cert:
            return {"error": "No certificate returned"}
        subject = dict(cert.get("subject", [[["", ""]]])[0])
        issuer = dict(cert.get("issuer", [[["", ""]]])[0])
        sans = []
        for ext in cert.get("subjectAltName", []):
            sans.append(f"{ext[0]}: {ext[1]}")
        not_before = cert.get("notBefore", "")
        not_after = cert.get("notAfter", "")
        return {
            "subject": subject.get("commonName", ""),
            "issuer": issuer.get("organizationName", issuer.get("commonName", "")),
            "serial": str(cert.get("serialNumber", "")),
            "version": cert.get("version", ""),
            "not_before": not_before,
            "not_after": not_after,
            "sans": sans,
            "fingerprint": "",
        }
    except Exception as e:
        return {"error": str(e)}


def http_headers_lookup(target: str) -> dict:
    try:
        hostname = _require_public_host(target)
        url = f"https://{hostname}"
        r = _public_get(url, timeout=10)
        headers = dict(r.headers)
        security = {}
        sec_headers = [
            "Strict-Transport-Security", "Content-Security-Policy",
            "X-Frame-Options", "X-Content-Type-Options",
            "X-XSS-Protection", "Referrer-Policy",
            "Permissions-Policy", "Cross-Origin-Opener-Policy",
        ]
        for h in sec_headers:
            val = headers.get(h, headers.get(h.lower(), None))
            security[h] = val if val else "Not set"
        return {
            "status_code": r.status_code,
            "server": headers.get("Server", headers.get("server", "Unknown")),
            "content_type": headers.get("Content-Type", ""),
            "security": security,
            "all_headers": {k: v for k, v in sorted(headers.items())},
            "final_url": r.url,
        }
    except Exception as e:
        return {"error": str(e)}


def reverse_dns_lookup(target: str) -> dict:
    try:
        ip = resolve_domain(target)
        hostname, aliases, ips = socket.gethostbyaddr(ip)
        return {
            "hostname": hostname,
            "aliases": aliases,
            "ips": ips,
        }
    except Exception as e:
        return {"error": str(e)}


def rdap_lookup(target: str) -> dict:
    """Registration data for both IP addresses and domains."""
    try:
        host = normalize_target(target)
        kind = "ip" if _is_ip(host) else "domain"
        response = requests.get(f"https://rdap.org/{kind}/{host}", timeout=12)
        response.raise_for_status()
        data = response.json()
        entities = []
        for entity in data.get("entities", []):
            card = entity.get("vcardArray", [None, []])
            names = [row[3] for row in card[1] if row and row[0] in {"fn", "org"}] if len(card) > 1 else []
            entities.append({"roles": entity.get("roles", []), "names": names})
        return {
            "handle": data.get("handle"),
            "name": data.get("ldhName") or data.get("name"),
            "status": data.get("status", []),
            "country": data.get("country"),
            "start_address": data.get("startAddress"),
            "end_address": data.get("endAddress"),
            "events": data.get("events", []),
            "nameservers": [n.get("ldhName") for n in data.get("nameservers", [])],
            "entities": entities,
        }
    except Exception as e:
        return {"error": str(e)}


def subdomain_lookup(target: str) -> dict:
    """Passive subdomains observed in certificate transparency logs."""
    try:
        host = normalize_target(target)
        if _is_ip(host):
            raise ValueError("Certificate transparency lookup requires a domain")
        response = requests.get("https://crt.sh/", params={"q": f"%.{host}", "output": "json"}, timeout=15)
        response.raise_for_status()
        names = {
            name.strip().lower().removeprefix("*.")
            for row in response.json()
            for name in row.get("name_value", "").splitlines()
            if name.strip().lower().endswith(host)
        }
        return {"count": len(names), "subdomains": sorted(names)[:500], "truncated": len(names) > 500}
    except Exception as e:
        return {"error": str(e)}


def email_security_lookup(target: str) -> dict:
    """Mail routing and anti-spoofing posture."""
    try:
        host = normalize_target(target)
        if _is_ip(host):
            raise ValueError("Email security lookup requires a domain")

        def records(name: str, kind: str) -> list[str]:
            try:
                return [str(answer).strip('"') for answer in dns.resolver.resolve(name, kind)]
            except Exception:
                return []

        txt = records(host, "TXT")
        dmarc = records(f"_dmarc.{host}", "TXT")
        return {
            "mx": records(host, "MX"),
            "spf": [value for value in txt if value.lower().startswith("v=spf1")],
            "dmarc": [value for value in dmarc if value.lower().startswith("v=dmarc1")],
            "has_spf": any(value.lower().startswith("v=spf1") for value in txt),
            "has_dmarc": any(value.lower().startswith("v=dmarc1") for value in dmarc),
        }
    except Exception as e:
        return {"error": str(e)}


class _PageIntelParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self._in_title = False
        self.meta = {}
        self.links = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta" and attrs.get("content"):
            key = attrs.get("name") or attrs.get("property")
            if key in {"description", "generator", "og:title", "og:description"}:
                self.meta[key] = attrs["content"]
        elif tag == "a" and attrs.get("href", "").startswith(("http://", "https://")):
            self.links.add(attrs["href"])

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def web_intel_lookup(target: str) -> dict:
    """Public homepage metadata and lightweight technology signals."""
    try:
        host = _require_public_host(target)
        response = _public_get(f"https://{host}", timeout=12)
        response.raise_for_status()
        parser = _PageIntelParser()
        parser.feed(response.text[:2_000_000])
        haystack = (response.text[:500_000] + str(response.headers)).lower()
        signatures = {
            "WordPress": "wp-content", "Drupal": "drupal", "Shopify": "cdn.shopify.com",
            "React": "react", "Next.js": "__next", "Vue": "vue", "Cloudflare": "cloudflare",
            "Google Analytics": "googletagmanager.com", "Bootstrap": "bootstrap",
        }
        social_hosts = ("github.com", "linkedin.com", "twitter.com", "x.com", "facebook.com", "instagram.com", "youtube.com")
        return {
            "final_url": response.url,
            "title": parser.title.strip(),
            "metadata": parser.meta,
            "technologies": [name for name, marker in signatures.items() if marker in haystack],
            "emails": sorted(set(re.findall(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", response.text, re.I)))[:100],
            "social_links": sorted(link for link in parser.links if any(site in link for site in social_hosts))[:100],
        }
    except Exception as e:
        return {"error": str(e)}


def public_files_lookup(target: str) -> dict:
    """Discover standard public metadata files without crawling."""
    try:
        host = _require_public_host(target)
        found = {}
        for path in ("/robots.txt", "/sitemap.xml", "/.well-known/security.txt"):
            response = _public_get(f"https://{host}{path}", timeout=8)
            if response.ok:
                found[path] = {"url": response.url, "content_type": response.headers.get("content-type"), "preview": response.text[:1000]}
        return {"found": found}
    except Exception as e:
        return {"error": str(e)}


def _probe_port(host: str, port: int) -> dict | None:
    try:
        with socket.create_connection((host, port), timeout=0.4) as connection:
            try:
                service = socket.getservbyport(port, "tcp")
            except OSError:
                service = "unknown"
            connection.settimeout(0.35)
            try:
                if port in {80, 8000, 8080, 8888}:
                    connection.sendall(f"HEAD / HTTP/1.0\r\nHost: {host}\r\n\r\n".encode())
                banner = connection.recv(256).decode("utf-8", "replace").strip().splitlines()[0][:160]
            except OSError:
                banner = ""
            return {"port": port, "service": service, "state": "open", "banner": banner or None}
    except OSError:
        return None


def port_scan(target: str) -> dict:
    """Actively test a bounded set of common TCP ports on a public target."""
    try:
        host = _require_public_host(target)
        with ThreadPoolExecutor(max_workers=128) as pool:
            open_ports = [result for result in pool.map(lambda port: _probe_port(host, port), TCP_SCAN_PORTS) if result]
        return {
            "host": host,
            "range": "1-1024 plus selected high-value service ports",
            "scanned_count": len(TCP_SCAN_PORTS),
            "open_count": len(open_ports),
            "open_ports": open_ports,
        }
    except Exception as e:
        return {"error": str(e)}


def connectivity_lookup(target: str) -> dict:
    """Measure TCP reachability and connection time for common services."""
    try:
        host = _require_public_host(target)
        checks = {"ssh": 22, "smtp": 25, "dns": 53, "http": 80, "https": 443}

        def check(item):
            service, port = item
            started = time.perf_counter()
            try:
                with socket.create_connection((host, port), timeout=1):
                    return service, {"port": port, "reachable": True, "latency_ms": round((time.perf_counter() - started) * 1000, 1)}
            except OSError:
                return service, {"port": port, "reachable": False, "latency_ms": None}

        with ThreadPoolExecutor(max_workers=len(checks)) as pool:
            return {"host": host, "services": dict(pool.map(check, checks.items()))}
    except Exception as e:
        return {"error": str(e)}


def zone_transfer_lookup(target: str) -> dict:
    """Check whether authoritative DNS servers permit AXFR zone transfers."""
    try:
        host = normalize_target(target)
        if _is_ip(host):
            raise ValueError("Zone transfer checks require a domain")
        nameservers = [str(answer).rstrip(".") for answer in dns.resolver.resolve(host, "NS")]
        results = []
        for nameserver in nameservers:
            try:
                _require_public_host(nameserver)
                zone = dns.zone.from_xfr(dns.query.xfr(nameserver, host, lifetime=4))
                results.append({"nameserver": nameserver, "allowed": True, "record_names": len(zone.nodes)})
            except Exception:
                results.append({"nameserver": nameserver, "allowed": False, "record_names": 0})
        return {"domain": host, "transfer_allowed": any(item["allowed"] for item in results), "nameservers": results}
    except Exception as e:
        return {"error": str(e)}


SCAN_TYPES = {
    "quick": quick_scan,
    "dns": dns_lookup,
    "whois": whois_lookup,
    "ssl": ssl_lookup,
    "http": http_headers_lookup,
    "reverse": reverse_dns_lookup,
    "rdap": rdap_lookup,
    "subdomains": subdomain_lookup,
    "email": email_security_lookup,
    "web": web_intel_lookup,
    "files": public_files_lookup,
    "ports": port_scan,
    "connectivity": connectivity_lookup,
    "zone_transfer": zone_transfer_lookup,
}


def full_scan(target: str) -> dict:
    """Run independent intelligence collectors concurrently."""
    target = normalize_target(target)
    results, errors = {}, {}
    with ThreadPoolExecutor(max_workers=min(8, len(SCAN_TYPES))) as pool:
        futures = {pool.submit(fn, target): name for name, fn in SCAN_TYPES.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                data = future.result()
                (errors if "error" in data else results)[name] = data.get("error") if "error" in data else data
            except Exception as e:
                errors[name] = str(e)
    return {"target": target, "resolved_ip": resolve_domain(target), "results": results, "errors": errors or None}
