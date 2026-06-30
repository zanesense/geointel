import type { FullScanResult } from '../types';
import QuickScanResult from './QuickScanResult';
import DnsView from './DnsView';
import WhoisView from './WhoisView';
import SslView from './SslView';
import HttpView from './HttpView';
import ReverseDnsView from './ReverseDnsView';

interface FullScanViewProps {
  data: FullScanResult;
}

const label = (key: string) => key.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());

function FormattedValue({ value }: { value: unknown }) {
  if (value === null || value === undefined || value === '') {
    return <span style={{ color: 'var(--color-ash)' }}>—</span>;
  }
  if (Array.isArray(value)) {
    if (!value.length) return <span style={{ color: 'var(--color-ash)' }}>None</span>;
    return (
      <div className="space-y-2">
        {value.map((item, index) => (
          <div key={index} className={typeof item === 'object' ? 'card p-3' : ''}>
            <FormattedValue value={item} />
          </div>
        ))}
      </div>
    );
  }
  if (typeof value === 'object') {
    return (
      <dl className="hairline-grid rounded-lg overflow-hidden">
        {Object.entries(value as Record<string, unknown>).map(([key, item]) => (
          <div key={key} className="grid grid-cols-1 sm:grid-cols-[180px_1fr] gap-2 px-4 py-3" style={{ background: 'var(--color-surface-card)' }}>
            <dt className="text-xs" style={{ color: 'var(--color-charcoal)', fontFamily: 'var(--font-body)' }}>{label(key)}</dt>
            <dd className="text-xs break-words min-w-0" style={{ color: 'var(--color-ink)', fontFamily: 'var(--font-mono)' }}><FormattedValue value={item} /></dd>
          </div>
        ))}
      </dl>
    );
  }
  return <span>{typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}</span>;
}

export default function FullScanView({ data }: FullScanViewProps) {
  const sections: { key: string; label: string; node: React.ReactNode }[] = [];

  if (data.results.quick) sections.push({ key: 'quick', label: 'GeoIP Location', node: <QuickScanResult result={data.results.quick} /> });
  if (data.results.dns) sections.push({ key: 'dns', label: 'DNS Analysis', node: <DnsView data={data.results.dns} /> });
  if (data.results.whois) sections.push({ key: 'whois', label: 'WHOIS', node: <WhoisView data={data.results.whois} /> });
  if (data.results.ssl) sections.push({ key: 'ssl', label: 'SSL/TLS', node: <SslView data={data.results.ssl} /> });
  if (data.results.http) sections.push({ key: 'http', label: 'HTTP Headers', node: <HttpView data={data.results.http} /> });
  if (data.results.reverse) sections.push({ key: 'reverse', label: 'Reverse DNS', node: <ReverseDnsView data={data.results.reverse} /> });
  for (const [key, label] of Object.entries({ rdap: 'RDAP Registration', subdomains: 'Certificate Transparency', email: 'Email Security', web: 'Web Intelligence', files: 'Public Files', ports: 'Open TCP Ports & Services', connectivity: 'Service Connectivity', zone_transfer: 'DNS Zone Transfer' })) {
    const value = data.results[key as keyof typeof data.results];
    if (value) sections.push({
      key,
      label,
      node: <FormattedValue value={value} />,
    });
  }

  return (
    <div className="space-y-10">
      {data.errors && Object.keys(data.errors).length > 0 && (
        <div className="card p-5" style={{ border: '1px solid rgba(255,32,71,0.3)' }}>
          <p className="text-sm font-medium mb-2" style={{ color: 'var(--color-accent-yellow)', fontFamily: 'var(--font-body)' }}>Scan Errors</p>
          {Object.entries(data.errors).map(([k, msg]) => (
            <p key={k} className="text-sm" style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-body)' }}>
              <span style={{ color: 'var(--color-accent-yellow)' }}>{k}:</span> {msg}
            </p>
          ))}
        </div>
      )}

      {sections.map((s) => (
        <div key={s.key}>
          <p className="text-sm font-medium mb-4" style={{ color: 'var(--color-ink)', fontFamily: 'var(--font-body)' }}>{s.label}</p>
          {s.node}
        </div>
      ))}
    </div>
  );
}
