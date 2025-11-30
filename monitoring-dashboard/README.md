# CasareRPA Monitoring Dashboard

Real-time monitoring dashboard for the CasareRPA enterprise RPA platform. Built with **React 19**, **TypeScript**, **Vite**, and **TailwindCSS**.

## Features

- **Real-time Fleet Monitoring**: Live WebSocket updates for robot status and job execution
- **Job Tracking**: Monitor workflow executions across LAN and internet robots
- **Queue Metrics**: Visualize job queues and processing rates
- **Responsive Design**: Modern UI optimized for desktop and tablet devices
- **Auto-Reconnecting WebSockets**: Resilient connections with exponential backoff

## Architecture

The dashboard connects to the CasareRPA Orchestrator API via:
- **REST API** (`/api/v1/*`): Job management, workflow submission, metrics
- **WebSocket** (`/ws/*`): Real-time updates for jobs, robots, and queues

## Setup

### Prerequisites

- **Node.js** 18+ and npm/yarn/pnpm
- **CasareRPA Orchestrator API** running (default: `http://localhost:8000`)

### Installation

```bash
# Install dependencies
npm install

# Copy environment template
cp .env.example .env

# Edit .env with your Orchestrator URL (if not localhost)
# VITE_API_BASE_URL=http://your-orchestrator-ip:8000
# VITE_WS_BASE_URL=ws://your-orchestrator-ip:8000
```

### Development

```bash
# Start development server (port 5173)
npm run dev

# The app will be available at http://localhost:5173
# API requests proxy to http://localhost:8000 (configured in vite.config.ts)
```

### Production Build

```bash
# Build for production
npm run build

# Output: ../src/casare_rpa/orchestrator/api/static/
# The build is configured to be served by the FastAPI Orchestrator directly

# Preview production build locally
npm run preview
```

## Environment Variables

Create a `.env` file based on `.env.example`:

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Orchestrator REST API URL |
| `VITE_WS_BASE_URL` | `ws://localhost:8000` | Orchestrator WebSocket URL |

**Note**: For HTTPS deployments, use `https://` and `wss://` respectively.

## Project Structure

```
monitoring-dashboard/
├── src/
│   ├── api/                # API clients and WebSocket hooks
│   │   ├── client.ts       # Axios REST client
│   │   └── websockets.ts   # WebSocket hooks (useWebSocket, useLiveJobs, etc.)
│   ├── components/         # React components
│   ├── hooks/              # Custom React hooks
│   ├── pages/              # Page components
│   ├── types/              # TypeScript type definitions
│   └── App.tsx             # Main application component
├── public/                 # Static assets
├── .env.example            # Environment template
├── .env                    # Local environment (gitignored)
├── vite.config.ts          # Vite configuration
└── package.json
```

## API Integration

### REST API Endpoints

- `GET /api/v1/metrics` - System metrics
- `POST /api/v1/workflows` - Submit workflow
- `GET /api/v1/schedules` - List schedules
- `GET /health` - Health check

### WebSocket Endpoints

- `/ws/live-jobs` - Real-time job status updates
- `/ws/robot-status` - Robot heartbeat and availability
- `/ws/queue-metrics` - Queue depth and throughput metrics

All WebSocket connections auto-reconnect with exponential backoff (max 5 attempts, 3-30 second intervals).

## Development Tips

- **Hot Module Replacement (HMR)**: Changes auto-reload in development
- **TypeScript**: Strict type checking enabled
- **ESLint**: Configured for React and TypeScript
- **Console Logging**: WebSocket and API calls logged in dev mode only

## Deployment

### Option 1: Serve from FastAPI Orchestrator (Recommended)

```bash
# Build dashboard
npm run build

# Built files are automatically copied to:
# ../src/casare_rpa/orchestrator/api/static/

# Start Orchestrator API (serves dashboard at root)
uvicorn casare_rpa.infrastructure.orchestrator.api.main:app --host 0.0.0.0 --port 8000

# Access dashboard at http://your-server:8000
```

### Option 2: Serve Separately (e.g., Nginx)

```bash
npm run build

# Copy dist/ folder to your web server
# Configure reverse proxy to Orchestrator API
```

### Option 3: Docker (Future)

```dockerfile
# Example - not yet implemented
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
CMD ["npm", "run", "preview"]
```

## Troubleshooting

### WebSocket Connection Failed

- Ensure Orchestrator API is running: `http://localhost:8000/health`
- Check CORS settings in Orchestrator API `main.py`
- Verify `VITE_WS_BASE_URL` in `.env` matches Orchestrator host

### API Requests Fail

- Verify `VITE_API_BASE_URL` in `.env`
- Check network connectivity to Orchestrator
- Review browser console for CORS errors

### Build Errors

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
npm run build
```

## Tech Stack

- **React** 19.0 - UI framework
- **TypeScript** 5.6 - Type safety
- **Vite** 6.0 - Build tool & dev server
- **TailwindCSS** 3.x - Utility-first CSS
- **Axios** - HTTP client
- **WebSocket API** - Real-time communication
- **ESLint** - Code linting

## License

Part of the CasareRPA platform. See root LICENSE file.

## Support

For issues or questions, open an issue in the main CasareRPA repository.
