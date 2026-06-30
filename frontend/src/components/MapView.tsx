import { useEffect, useRef } from 'react';
import L from 'leaflet';

interface MapViewProps {
  lat: number;
  lon: number;
  label: string;
}

const TILE_URL = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const TILE_ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>';

function createIcon() {
  return L.divIcon({
    className: '',
    html: `<div style="width:32px;height:32px;background:#b7a1ff;border:2px solid #fcfdff;border-radius:8px;display:flex;align-items:center;justify-content:center;box-shadow:0 0 0 1px rgba(183,161,255,0.3)">
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
    </div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -36],
  });
}

export default function MapView({ lat, lon, label }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      center: [20, 0],
      zoom: 2,
      zoomControl: true,
      attributionControl: true,
    });

    L.tileLayer(TILE_URL, { attribution: TILE_ATTR, maxZoom: 18 }).addTo(map);

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (markerRef.current) {
      markerRef.current.remove();
      markerRef.current = null;
    }

    if (lat && lon) {
      const marker = L.marker([lat, lon], { icon: createIcon() })
        .addTo(map)
        .bindPopup(
          `<div style="font-family:Inter,sans-serif;line-height:1.6">
            <div style="font-size:13px;font-weight:500;color:#fcfdff">${label}</div>
            <div style="font-size:11px;color:#a1a4a5;font-family:JetBrains Mono,monospace">${lat.toFixed(4)}, ${lon.toFixed(4)}</div>
          </div>`,
          { closeButton: false }
        )
        .openPopup();

      markerRef.current = marker;

      map.flyTo([lat, lon], lat > 60 || lat < -60 ? 5 : 10, {
        duration: 1.2,
        easeLinearity: 0.25,
      });
    }
  }, [lat, lon, label]);

  return (
    <div style={{ width: '100%', height: 420, borderRadius: 'var(--radius-lg)', overflow: 'hidden', border: '1px solid var(--color-hairline-strong)' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
    </div>
  );
}
