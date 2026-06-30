export function exportAsJson(data: Record<string, unknown>, filename = 'geointel-scan.json') {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  downloadBlob(blob, filename);
}

export function exportAsCsv(data: Record<string, unknown>, filename = 'geointel-scan.csv') {
  const flat = flattenObject(data);
  const headers = Object.keys(flat);
  const values = headers.map((h) => {
    const v = flat[h];
    const str = v == null ? '' : String(v);
    return `"${str.replace(/"/g, '""')}"`;
  });
  const csv = [headers.join(','), values.join(',')].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  downloadBlob(blob, filename);
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function flattenObject(
  obj: Record<string, unknown>,
  prefix = '',
  result: Record<string, unknown> = {}
): Record<string, unknown> {
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      flattenObject(value as Record<string, unknown>, fullKey, result);
    } else if (Array.isArray(value)) {
      result[fullKey] = value.join('; ');
    } else {
      result[fullKey] = value;
    }
  }
  return result;
}
