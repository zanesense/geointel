import SettingsPopover from './SettingsPopover';
import { Activity } from 'lucide-react';

export default function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-hairline backdrop-blur-xl" style={{ height: 68, background: 'rgba(0,0,0,.82)' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-full flex items-center justify-between">
        <a href="/" aria-label="GeoIntel home" className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center border" style={{ background: 'rgba(183,161,255,0.1)', borderColor: 'rgba(183,161,255,.25)' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#b7a1ff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
              <circle cx="12" cy="10" r="3"/>
            </svg>
          </div>
          <span className="text-sm font-semibold tracking-tight" style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-ink)' }}>GEOINTEL</span>
          <span className="hidden sm:inline text-xs border-l border-hairline pl-3" style={{ color: 'var(--color-ash)', fontFamily: 'var(--font-mono)' }}>
            OSINT CONSOLE
          </span>
        </a>
        <div className="flex items-center gap-3">
          <nav aria-label="Primary" className="hidden lg:flex items-center gap-4 mr-1 text-xs" style={{ color: 'var(--color-charcoal)' }}>
            <a href="/docs">Docs</a>
            <a href="/status">Status</a>
            <a href="/terms">Terms</a>
          </nav>
          <a href="/#workspace" className="hidden md:flex items-center gap-1.5 text-xs" style={{ color: 'var(--color-charcoal)', fontFamily: 'var(--font-body)' }}>
            <Activity className="w-3.5 h-3.5" /> Workspace
          </a>
          <SettingsPopover />
          <span className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-full border" style={{ color: 'var(--color-charcoal)', borderColor: 'var(--color-hairline)', fontFamily: 'var(--font-mono)' }}>
            <span className="w-2 h-2 rounded-full" style={{ background: '#11ff99' }} />
            ONLINE
          </span>
        </div>
      </div>
    </header>
  );
}
