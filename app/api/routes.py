from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.scanner import (
    quick_scan, full_scan as run_full_scan, SCAN_TYPES,
)

router = APIRouter(prefix="/api")


class LookupPayload(BaseModel):
    target: str


class ScanPayload(BaseModel):
    target: str
    scan_type: str = "quick"


@router.post("/lookup")
def lookup(payload: LookupPayload):
    return quick_scan(payload.target)


@router.post("/scan")
def scan(payload: ScanPayload):
    if payload.scan_type not in SCAN_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scan type '{payload.scan_type}'. Available: {', '.join(SCAN_TYPES.keys())}",
        )
    try:
        result = SCAN_TYPES[payload.scan_type](payload.target)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/full-scan")
def full_scan(payload: LookupPayload):
    try:
        return run_full_scan(payload.target)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/scan-types")
def scan_types():
    return {
        "types": [
            {
                "id": "quick",
                "name": "Quick GeoIP",
                "description": "Basic geolocation and network provider info",
                "icon": "MapPin",
            },
            {
                "id": "dns",
                "name": "DNS Analysis",
                "description": "A, AAAA, MX, NS, TXT, SOA, CNAME, PTR records",
                "icon": "Network",
            },
            {
                "id": "whois",
                "name": "WHOIS Lookup",
                "description": "Domain registration, registrar, expiry, name servers",
                "icon": "FileText",
            },
            {
                "id": "ssl",
                "name": "SSL/TLS Certificate",
                "description": "Certificate issuer, subject, validity, SANs",
                "icon": "Shield",
            },
            {
                "id": "http",
                "name": "HTTP Headers",
                "description": "Server info, security headers, status codes",
                "icon": "Globe",
            },
            {
                "id": "reverse",
                "name": "Reverse DNS",
                "description": "PTR records and hostname resolution",
                "icon": "Search",
            },
            {
                "id": "full",
                "name": "Full Recon",
                "description": "All scans combined in one comprehensive report",
                "icon": "Crosshair",
            },
            {"id": "rdap", "name": "RDAP", "description": "IP and domain registration data", "icon": "FileText"},
            {"id": "subdomains", "name": "Subdomains", "description": "Certificate transparency discoveries", "icon": "Network"},
            {"id": "email", "name": "Email Security", "description": "MX, SPF, and DMARC posture", "icon": "Shield"},
            {"id": "web", "name": "Web Intelligence", "description": "Metadata, technologies, emails, and social links", "icon": "Globe"},
            {"id": "files", "name": "Public Files", "description": "robots.txt, sitemap, and security.txt", "icon": "Search"},
            {"id": "ports", "name": "Port & Service Scan", "description": "TCP ports 1-1024, high-value ports, and service banners", "icon": "Network"},
            {"id": "connectivity", "name": "Connectivity", "description": "TCP reachability and latency for common services", "icon": "Activity"},
            {"id": "zone_transfer", "name": "DNS Zone Transfer", "description": "Check authoritative nameservers for AXFR exposure", "icon": "Shield"},
        ]
    }
