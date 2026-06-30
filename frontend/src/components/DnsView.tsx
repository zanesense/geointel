import type { DnsResult } from '../types';

interface DnsViewProps {
  data: DnsResult;
}

const meta: Record<string, string> = {
  A: 'A (IPv4)', AAAA: 'AAAA (IPv6)', MX: 'MX (Mail)',
  NS: 'NS (Nameservers)', TXT: 'TXT', SOA: 'SOA',
  CNAME: 'CNAME', PTR: 'PTR (Reverse)',
};

export default function DnsView({ data }: DnsViewProps) {
  const entries = Object.entries(meta).filter(([key]) => {
    const vals = data[key as keyof DnsResult];
    return vals && vals.length > 0;
  });

  if (entries.length === 0) {
    return (
      <div className="card p-8 text-center">
        <p style={{ color: 'var(--color-charcoal)', fontFamily: 'var(--font-body)', fontSize: 14 }}>No DNS records found</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {entries.map(([key, label]) => {
        const values = data[key as keyof DnsResult] as string[];
        return (
          <div key={key} className="card border overflow-hidden" style={{ borderColor: 'var(--color-hairline)' }}>
            <div className="flex items-center gap-2 px-5 py-3 border-b" style={{ borderColor: 'var(--color-hairline)' }}>
              <span style={{ fontFamily: 'var(--font-body)', fontSize: 14, fontWeight: 500, color: 'var(--color-ink)' }}>{label}</span>
              <span className="ml-auto text-xs" style={{ color: 'var(--color-ash)', fontFamily: 'var(--font-mono)' }}>{values.length}</span>
            </div>
            <div className="record-list">
              {values.map((val, vi) => (
                <div key={vi} className="px-5 py-2.5 text-sm break-all" style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-body)' }}>
                  {val}
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
