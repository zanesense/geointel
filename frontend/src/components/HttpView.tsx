import type { HttpResult } from '../types';

interface HttpViewProps {
  data: HttpResult;
}

const sevColor = (v: string) => v === 'Not set' || !v ? 'var(--color-accent-red)' : v === 'Set' ? 'var(--color-accent-green)' : 'var(--color-accent-yellow)';

export default function HttpView({ data }: HttpViewProps) {
  return (
    <div className="space-y-4">
      <div className="hairline-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
        {[
          { label: 'Status Code', value: String(data.status_code), c: data.status_code < 300 ? 'var(--color-accent-green)' : data.status_code < 400 ? 'var(--color-accent-yellow)' : 'var(--color-accent-red)' },
          { label: 'Server', value: data.server, c: 'var(--color-ink)' },
          { label: 'Content-Type', value: data.content_type, c: 'var(--color-ink)' },
        ].map((s) => (
          <div key={s.label} className="p-5">
            <div className="text-xs mb-1.5" style={{ color: 'var(--color-charcoal)', fontFamily: 'var(--font-body)' }}>{s.label}</div>
            <div className="text-sm font-medium truncate" style={{ color: s.c, fontFamily: 'var(--font-mono)' }}>{s.value || '—'}</div>
          </div>
        ))}
      </div>

      <div className="card border overflow-hidden" style={{ borderColor: 'var(--color-hairline)' }}>
        <div className="px-5 py-3 border-b" style={{ borderColor: 'var(--color-hairline)' }}>
          <span style={{ fontFamily: 'var(--font-body)', fontSize: 14, fontWeight: 500, color: 'var(--color-ink)' }}>Security Headers</span>
        </div>
        <div className="record-list">
          {Object.entries(data.security).map(([header, value]) => (
            <div key={header} className="px-5 py-3 flex items-center justify-between" style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>
              <span style={{ color: 'var(--color-ink)' }}>{header}</span>
              <span style={{ color: sevColor(value) }}>{value || 'Not set'}</span>
            </div>
          ))}
        </div>
      </div>

      <details className="card border overflow-hidden" style={{ borderColor: 'var(--color-hairline)' }}>
        <summary className="px-5 py-3 cursor-pointer select-none text-sm" style={{ fontFamily: 'var(--font-body)', fontWeight: 500, color: 'var(--color-ink)' }}>
          All Response Headers · {Object.keys(data.all_headers).length}
        </summary>
        <div className="border-t max-h-72 overflow-y-auto" style={{ borderColor: 'var(--color-hairline)' }}>
          {Object.entries(data.all_headers).map(([k, v]) => (
            <div key={k} className="px-5 py-2 border-b text-xs" style={{ borderColor: 'var(--color-hairline)', fontFamily: 'var(--font-mono)' }}>
              <span style={{ color: 'var(--color-accent-orange)' }}>{k}</span>
              <span style={{ color: 'var(--color-mute)' }}>: </span>
              <span style={{ color: 'var(--color-body)' }}>{v}</span>
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}
