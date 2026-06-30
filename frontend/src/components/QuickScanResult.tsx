import type { GeoIntelResult } from '../types';

interface QuickScanResultProps {
  result: GeoIntelResult;
}

const fields: { label: string; key: keyof GeoIntelResult; fmt?: (r: GeoIntelResult) => string }[] = [
  { label: 'IP Address', key: 'ip' },
  { label: 'Continent', key: 'continent' },
  { label: 'Country', key: 'country' },
  { label: 'Region', key: 'region' },
  { label: 'City', key: 'city' },
  { label: 'Coordinates', key: 'lat', fmt: (r) => `${r.lat.toFixed(4)}, ${r.lon.toFixed(4)}` },
  { label: 'ISP', key: 'isp' },
  { label: 'Organization', key: 'org' },
  { label: 'ASN', key: 'asn' },
];

export default function QuickScanResult({ result }: QuickScanResultProps) {
  return (
    <div className="hairline-grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))' }}>
      {fields.map((field) => {
        const value = field.fmt ? field.fmt(result) : String(result[field.key] ?? '—');
        return (
          <div key={field.key} className="p-5">
            <div className="text-xs mb-1.5" style={{ color: 'var(--color-charcoal)', fontFamily: 'var(--font-body)' }}>
              {field.label}
            </div>
            <div className="text-sm font-medium truncate" style={{ color: 'var(--color-ink)', fontFamily: 'var(--font-mono)' }}>
              {value}
            </div>
          </div>
        );
      })}
    </div>
  );
}
