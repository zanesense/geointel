import { useState, useRef, useEffect } from 'react';
import { Settings, X, KeyRound } from 'lucide-react';
import { getOpenCageKey, setOpenCageKey, hasOpenCageKey } from '../utils/opencage';

export default function SettingsPopover() {
  const [open, setOpen] = useState(false);
  const [key, setKey] = useState(getOpenCageKey());
  const [saved, setSaved] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    if (open) document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  const handleSave = () => {
    setOpenCageKey(key.trim());
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleClear = () => {
    setKey('');
    setOpenCageKey('');
    setSaved(false);
  };

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center justify-center w-7 h-7 rounded-md transition-colors duration-150 cursor-pointer"
        style={{ color: hasOpenCageKey() ? 'var(--color-accent-orange)' : 'var(--color-stone)' }}
        title="Settings"
      >
        <Settings className="w-4 h-4" />
      </button>

      {open && (
        <div
          className="absolute right-0 top-full mt-2 w-80 p-5 border rounded-xl z-50"
          style={{
            background: 'var(--color-surface-elevated)',
            borderColor: 'var(--color-hairline-strong)',
            borderRadius: 'var(--radius-lg)',
          }}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <KeyRound className="w-4 h-4" style={{ color: 'var(--color-accent-orange)' }} />
              <span className="text-sm font-medium" style={{ color: 'var(--color-ink)', fontFamily: 'var(--font-body)' }}>
                OpenCage API Key
              </span>
            </div>
            <button onClick={() => setOpen(false)} className="cursor-pointer" style={{ color: 'var(--color-stone)' }}>
              <X className="w-4 h-4" />
            </button>
          </div>

          <p className="text-xs mb-3 leading-relaxed" style={{ color: 'var(--color-body)', fontFamily: 'var(--font-body)' }}>
            Add your free OpenCage API key to unlock timezone, currency, formatted addresses, and confidence scores.
            <br />
            <a
              href="https://opencagedata.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="underline"
              style={{ color: 'var(--color-accent-orange)' }}
            >
              Get a free key &rarr;
            </a>
          </p>

          <input
            type="text"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="Enter your API key..."
            className="w-full px-3 py-2 text-sm rounded-lg outline-none border mb-3"
            style={{
              background: 'var(--color-surface-card)',
              borderColor: 'var(--color-hairline-strong)',
              color: 'var(--color-ink)',
              fontFamily: 'var(--font-mono)',
              borderRadius: 'var(--radius-md)',
            }}
          />

          <div className="flex items-center gap-2">
            <button
              onClick={handleSave}
              className="flex-1 px-3 py-1.5 text-sm font-medium rounded-lg transition-colors duration-150 cursor-pointer"
              style={{
                background: 'var(--color-primary)',
                color: 'var(--color-primary-on)',
                borderRadius: 'var(--radius-md)',
                fontFamily: 'var(--font-body)',
              }}
            >
              {saved ? 'Saved' : 'Save'}
            </button>
            {hasOpenCageKey() && (
              <button
                onClick={handleClear}
                className="px-3 py-1.5 text-sm rounded-lg transition-colors duration-150 cursor-pointer"
                style={{
                  background: 'var(--color-surface-card)',
                  border: '1px solid var(--color-hairline-strong)',
                  color: 'var(--color-charcoal)',
                  borderRadius: 'var(--radius-md)',
                  fontFamily: 'var(--font-body)',
                }}
              >
                Clear
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
