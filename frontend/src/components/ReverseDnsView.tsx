import type { ReverseDnsResult } from '../types';

interface ReverseDnsViewProps {
  data: ReverseDnsResult;
}

export default function ReverseDnsView({ data }: ReverseDnsViewProps) {
  return (
    <div className="space-y-4">
      <div className="card border p-5" style={{ borderColor: 'var(--color-hairline)' }}>
        <div className="text-xs mb-2" style={{ color: 'var(--color-charcoal)', fontFamily: 'var(--font-body)' }}>Hostname</div>
        <div className="text-sm" style={{ color: 'var(--color-ink)', fontFamily: 'var(--font-mono)' }}>{data.hostname || '—'}</div>
      </div>

      {data.aliases && data.aliases.length > 0 && (
        <div className="card border overflow-hidden" style={{ borderColor: 'var(--color-hairline)' }}>
          <div className="px-5 py-3 border-b" style={{ borderColor: 'var(--color-hairline)' }}>
            <span style={{ fontFamily: 'var(--font-body)', fontSize: 14, fontWeight: 500, color: 'var(--color-ink)' }}>Aliases</span>
          </div>
          <div className="record-list">
            {data.aliases.map((alias, i) => (
              <div key={i} className="px-5 py-2.5 text-sm" style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-body)' }}>{alias}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
