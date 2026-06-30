import type { SslResult } from '../types';

interface SslViewProps {
  data: SslResult;
}

function parseDate(s: string): string {
  if (!s) return '—';
  try { return new Date(s).toLocaleString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }); }
  catch { return s; }
}

const fields: { key: keyof SslResult; label: string; fmt?: (v: string) => string }[] = [
  { key: 'subject', label: 'Subject (CN)' },
  { key: 'issuer', label: 'Issuer' },
  { key: 'serial', label: 'Serial Number' },
  { key: 'version', label: 'Version' },
  { key: 'not_before', label: 'Valid From', fmt: parseDate },
  { key: 'not_after', label: 'Valid Until', fmt: parseDate },
];

export default function SslView({ data }: SslViewProps) {
  return (
    <div className="space-y-4">
      <div className="hairline-grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))' }}>
        {fields.map(({ key, label, fmt }) => {
          const val = data[key];
          if (!val) return null;
          const display = fmt ? fmt(String(val)) : String(val);
          return (
            <div key={key} className="p-5">
              <div className="text-xs mb-1.5" style={{ color: 'var(--color-charcoal)', fontFamily: 'var(--font-body)' }}>{label}</div>
              <div className="text-sm break-all" style={{ color: 'var(--color-ink)', fontFamily: 'var(--font-mono)' }}>{display}</div>
            </div>
          );
        })}
      </div>

      {data.sans && data.sans.length > 0 && (
        <div className="card border overflow-hidden" style={{ borderColor: 'var(--color-hairline)' }}>
          <div className="flex items-center gap-2 px-5 py-3 border-b" style={{ borderColor: 'var(--color-hairline)' }}>
            <span style={{ fontFamily: 'var(--font-body)', fontSize: 14, fontWeight: 500, color: 'var(--color-ink)' }}>Subject Alternative Names (SANs)</span>
            <span className="ml-auto text-xs" style={{ color: 'var(--color-ash)', fontFamily: 'var(--font-mono)' }}>{data.sans.length}</span>
          </div>
          <div className="record-list">
            {data.sans.map((san, i) => (
              <div key={i} className="px-5 py-2.5 text-sm" style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-body)' }}>{san}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
