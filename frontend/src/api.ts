import type { ScanType, FullScanResult, ScanResult } from './types';

const BASE_URL = import.meta.env.PROD ? '' : 'http://localhost:8000';
const API = `${BASE_URL}/api`;

export async function fetchScanTypes(): Promise<ScanType[]> {
  const res = await fetch(`${API}/scan-types`);
  const data = await res.json();
  return data.types;
}

export async function runScan(
  target: string,
  scanType: string
): Promise<ScanResult> {
  const res = await fetch(`${API}/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target, scan_type: scanType }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Scan failed' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function runFullScan(target: string): Promise<FullScanResult> {
  const res = await fetch(`${API}/full-scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Full scan failed' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}
