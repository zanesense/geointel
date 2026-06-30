import { MapPin } from 'lucide-react';
import { useReveal } from '../utils/reveal';

const groups = [
  { title: 'Product', links: [['Workspace', '/'], ['System status', '/status']] },
  { title: 'Resources', links: [['Documentation', '/docs'], ['API reference', '/api/docs']] },
  { title: 'Legal', links: [['Terms & acceptable use', '/terms'], ['Privacy', '/terms#privacy']] },
];

export default function Footer() {
  const footerRef = useReveal<HTMLElement>();

  return (
    <footer ref={footerRef} className="border-t" style={{ borderColor: 'var(--color-hairline)', background: 'var(--color-surface-deep)' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
        <div className="grid gap-10 md:grid-cols-[1.5fr_2fr]">
          <div>
            <a href="/" className="inline-flex items-center gap-2 mb-4">
              <span className="grid place-items-center w-8 h-8 rounded-lg border" style={{ color: 'var(--color-accent-orange)', borderColor: 'rgba(183,161,255,.25)', background: 'rgba(183,161,255,.08)' }}>
                <MapPin className="w-4 h-4" />
              </span>
              <span className="text-sm font-semibold tracking-tight" style={{ fontFamily: 'var(--font-mono)' }}>GEOINTEL</span>
            </a>
            <p className="max-w-sm text-sm leading-relaxed" style={{ color: 'var(--color-ash)' }}>
              A local IP and domain intelligence workspace for infrastructure research and authorized network checks.
            </p>
          </div>
          <nav aria-label="Footer" className="grid grid-cols-2 sm:grid-cols-3 gap-8">
            {groups.map((group) => (
              <div key={group.title}>
                <h2 className="text-xs font-medium mb-4" style={{ color: 'var(--color-ink)' }}>{group.title}</h2>
                <ul className="space-y-3">
                  {group.links.map(([name, href]) => (
                    <li key={href}><a href={href} className="text-xs hover:text-white transition-colors" style={{ color: 'var(--color-ash)' }}>{name}</a></li>
                  ))}
                </ul>
              </div>
            ))}
          </nav>
        </div>
        <div className="mt-10 pt-6 border-t flex flex-col sm:flex-row gap-3 justify-between text-xs" style={{ borderColor: 'var(--color-hairline)', color: 'var(--color-ash)', fontFamily: 'var(--font-mono)' }}>
          <span>GeoIntel · Use only on systems you are authorized to test.</span>
          <a href="https://github.com/zanesense" target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 hover:text-white transition-colors">
            Built by @zanesense on GitHub
          </a>
        </div>
      </div>
    </footer>
  );
}
