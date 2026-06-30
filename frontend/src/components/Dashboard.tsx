import { useEffect, useState, useRef } from 'react';
import { Crosshair, Activity, Download, MapPin, AlertCircle, Loader2 } from 'lucide-react';
import SearchBar from './SearchBar';
import FullScanView from './FullScanView';
import ScanTypeSelector from './ScanTypeSelector';
import MapView from './MapView';
import { fetchScanTypes, runScan } from '../api';
import { exportAsJson, exportAsCsv } from '../utils/export';
import { reverseGeocode, hasOpenCageKey } from '../utils/opencage';
import type { GeoIntelResult, FullScanResult, ScanResult, ScanType } from '../types';
import type { OpenCageResult } from '../utils/opencage';

export default function Dashboard() {
  const [result, setResult] = useState<GeoIntelResult | null>(null);
  const [scanTypes, setScanTypes] = useState<ScanType[]>([]);
  const [selectedType, setSelectedType] = useState('');
  const [intelResult, setIntelResult] = useState<ScanResult | null>(null);
  const [intelLoading, setIntelLoading] = useState(false);
  const [intelError, setIntelError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<string[]>([]);
  const [target, setTarget] = useState('');
  const [ocResult, setOcResult] = useState<OpenCageResult | null>(null);
  const [ocLoading, setOcLoading] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchScanTypes()
      .then((types) => setScanTypes(types.filter(({ id }) => id !== 'quick' && id !== 'full')))
      .catch(() => setIntelError('Could not load intelligence tools'));
  }, []);

  const search = async (t: string) => {
    setTarget(t);
    setLoading(true);
    setError(null);
    setResult(null);
    setSelectedType('');
    setIntelResult(null);
    setIntelError(null);
    setOcResult(null);
    try {
      const data = await runScan(t, 'quick') as GeoIntelResult;
      setResult(data);
      setHistory((p) => [t, ...p.filter((x) => x !== t)].slice(0, 5));
      requestAnimationFrame(() => resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }));

      if (hasOpenCageKey()) {
        setOcLoading(true);
        reverseGeocode(data.lat, data.lon).then((oc) => {
          setOcResult(oc);
          setOcLoading(false);
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Lookup failed');
    } finally {
      setLoading(false);
    }
  };

  const runIntelScan = async (scanType: string) => {
    setSelectedType(scanType);
    setIntelResult(null);
    setIntelError(null);
    setIntelLoading(true);
    try {
      setIntelResult(await runScan(target, scanType));
    } catch (err) {
      setIntelError(err instanceof Error ? err.message : 'Scan failed');
    } finally {
      setIntelLoading(false);
    }
  };

  const selectedScan = intelResult ? ({
    target,
    resolved_ip: result?.ip || '',
    results: { [selectedType]: intelResult },
    errors: null,
  } as unknown as FullScanResult) : null;

  return (
    <div className="min-h-screen" style={{ background: 'var(--color-canvas)' }}>
      {/* Hero */}
      <section className="hero-grid px-4 sm:px-6 pb-16 border-b" style={{ borderColor: 'var(--color-hairline)' }}>
        <div className="max-w-7xl mx-auto pt-20 sm:pt-28 pb-10">
          <div
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full border text-[11px] uppercase tracking-[.14em] mb-7"
            style={{ background: 'var(--color-surface-card)', borderColor: 'var(--color-hairline)', color: 'var(--color-charcoal)', fontFamily: 'var(--font-body)' }}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#b7a1ff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
              <circle cx="12" cy="10" r="3"/>
            </svg>
            Network intelligence workspace
          </div>
          <div className="grid lg:grid-cols-[1fr_340px] gap-10 lg:gap-20 items-end">
            <div>
              <h1 className="text-5xl sm:text-6xl md:text-7xl leading-[.98] tracking-[-.04em] mb-6 max-w-4xl" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-ink)' }}>
                Investigate the internet<br /><em>from one console.</em>
              </h1>
              <p className="text-base sm:text-lg max-w-2xl leading-relaxed mb-8" style={{ color: 'var(--color-charcoal)', fontFamily: 'var(--font-body)' }}>
                Resolve infrastructure, inspect registration and DNS, evaluate web posture, and check exposed services without switching tools.
              </p>
              <SearchBar onSearch={search} loading={loading} />
            </div>
            <div className="hidden lg:grid grid-cols-2 gap-px rounded-xl overflow-hidden border" style={{ background: 'var(--color-hairline)', borderColor: 'var(--color-hairline)' }}>
              {[['15', 'scan modes'], ['1K+', 'TCP ports'], ['3', 'public files'], ['1', 'target workflow']].map(([value, metric]) => (
                <div key={metric} className="p-5" style={{ background: 'rgba(10,10,12,.8)' }}>
                  <div className="text-2xl mb-1" style={{ color: 'var(--color-ink)', fontFamily: 'var(--font-mono)' }}>{value}</div>
                  <div className="text-[11px] uppercase tracking-wider" style={{ color: 'var(--color-ash)', fontFamily: 'var(--font-mono)' }}>{metric}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Results */}
      <section id="workspace" ref={resultsRef} className="px-4 sm:px-6 py-12 sm:py-16 max-w-7xl mx-auto scroll-mt-20">
        {loading && (
          <div className="flex flex-col items-center justify-center py-32">
            <div className="relative w-12 h-12 mb-4">
              <div className="absolute inset-0 rounded-full border" style={{ borderColor: 'var(--color-hairline)' }} />
              <div className="absolute inset-0 rounded-full border-2 border-transparent" style={{ borderTopColor: 'var(--color-accent-orange)' }} />
              <Loader2 className="absolute inset-0 m-auto w-5 h-5 animate-pulse" style={{ color: 'var(--color-accent-orange)' }} />
            </div>
            <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--color-charcoal)', fontFamily: 'var(--font-body)' }}>
              <Activity className="w-4 h-4 animate-pulse" style={{ color: 'var(--color-accent-orange)' }} />
              Resolving location&hellip;
            </div>
          </div>
        )}

        {error && !loading && (
          <div className="max-w-lg mx-auto card p-5 flex items-start gap-3" style={{ border: '1px solid rgba(255,32,71,0.3)' }}>
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" style={{ color: 'var(--color-accent-red)' }} />
            <div>
              <p className="text-sm font-medium mb-0.5" style={{ color: 'var(--color-ink)', fontFamily: 'var(--font-body)' }}>Lookup failed</p>
              <p className="text-sm" style={{ color: 'var(--color-body)', fontFamily: 'var(--font-body)' }}>{error}</p>
            </div>
          </div>
        )}

        {result && !loading && !error && (
          <div className="space-y-6">
            {/* Toolbar */}
            <div className="card-elevated border flex items-center justify-between flex-wrap gap-3 px-5 py-3" style={{ borderColor: 'var(--color-hairline)' }}>
              <div className="flex items-center gap-3">
                <MapPin className="w-4 h-4" style={{ color: 'var(--color-accent-orange)' }} />
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--color-ink)', fontFamily: 'var(--font-body)' }}>Geolocation</p>
                  <p className="text-xs" style={{ color: 'var(--color-charcoal)', fontFamily: 'var(--font-mono)' }}>{target}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {[
                  { label: 'JSON', ext: 'json' },
                  { label: 'CSV', ext: 'csv' },
                ].map(({ label, ext }) => (
                  <button
                    key={ext}
                    onClick={() => {
                      const fn = `geoip-${target}.${ext}`;
                      if (ext === 'json') exportAsJson(result as unknown as Record<string, unknown>, fn);
                      else exportAsCsv(result as unknown as Record<string, unknown>, fn);
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs transition-colors duration-150 cursor-pointer"
                    style={{
                      background: 'var(--color-surface-card)',
                      border: '1px solid var(--color-hairline-strong)',
                      color: 'var(--color-charcoal)',
                      fontFamily: 'var(--font-body)',
                    }}
                  >
                    <Download className="w-3 h-3" />
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Map + Data side by side */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
              <div className="lg:col-span-2">
                <div className="hairline-grid rounded-xl overflow-hidden" style={{ borderRadius: 'var(--radius-lg)' }}>
                  {[
                    ['IP Address', result.ip],
                    ['Continent', result.continent],
                    ['Country', result.country],
                    ['Region', result.region],
                    ['City', result.city],
                    ['Coordinates', `${result.lat}, ${result.lon}`],
                    ['ISP', result.isp],
                    ['Organization', result.org],
                    ['ASN', result.asn],
                    ...(ocLoading
                      ? [['Timezone', 'Loading\u2026']]
                      : ocResult
                      ? [
                          ['Timezone', ocResult.timezone?.name || ''],
                          ['UTC Offset', ocResult.timezone?.offset_string || ''],
                          ['Currency', ocResult.currency ? `${ocResult.currency.name} (${ocResult.currency.symbol})` : ''],
                          ['Formatted Address', ocResult.formatted || ''],
                          ['Confidence', `${ocResult.confidence}/10`],
                        ]
                      : []),
                  ].map(([label, value], i) => (
                    <div key={i} className="px-5 py-3 flex items-center justify-between" style={{ background: 'var(--color-surface-card)' }}>
                      <span className="text-xs" style={{ color: 'var(--color-charcoal)', fontFamily: 'var(--font-body)' }}>{label}</span>
                      <span className="text-xs font-medium" style={{ color: 'var(--color-ink)', fontFamily: 'var(--font-mono)' }}>{value}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="lg:col-span-3 lg:sticky lg:top-24">
                <MapView lat={result.lat} lon={result.lon} label={`${result.city || ''}, ${result.country || ''}`} />
              </div>
            </div>

            {/* Intelligence tools */}
            <div className="border rounded-xl overflow-hidden" style={{ borderColor: 'var(--color-hairline-strong)', borderRadius: 'var(--radius-lg)' }}>
              <div className="px-4 sm:px-5 py-5" style={{ background: 'var(--color-surface-card)' }}>
                <div className="flex items-center justify-between gap-3 mb-5">
                  <div>
                    <div className="flex items-center gap-2 text-sm font-medium" style={{ color: 'var(--color-ink)', fontFamily: 'var(--font-body)' }}>
                      <Activity className="w-4 h-4" style={{ color: 'var(--color-accent-orange)' }} /> Intelligence modules
                    </div>
                    <p className="text-xs mt-1.5 ml-6" style={{ color: 'var(--color-ash)' }}>Choose one module. Only the selected operation runs.</p>
                  </div>
                  <span className="text-[10px] uppercase tracking-wider px-2 py-1 rounded border" style={{ color: 'var(--color-ash)', borderColor: 'var(--color-hairline)', fontFamily: 'var(--font-mono)' }}>{scanTypes.length} available</span>
                </div>
                <ScanTypeSelector types={scanTypes} selected={selectedType} onSelect={runIntelScan} />
              </div>
              <div className="border-t" style={{ borderColor: 'var(--color-hairline)', background: 'var(--color-canvas)' }}>
                {intelLoading && (
                  <div className="flex items-center gap-2 px-5 py-8 justify-center text-sm" style={{ color: 'var(--color-charcoal)', fontFamily: 'var(--font-body)' }}>
                    <Loader2 className="w-4 h-4 animate-spin" style={{ color: 'var(--color-accent-orange)' }} />
                    Running {scanTypes.find(({ id }) => id === selectedType)?.name || 'scan'}&hellip;
                  </div>
                )}
                {intelError && !intelLoading && (
                  <div className="px-5 py-6 text-sm" style={{ color: 'var(--color-accent-red)', fontFamily: 'var(--font-body)' }}>{intelError}</div>
                )}
                {selectedScan && !intelLoading && (
                  <div className="p-5"><FullScanView data={selectedScan} /></div>
                )}
                {!selectedScan && !intelLoading && !intelError && (
                  <div className="px-5 py-8 text-center text-sm" style={{ color: 'var(--color-ash)', fontFamily: 'var(--font-body)' }}>
                    Select one tool above. Only that scan will run.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {!result && !loading && !error && (
          <div className="flex flex-col items-center justify-center py-32">
            <div className="w-12 h-12 rounded-full border flex items-center justify-center mb-4" style={{ borderColor: 'var(--color-hairline)' }}>
              <Crosshair className="w-5 h-5" style={{ color: 'var(--color-stone)' }} />
            </div>
            <p className="text-sm mb-1" style={{ color: 'var(--color-charcoal)', fontFamily: 'var(--font-body)' }}>Awaiting target</p>
            <p className="text-xs" style={{ color: 'var(--color-ash)', fontFamily: 'var(--font-body)' }}>Enter an IP address or domain name to begin</p>
          </div>
        )}
      </section>

      {history.length > 0 && (
        <section className="px-4 pb-24 max-w-7xl mx-auto">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-3.5 h-3.5" style={{ color: 'var(--color-ash)' }} />
            <span className="text-xs" style={{ color: 'var(--color-ash)', fontFamily: 'var(--font-body)' }}>Recent lookups</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {history.map((t, i) => (
              <button
                key={`${t}-${i}`}
                type="button"
                onClick={() => search(t)}
                className="px-4 py-1.5 rounded-full border text-xs transition-all duration-150 cursor-pointer"
                style={{
                  background: 'var(--color-surface-card)',
                  borderColor: 'var(--color-hairline)',
                  color: 'var(--color-charcoal)',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {t}
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
