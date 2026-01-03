# Execution Plan: Monitoring Dashboard

Root: `C:/Users/Rau/Desktop/CasareRPA/monitoring-dashboard`

## Immediate gates

- `npm ci` must succeed from `package-lock.json` (no committed `node_modules` reliance).
- `npm run lint` must succeed (ESLint flat config).
- `npm run build` must succeed (TypeScript + Vite).

## File inventory (`monitoring-dashboard/src/`)

- `monitoring-dashboard/src/api/ApiContext.tsx`
- `monitoring-dashboard/src/api/client.ts`
- `monitoring-dashboard/src/App.tsx`
- `monitoring-dashboard/src/components/Layout.tsx`
- `monitoring-dashboard/src/hooks/useWebSocket.ts`
- `monitoring-dashboard/src/index.css`
- `monitoring-dashboard/src/main.tsx`
- `monitoring-dashboard/src/pages/AnalyticsPage.tsx`
- `monitoring-dashboard/src/pages/ApiKeysPage.tsx`
- `monitoring-dashboard/src/pages/DLQPage.tsx`
- `monitoring-dashboard/src/pages/JobsPage.tsx`
- `monitoring-dashboard/src/pages/RobotsPage.tsx`
- `monitoring-dashboard/src/pages/SchedulesPage.tsx`
- `monitoring-dashboard/src/types/index.ts`
- `monitoring-dashboard/src/vite-env.d.ts`
