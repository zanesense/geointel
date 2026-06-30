import { useReveal } from '../utils/reveal';

export default function TermsPage() {
  const sectionsRef = useReveal<HTMLDivElement>({ stagger: 0.08 });

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-14 sm:py-20">
      <div className="eyebrow">Legal</div>
      <h1 className="page-title">Terms and acceptable use.</h1>
      <p className="page-lead">These terms describe the intended use and operational limits of this GeoIntel installation.</p>

      <article ref={sectionsRef} className="docs-prose mt-14">
        <section><h2>Authorized use</h2><p>You may use GeoIntel for research, administration, defensive security, and testing of systems you own or are explicitly authorized to assess. You are responsible for obtaining permission and following applicable laws, contracts, and provider terms.</p></section>
        <section><h2>Prohibited use</h2><p>Do not use GeoIntel to disrupt services, evade access controls, collect credentials, exploit vulnerabilities, harass third parties, or scan systems when you do not have permission. Do not use results as the sole basis for high-impact decisions about a person or organization.</p></section>
        <section><h2>Active network traffic</h2><p>Port scans, service-banner collection, connectivity checks, HTTP requests, TLS connections, and DNS zone-transfer checks contact target infrastructure. These actions may appear in target logs and can trigger monitoring or rate limits.</p></section>
        <section><h2>Third-party data</h2><p>GeoIntel queries external services and public infrastructure, including GeoIP, DNS, WHOIS, RDAP, certificate-transparency, mapping, and website endpoints. Their availability, accuracy, retention, and terms are controlled by their operators. Results can be incomplete, stale, or incorrect.</p></section>
        <section id="privacy"><h2>Privacy</h2><p>The application does not implement user accounts or a server-side scan-history database. Recent targets and an optional OpenCage key are held in the browser; the key is stored in local storage and sent directly to OpenCage when enrichment is enabled. Requests and targets may still appear in application, proxy, DNS, target, and third-party provider logs.</p></section>
        <section><h2>No warranty</h2><p>GeoIntel is provided as-is. Do not rely on it as the only source for security, availability, identity, ownership, or location decisions. Verify important findings through authoritative sources and approved testing procedures.</p></section>
        <section><h2>Changes</h2><p>Features, data providers, limits, and these terms may change as the project evolves. Stop using the application if you do not agree with the current terms.</p></section>
      </article>
    </div>
  );
}
