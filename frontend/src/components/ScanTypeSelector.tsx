import type { ScanType } from '../types';
import { Activity, MapPin, Network, FileText, Shield, Globe, Search, Crosshair } from 'lucide-react';

const iconMap: Record<string, typeof MapPin> = {
  Activity, MapPin, Network, FileText, Shield, Globe, Search, Crosshair,
};

interface ScanTypeSelectorProps {
  types: ScanType[];
  selected: string;
  onSelect: (id: string) => void;
}

export default function ScanTypeSelector({ types, selected, onSelect }: ScanTypeSelectorProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
      {types.map((type) => {
        const Icon = iconMap[type.icon] || Crosshair;
        const isActive = selected === type.id;
        return (
          <button
            key={type.id}
            type="button"
            onClick={() => onSelect(type.id)}
            aria-pressed={isActive}
            className="flex items-start text-left gap-3 p-3.5 rounded-lg text-sm transition-all duration-150 cursor-pointer"
            style={{
              background: isActive ? 'rgba(183,161,255,.09)' : 'var(--color-surface-deep)',
              color: isActive ? 'var(--color-ink)' : 'var(--color-charcoal)',
              border: isActive ? '1px solid rgba(183,161,255,.45)' : '1px solid var(--color-hairline)',
              fontFamily: 'var(--font-body)',
            }}
          >
            <span className="grid place-items-center w-8 h-8 shrink-0 rounded-md" style={{ background: isActive ? 'var(--color-accent-orange)' : 'var(--color-surface-elevated)', color: isActive ? '#000' : 'var(--color-mute)' }}>
              <Icon className="w-4 h-4" />
            </span>
            <span className="min-w-0">
              <span className="block text-xs font-medium mb-1" style={{ color: 'var(--color-ink)' }}>{type.name}</span>
              <span className="block text-[11px] leading-relaxed" style={{ color: 'var(--color-ash)' }}>{type.description}</span>
            </span>
          </button>
        );
      })}
    </div>
  );
}
