# MSC Super Friend Web (Next.js)

## Run locally

```bash
npm install
npm run dev
```

App default URL: `http://localhost:3000`

## Environment variables

Copy `.env.example` to `.env.local` and set values:

- `NEXT_PUBLIC_API_BASE_URL`: FastAPI base URL (for Ask flow), e.g. `http://localhost:8000`
- `NEXT_PUBLIC_RATE_URL`: Optional external rating URL used by Settings > Rate app
- `NEXT_PUBLIC_APP_VERSION`: Optional version string shown in Settings/About
- `NEXT_PUBLIC_ENABLE_SW`: `true` to register `/sw.js` (disabled by default)

## PWA notes

- Manifest route is defined at `src/app/manifest.ts`
- Layout metadata includes manifest + app icons
- Expected icon files:
  - `public/icons/icon-192.png`
  - `public/icons/icon-512.png`
- Service worker registration is feature-flagged in `src/components/ServiceWorkerRegister.tsx`
- Current `public/sw.js` is a minimal placeholder. Replace with Serwist when offline caching requirements are finalized.

