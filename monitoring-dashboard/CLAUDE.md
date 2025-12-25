# Monitoring Dashboard Rules

**React 18.3 + Vite 6.0 + Tailwind 3.4 for Orchestrator dashboard.**

## Tech Stack

```json
{
  "react": "18.3.1",
  "vite": "6.0.1",
  "tailwindcss": "3.4.15"
}
```

## Core Principles

1. **Component-First**: Small, reusable components
2. **TypeScript**: Type all props and state
3. **Tailwind**: Utility classes, no custom CSS
4. **API-First**: Data from Orchestrator backend

## Component Structure

```
src/
├── components/     # Reusable UI components
├── pages/          # Route pages
├── hooks/          # Custom React hooks
├── services/       # API clients
└── types/          # TypeScript types
```

## Tailwind Usage

```tsx
// CORRECT
<div className="flex items-center gap-4 p-4 bg-white rounded-lg">

// WRONG
<div style={{display: 'flex', padding: '16px'}}>
```

## API Integration

```tsx
import { useQuery } from '@tanstack/react-query'

function RobotList() {
  const { data, isLoading } = useQuery({
    queryKey: ['robots'],
    queryFn: () => fetch('/api/robots').then(r => r.json())
  })
}
```

## Cross-References

- Root guide: `../CLAUDE.md`
- Orchestrator: `../src/casare_rpa/infrastructure/orchestrator/`
