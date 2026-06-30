# GeoIntel Web App

React + TypeScript frontend for the GeoIntel OSINT platform.

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Dashboard | Search bar, scan type selector, results viewer with map |
| `/docs` | Docs | API reference, scan types, usage examples |
| `/status` | Status | Service uptime and API health |
| `/terms` | Terms | Usage policy and legal disclaimer |

## Stack

- React 19 + TypeScript 6
- Vite 8 + SWC
- Tailwind CSS 4
- GSAP (scroll animations)
- Leaflet (geo map)
- Lucide React (icons)

## Development

```bash
npm run dev
```

The dev server proxies API calls to `http://localhost:8000`.

## Build

```bash
npm run build   # type-check + production build
npm run preview # preview production build
npm run lint    # ESLint
```

## API

All scan requests hit the backend at `/api/*`. See [Docs](/docs) for endpoint reference.
