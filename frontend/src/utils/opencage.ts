export interface OpenCageResult {
  formatted: string;
  timezone: { name: string; offset_string: string };
  currency: { name: string; symbol: string };
  continent: string;
  country: string;
  components: Record<string, string>;
  confidence: number;
}

const OC_KEY = 'geointel_opencage_key';

export function getOpenCageKey(): string {
  return localStorage.getItem(OC_KEY) || '';
}

export function setOpenCageKey(key: string): void {
  if (key) localStorage.setItem(OC_KEY, key);
  else localStorage.removeItem(OC_KEY);
}

export function hasOpenCageKey(): boolean {
  return !!getOpenCageKey();
}

export async function reverseGeocode(
  lat: number,
  lon: number
): Promise<OpenCageResult | null> {
  const key = getOpenCageKey();
  if (!key) return null;

  const res = await fetch(
    `https://api.opencagedata.com/geocode/v1/json?q=${lat}+${lon}&key=${key}&language=en&limit=1`
  );
  if (!res.ok) return null;

  const data = await res.json();
  if (!data.results?.length) return null;

  const r = data.results[0];
  return {
    formatted: r.formatted,
    timezone: r.annotations?.timezone || { name: '', offset_string: '' },
    currency: r.annotations?.currency || { name: '', symbol: '' },
    continent: r.components?.continent || '',
    country: r.components?.country || '',
    components: r.components || {},
    confidence: r.confidence,
  };
}
