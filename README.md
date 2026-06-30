# GeoIntel

An IP and domain OSINT workspace with a web dashboard, JSON API, and command-line interface.

GeoIntel combines common infrastructure lookups in one local application. Start with geolocation, then run DNS, registration, certificate, web, email-security, public-file, or TCP-port checks individually. The full-scan API and CLI mode can run every collector concurrently.

## Installation

You need Python 3.10+ and Node.js 20+.

Install the Python dependencies from the project root:

```bash
python -m pip install -r requirements.txt
```

Build the React frontend with npm. This repository includes `package-lock.json`, so npm is the supported package manager for these commands.

```bash
cd frontend
npm install
npm run build
cd ..
```

## Quick start

Start the API and built dashboard:

```bash
uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Enter an IP address, domain, or URL. After the initial GeoIP result appears, choose an intelligence module to run only that collector.

For command-line use:

```bash
python -m app example.com -t dns
```

## Collectors

| ID | Operation | Target |
|---|---|---|
| `quick` | IP geolocation, ISP, organization, and ASN | IP or domain |
| `dns` | A, AAAA, MX, NS, TXT, SOA, CNAME, and PTR records | IP or domain |
| `whois` | Registrar, dates, status, nameservers, and contacts | Domain |
| `ssl` | Certificate subject, issuer, validity, and SANs | Public domain |
| `http` | Response and security headers | Public domain |
| `reverse` | Reverse DNS hostname and aliases | IP or domain |
| `rdap` | Structured IP or domain registration records | IP or domain |
| `subdomains` | Certificate-transparency subdomains from crt.sh | Domain |
| `email` | MX, SPF, and DMARC posture | Domain |
| `web` | Page metadata, technology signals, public emails, and social links | Public domain |
| `files` | `robots.txt`, `sitemap.xml`, and `security.txt` | Public domain |
| `ports` | TCP ports 1–1024, selected higher-value ports, and service banners | Public IP or domain |
| `connectivity` | TCP reachability and latency for SSH, SMTP, DNS, HTTP, and HTTPS | Public IP or domain |
| `zone_transfer` | AXFR exposure checks against authoritative nameservers | Domain |

`full` is available through the CLI and `/full-scan` API. The dashboard intentionally runs one selected collector at a time.

## CLI

```text
python -m app TARGET [-t TYPE] [--json | --simple]
```

Examples:

```bash
# Human-readable GeoIP lookup
python -m app 8.8.8.8

# Active common-port scan
python -m app example.com -t ports

# Every collector with formatted JSON output
python -m app example.com -t full --json

# Flat key/value output
python -m app example.com -t rdap --simple
```

Run `python -m app --help` to see the scan types available in the installed version.

## API

### List scan types

```bash
curl http://127.0.0.1:8000/scan-types
```

### Run one collector

```bash
curl -X POST http://127.0.0.1:8000/scan \
  -H 'Content-Type: application/json' \
  -d '{"target":"example.com","scan_type":"dns"}'
```

### Run all collectors

```bash
curl -X POST http://127.0.0.1:8000/full-scan \
  -H 'Content-Type: application/json' \
  -d '{"target":"example.com"}'
```

Full scans return successful collectors under `results` and unavailable collectors under `errors`, so one upstream failure does not discard the rest of the report.

## Development

Run the backend:

```bash
uvicorn app.main:app --reload
```

In a second terminal, run Vite:

```bash
cd frontend
npm run dev
```

The development frontend uses `http://localhost:8000` for API requests. Before serving the application through FastAPI, rebuild `frontend/dist`:

```bash
cd frontend
npm run build
```

Available frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

The small backend checks can run without a test framework:

```bash
python -c "from test_scanner import *; test_normalize_target(); test_page_parser(); test_full_scan_keeps_partial_results(); test_private_web_targets_are_rejected(); test_port_probe_formats_json_result()"
```

## Optional OpenCage enrichment

The settings button in the dashboard accepts an OpenCage API key. When configured, GeoIP results also show timezone, UTC offset, currency, formatted address, and confidence. The key is stored in your browser's local storage and sent directly to OpenCage by the frontend.

GeoIntel's core collectors do not require this key.

## Safety and scope

GeoIntel rejects loopback, private, reserved, and otherwise non-public addresses for web probes and port scanning. Redirects are revalidated before the application follows them.

Port scanning, banner collection, connectivity checks, and zone-transfer checks are active. Port coverage is restricted to TCP ports 1–1024 plus a fixed list of higher-value service ports, all with short timeouts. Only scan systems you own or have permission to test. GeoIntel does not exploit services, brute-force accounts, or bypass access controls.

External services can rate-limit or temporarily reject requests. A failed source appears as an error for that collector rather than a fabricated result.

## Troubleshooting

### The dashboard returns 404 or a blank page

Build the frontend before starting FastAPI:

```bash
cd frontend
npm install
npm run build
```

### A collector returns an error

Confirm the target is public and appropriate for the collector. WHOIS, subdomain, and email-security lookups require a domain. Network sources such as crt.sh, RDAP servers, DNS resolvers, and target websites must also be reachable from the backend host.

### Port 8000 is already in use

Choose another port:

```bash
uvicorn app.main:app --port 8080
```

When using Vite development mode, update `frontend/src/api.ts` if the backend no longer runs on port 8000.
