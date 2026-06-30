import { useReveal } from '../utils/reveal';

const tools = [
  ['Quick GeoIP', 'quick', 'Geolocation, ISP, organization, and ASN'],
  ['DNS Analysis', 'dns', 'A, AAAA, MX, NS, TXT, SOA, CNAME, and PTR records'],
  ['WHOIS', 'whois', 'Registrar, lifecycle dates, status, nameservers, and contacts'],
  ['TLS Certificate', 'ssl', 'Subject, issuer, validity, serial number, and SANs'],
  ['HTTP Headers', 'http', 'Response metadata and security-header coverage'],
  ['Reverse DNS', 'reverse', 'Hostname, aliases, and resolved addresses'],
  ['RDAP', 'rdap', 'Structured IP and domain registration records'],
  ['Subdomains', 'subdomains', 'Certificate-transparency names reported by crt.sh'],
  ['Email Security', 'email', 'MX, SPF, and DMARC posture'],
  ['Web Intelligence', 'web', 'Metadata, technology signals, public emails, and social links'],
  ['Public Files', 'files', 'robots.txt, sitemap.xml, and security.txt'],
  ['Port & Service Scan', 'ports', 'TCP ports 1–1024, selected high ports, and banners'],
  ['Connectivity', 'connectivity', 'TCP reachability and latency for common services'],
  ['DNS Zone Transfer', 'zone_transfer', 'AXFR exposure on authoritative nameservers'],
];

export default function DocsPage() {
  const sectionsRef = useReveal<HTMLDivElement>({ stagger: 0.1 });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-14 sm:py-20">
      <div className="mb-14 max-w-3xl">
        <div className="eyebrow">Documentation</div>
        <h1 className="page-title">Use GeoIntel with confidence.</h1>
        <p className="page-lead">Set up the application, choose the right collector, use the CLI and API, and understand which checks generate active network traffic.</p>
      </div>

      <div className="grid lg:grid-cols-[220px_1fr] gap-10 lg:gap-16 items-start">
        <aside className="hidden lg:block sticky top-24 text-xs">
          <nav aria-label="Documentation sections" className="space-y-1">
            {['Quick start', 'Workflow', 'Collectors', 'CLI', 'API', 'Results and errors', 'Safety'].map((name) => (
              <a key={name} href={`#${name.toLowerCase().replaceAll(' ', '-')}`} className="block px-3 py-2 rounded-md hover:bg-white/5" style={{ color: 'var(--color-charcoal)' }}>{name}</a>
            ))}
          </nav>
        </aside>

        <article ref={sectionsRef} className="docs-prose min-w-0">
          <section id="quick-start">
            <h2>Quick start</h2>
            <p>Install the Python dependencies, build the frontend, and start FastAPI from the repository root.</p>
            <pre><code>{`python -m pip install -r requirements.txt
cd frontend
npm install
npm run build
cd ..
uvicorn app.main:app --reload`}</code></pre>
            <p>Open <a href="http://127.0.0.1:8000">http://127.0.0.1:8000</a>. The OpenAPI interface is available separately at <a href="/api/docs">/api/docs</a>.</p>
          </section>

          <section id="workflow">
            <h2>Dashboard workflow</h2>
            <ol>
              <li>Enter a public IP address, domain, or URL.</li>
              <li>GeoIntel resolves the target and displays the initial geolocation result.</li>
              <li>Select one intelligence module. Only that collector runs.</li>
              <li>Review the formatted result or export the initial GeoIP record as JSON or CSV.</li>
            </ol>
            <div className="notice"><strong>Optional enrichment:</strong> Add an OpenCage key from the settings menu to display timezone, currency, formatted address, and confidence. The key is held in memory for the session and never persisted to disk or storage.</div>
          </section>

          <section id="collectors">
            <h2>Collectors</h2>
            <p>Domain-only collectors report a clear error when given an IP address. Web probes and active checks reject private, loopback, reserved, and otherwise non-public destinations.</p>
            <div className="overflow-x-auto rounded-xl border" style={{ borderColor: 'var(--color-hairline)' }}>
              <table>
                <thead><tr><th>Tool</th><th>API ID</th><th>What it returns</th></tr></thead>
                <tbody>{tools.map(([name, id, description]) => <tr key={id}><td>{name}</td><td><code>{id}</code></td><td>{description}</td></tr>)}</tbody>
              </table>
            </div>
          </section>

          <section id="cli">
            <h2>Command line</h2>
            <pre><code>geointel lookup --target TARGET [-t TYPE] [--json | --simple | --csv] [--opencage-key KEY] [--no-logo]</code></pre>
            <h3>Examples</h3>
            <pre><code>{`# DNS records in the default readable format
geointel lookup --target example.com -t dns

# Multi-type scan (runs types concurrently)
geointel lookup --target example.com -t dns,whois,ssl

# Active port and service scan
geointel lookup --target example.com -t ports

# All collectors as formatted JSON
geointel lookup --target example.com -t full --json

# Export quick GeoIP as CSV
geointel lookup --target 8.8.8.8 -t quick --csv

# View scan history
geointel history`}</code></pre>
            <p>Run <code>geointel lookup --help</code> for the scan types supported by your installed version.</p>
          </section>

          <section id="api">
            <h2>HTTP API</h2>
            <h3>List collectors</h3>
            <pre><code>curl http://127.0.0.1:8000/scan-types</code></pre>
            <h3>Run one collector</h3>
            <pre><code>{`curl -X POST http://127.0.0.1:8000/scan \\
  -H 'Content-Type: application/json' \\
  -d '{"target":"example.com","scan_type":"dns"}'`}</code></pre>
            <h3>Run every collector</h3>
            <pre><code>{`curl -X POST http://127.0.0.1:8000/full-scan \\
  -H 'Content-Type: application/json' \\
  -d '{"target":"example.com"}'`}</code></pre>
            <div className="overflow-x-auto rounded-xl border" style={{ borderColor: 'var(--color-hairline)' }}>
              <table><thead><tr><th>Endpoint</th><th>Method</th><th>Purpose</th></tr></thead><tbody>
                <tr><td><code>/scan-types</code></td><td>GET</td><td>List UI metadata for every scan mode.</td></tr>
                <tr><td><code>/lookup</code></td><td>POST</td><td>Run the initial GeoIP lookup.</td></tr>
                <tr><td><code>/scan</code></td><td>POST</td><td>Run one collector by ID.</td></tr>
                <tr><td><code>/full-scan</code></td><td>POST</td><td>Run collectors concurrently and preserve partial results.</td></tr>
                <tr><td><code>/geocode</code></td><td>POST</td><td>Reverse-geocode lat/lon via OpenCage (key passed in body, never stored).</td></tr>
              </tbody></table>
            </div>
          </section>

          <section id="results-and-errors">
            <h2>Results and errors</h2>
            <p>A single scan returns that collector's result directly. Invalid targets, incompatible target types, and failed upstream requests return an HTTP error with a <code>detail</code> message.</p>
            <p>A full scan separates successful data under <code>results</code> from collector failures under <code>errors</code>. One unavailable source does not discard successful results from the others.</p>
          </section>

          <section id="safety">
            <h2>Active checks and authorization</h2>
            <p>Port scanning, service-banner collection, connectivity measurement, and DNS zone-transfer checks create traffic on the target network. Use them only on systems you own or have explicit permission to test.</p>
            <p>GeoIntel does not exploit services, brute-force credentials, or bypass access controls. Read the <a href="/terms">terms and acceptable-use policy</a> before exposing an installation to other users.</p>
          </section>
        </article>
      </div>
    </div>
  );
}
