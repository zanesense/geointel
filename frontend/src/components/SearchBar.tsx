import { useState, type FormEvent } from 'react';
import { ArrowRight, Loader2, Search, X } from 'lucide-react';

interface SearchBarProps {
  onSearch: (target: string) => void;
  loading: boolean;
}

const quickTargets = [
  ['Google DNS', '8.8.8.8'],
  ['Cloudflare', '1.1.1.1'],
  ['Example domain', 'example.com'],
] as const;

export default function SearchBar({ onSearch, loading }: SearchBarProps) {
  const [value, setValue] = useState('');
  const targetType = value ? (value.includes('://') ? 'URL' : 'IP / domain') : 'Target';

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (trimmed && !loading) onSearch(trimmed);
  };

  return (
    <div className="w-full max-w-3xl">
      <form onSubmit={handleSubmit} aria-label="Investigate a target">
        <div className="search-shell overflow-hidden flex items-center p-1.5" style={{ minHeight: 66 }}>
          <div className="pl-5 pr-3 select-none" style={{ color: 'var(--color-mute)' }}>
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" style={{ color: 'var(--color-accent-orange)' }} />
            ) : (
              <Search className="w-5 h-5" />
            )}
          </div>
          <input
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="IP address, domain, or URL"
            aria-label="Target IP address, domain, or URL"
            className="flex-1 min-w-0 bg-transparent py-4 pr-2 outline-none"
            style={{ color: 'var(--color-ink)', fontFamily: 'var(--font-mono)', fontSize: 14 }}
            disabled={loading}
            autoComplete="off"
            autoCapitalize="none"
            spellCheck={false}
            autoFocus
          />
          <div className="flex items-center gap-1.5">
            <span className="hidden md:inline-flex px-2 py-1 rounded text-[10px] uppercase tracking-wider border" style={{ color: 'var(--color-ash)', borderColor: 'var(--color-hairline)', fontFamily: 'var(--font-mono)' }}>
              {targetType}
            </span>
            {value && !loading && (
              <button
                type="button"
                onClick={() => setValue('')}
                aria-label="Clear target"
                className="grid place-items-center w-8 h-8 rounded-md transition-colors duration-150 cursor-pointer"
                style={{ color: 'var(--color-mute)', fontFamily: 'var(--font-body)' }}
              >
                <X className="w-4 h-4" />
              </button>
            )}
            <button
              type="submit"
              disabled={loading || !value.trim()}
              className="h-11 px-3 sm:px-5 flex items-center gap-2 text-sm font-medium transition-all duration-150 cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
              style={{
                background: loading || !value.trim() ? 'var(--color-surface-card)' : 'var(--color-primary)',
                color: loading || !value.trim() ? 'var(--color-stone)' : 'var(--color-primary-on)',
                borderRadius: 'var(--radius-md)',
                fontFamily: 'var(--font-body)',
              }}
            >
              <span className="hidden sm:inline">{loading ? 'Scanning…' : 'Investigate'}</span>
              {!loading && <ArrowRight className="w-4 h-4" />}
              {loading && <Loader2 className="w-4 h-4 animate-spin sm:hidden" />}
            </button>
          </div>
        </div>
      </form>

      <div className="flex items-center justify-between gap-3 mt-3 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[11px] uppercase tracking-wider" style={{ color: 'var(--color-ash)', fontFamily: 'var(--font-mono)' }}>Try</span>
        {quickTargets.map(([name, target]) => (
          <button
            key={target}
            type="button"
            onClick={() => { setValue(target); onSearch(target); }}
            disabled={loading}
            className="px-3 py-1 rounded-full border text-xs transition-all duration-150 cursor-pointer disabled:opacity-30"
            style={{
              background: 'var(--color-surface-card)',
              borderColor: 'var(--color-hairline)',
              color: 'var(--color-charcoal)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {name}
          </button>
        ))}
        </div>
        <span className="hidden sm:inline text-[11px]" style={{ color: 'var(--color-stone)', fontFamily: 'var(--font-mono)' }}>Press Enter to run</span>
      </div>
    </div>
  );
}
