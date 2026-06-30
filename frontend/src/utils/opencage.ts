export interface OpenCageResult {
  formatted: string;
  timezone: { name: string; offset_string: string };
  currency: { name: string; symbol: string };
  continent: string;
  country: string;
  components: Record<string, string>;
  confidence: number;
}

const API = window.location.origin;

let _key = '';

export function getOpenCageKey(): string {
  return _key;
}

export function setOpenCageKey(key: string): void {
  _key = key;
}

export function hasOpenCageKey(): boolean {
  return !!_key;
}

export async function reverseGeocode(
  lat: number,
  lon: number
): Promise<OpenCageResult | null> {
  const key = getOpenCageKey();
  if (!key) return null;

  try {
    const res = await fetch(`${API}/api/geocode`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lat, lon, api_key: key }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    if (data.error || !data.formatted) return null;
    return data as OpenCageResult;
  } catch {
    return null;
  }
}
