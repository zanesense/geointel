import app.services.scanner as scanner
from app.services.scanner import _PageIntelParser, normalize_target


def test_normalize_target():
    assert normalize_target("HTTPS://Example.COM:443/path?q=1") == "example.com"
    assert normalize_target("8.8.8.8") == "8.8.8.8"


def test_page_parser():
    parser = _PageIntelParser()
    parser.feed('<title> Acme </title><meta name="description" content="Example"><a href="https://github.com/acme">GitHub</a>')
    assert parser.title.strip() == "Acme"
    assert parser.meta["description"] == "Example"
    assert "https://github.com/acme" in parser.links


def test_full_scan_keeps_partial_results():
    original_types, original_resolve = scanner.SCAN_TYPES, scanner.resolve_domain
    scanner.SCAN_TYPES = {"ok": lambda _: {"value": 1}, "bad": lambda _: {"error": "unavailable"}}
    scanner.resolve_domain = lambda _: "203.0.113.1"
    try:
        result = scanner.full_scan("example.com")
        assert result["results"] == {"ok": {"value": 1}}
        assert result["errors"] == {"bad": "unavailable"}
    finally:
        scanner.SCAN_TYPES, scanner.resolve_domain = original_types, original_resolve


def test_private_web_targets_are_rejected():
    try:
        scanner._require_public_host("127.0.0.1")
    except ValueError:
        return
    raise AssertionError("private target accepted")


def test_port_probe_formats_json_result():
    original_connect, original_service = scanner.socket.create_connection, scanner.socket.getservbyport

    class Connection:
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def settimeout(self, *_): pass
        def sendall(self, *_): pass
        def recv(self, *_): return b"HTTP/1.0 200 OK\r\n"

    scanner.socket.create_connection = lambda *_args, **_kwargs: Connection()
    scanner.socket.getservbyport = lambda *_: "https"
    try:
        assert scanner._probe_port("example.com", 443) == {"port": 443, "service": "https", "state": "open", "banner": "HTTP/1.0 200 OK"}
    finally:
        scanner.socket.create_connection, scanner.socket.getservbyport = original_connect, original_service
