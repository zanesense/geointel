import type { WhoisResult } from '../types';

interface WhoisViewProps {
  data: WhoisResult;
}

const fields: { key: keyof WhoisResult; label: string }[] = [
  { key: 'domain_name', label: 'Domain Name' },
  { key: 'registrar', label: 'Registrar' },
  { key: 'whois_server', label: 'WHOIS Server' },
  { key: 'creation_date', label: 'Created' },
  { key: 'expiration_date', label: 'Expires' },
  { key: 'updated_date', label: 'Updated' },
  { key: 'org', label: 'Organization' },
  { key: 'country', label: 'Country' },
  { key: 'city', label: 'City' },
];

export default function WhoisView({ data }: WhoisViewProps) {
  return (
    <div className="space-y-4">
      <div className="hairline-grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))' }}>
        {fields.map(({ key, label }) => {
          const val = data[key];
          if (!val) return null;
          const display = Array.isArray(val) ? val.join(', ') : String(val);
          return (
            <div key={key} className="p-5">
              <div className="text-xs mb-1.5" style={{ color: 'var(--color-charcoal)', fontFamily: 'var(--font-body)' }}>{label}</div>
              <div className="text-sm break-all" style={{ color: 'var(--color-ink)', fontFamily: 'var(--font-mono)' }}>{display}</div>
            </div>
          );
        })}
      </div>

      {data.name_servers && data.name_servers.length > 0 && (
        <div className="card border overflow-hidden" style={{ borderColor: 'var(--color-hairline)' }}>
          <div className="px-5 py-3 border-b" style={{ borderColor: 'var(--color-hairline)' }}>
            <span style={{ fontFamily: 'var(--font-body)', fontSize: 14, fontWeight: 500, color: 'var(--color-ink)' }}>Name Servers</span>
          </div>
          <div className="record-list">
            {data.name_servers.map((ns, i) => (
              <div key={i} className="px-5 py-2.5 text-sm" style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-body)' }}>{ns}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
