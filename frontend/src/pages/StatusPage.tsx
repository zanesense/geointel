import { useEffect, useState } from 'react';
import { Activity, CheckCircle2, XCircle } from 'lucide-react';
import { fetchScanTypes } from '../api';
import { useReveal } from '../utils/reveal';

export default function StatusPage() {
  const [status, setStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const cardRef = useReveal<HTMLDivElement>();
  const [tools, setTools] = useState(0);

  useEffect(() => {
    fetchScanTypes()
      .then((types) => { setTools(types.length); setStatus('online'); })
      .catch(() => setStatus('offline'));
  }, []);

  const online = status === 'online';
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-14 sm:py-20 min-h-[70vh]">
      <div className="eyebrow">System status</div>
      <h1 className="page-title">GeoIntel service health.</h1>
      <p className="page-lead mb-10">This page checks the local API directly. It does not test third-party providers or target availability.</p>

      <div ref={cardRef} className="rounded-xl border overflow-hidden" style={{ borderColor: 'var(--color-hairline-strong)', background: 'var(--color-surface-card)' }}>
        <div className="p-5 sm:p-6 flex items-center justify-between gap-4 border-b" style={{ borderColor: 'var(--color-hairline)' }}>
          <div className="flex items-center gap-3">
            {status === 'checking' ? <Activity className="w-5 h-5 animate-pulse" style={{ color: 'var(--color-accent-yellow)' }} /> : online ? <CheckCircle2 className="w-5 h-5" style={{ color: 'var(--color-accent-green)' }} /> : <XCircle className="w-5 h-5" style={{ color: 'var(--color-accent-red)' }} />}
            <div><h2 className="text-sm font-medium">API</h2><p className="text-xs mt-1" style={{ color: 'var(--color-ash)' }}>GET /scan-types</p></div>
          </div>
          <span className="text-xs uppercase tracking-wider" style={{ color: online ? 'var(--color-accent-green)' : status === 'offline' ? 'var(--color-accent-red)' : 'var(--color-accent-yellow)', fontFamily: 'var(--font-mono)' }}>{status}</span>
        </div>
        <div className="grid sm:grid-cols-2 gap-px" style={{ background: 'var(--color-hairline)' }}>
          <div className="p-6" style={{ background: 'var(--color-surface-card)' }}><div className="text-3xl" style={{ fontFamily: 'var(--font-mono)' }}>{online ? tools : '—'}</div><div className="text-xs mt-2" style={{ color: 'var(--color-ash)' }}>Registered scan modes</div></div>
          <div className="p-6" style={{ background: 'var(--color-surface-card)' }}><div className="text-3xl" style={{ fontFamily: 'var(--font-mono)' }}>{online ? '200' : '—'}</div><div className="text-xs mt-2" style={{ color: 'var(--color-ash)' }}>Expected health response</div></div>
        </div>
      </div>

      <div className="notice mt-6">External DNS, RDAP, crt.sh, GeoIP, OpenCage, and target services can fail independently while the GeoIntel API remains online. Full scans report those failures per collector.</div>
    </div>
  );
}
