/**
 * API client for CasareRPA Orchestrator backend.
 *
 * Provides typed axios instance for REST API calls and WebSocket client
 * for real-time metrics streaming.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws');

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging (dev mode only)
apiClient.interceptors.request.use(
  (config) => {
    if (import.meta.env.DEV) {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('[API] Response error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// =============================================================================
// WebSocket Client for Real-time Metrics
// =============================================================================

export interface MetricsWebSocketMessage {
  type: 'metrics';
  timestamp: string;
  data: MetricsSnapshot;
}

export interface MetricsSnapshot {
  timestamp: string;
  environment: string;
  queue_depth: number;
  active_jobs: number;
  total_robots: number;
  busy_robots: number;
  idle_robots: number;
  fleet_utilization_percent: number;
  jobs_completed: number;
  jobs_failed: number;
  jobs_cancelled: number;
  job_success_rate: number;
  average_job_duration_seconds: number;
  average_queue_wait_seconds: number;
  process_cpu_percent: number;
  process_memory_mb: number;
  system_cpu_percent: number;
  system_memory_percent: number;
  healing_attempts: number;
  healing_successes: number;
  healing_success_rate: number;
  top_nodes: Array<{
    node_type: string;
    total_executions: number;
    success_rate: number;
    avg_duration_ms: number;
  }>;
}

type MetricsCallback = (data: MetricsSnapshot) => void;
type ConnectionCallback = (connected: boolean) => void;
type ErrorCallback = (error: Event) => void;

export class MetricsWebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start at 1 second
  private maxReconnectDelay = 30000; // Max 30 seconds
  private reconnectTimer: NodeJS.Timeout | null = null;
  private manualClose = false;

  private metricsCallbacks: MetricsCallback[] = [];
  private connectionCallbacks: ConnectionCallback[] = [];
  private errorCallbacks: ErrorCallback[] = [];

  private interval: number;
  private environment: string;

  constructor(interval = 5, environment = 'development') {
    this.interval = interval;
    this.environment = environment;
  }

  /**
   * Connect to the metrics WebSocket stream.
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('[WS] Already connected');
      return;
    }

    this.manualClose = false;
    const url = `${WS_BASE_URL}/api/v1/metrics/stream?interval=${this.interval}&environment=${this.environment}`;

    console.log(`[WS] Connecting to ${url}`);

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('[WS] Connected');
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        this.notifyConnectionCallbacks(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const message: MetricsWebSocketMessage = JSON.parse(event.data);
          if (message.type === 'metrics') {
            this.notifyMetricsCallbacks(message.data);
          }
        } catch (e) {
          console.error('[WS] Failed to parse message:', e);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[WS] Error:', error);
        this.notifyErrorCallbacks(error);
      };

      this.ws.onclose = (event) => {
        console.log(`[WS] Closed (code=${event.code}, reason=${event.reason})`);
        this.notifyConnectionCallbacks(false);

        if (!this.manualClose) {
          this.scheduleReconnect();
        }
      };
    } catch (error) {
      console.error('[WS] Failed to create WebSocket:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from the WebSocket.
   */
  disconnect(): void {
    this.manualClose = true;

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  /**
   * Check if currently connected.
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Subscribe to metrics updates.
   */
  onMetrics(callback: MetricsCallback): () => void {
    this.metricsCallbacks.push(callback);
    return () => {
      this.metricsCallbacks = this.metricsCallbacks.filter(cb => cb !== callback);
    };
  }

  /**
   * Subscribe to connection state changes.
   */
  onConnection(callback: ConnectionCallback): () => void {
    this.connectionCallbacks.push(callback);
    return () => {
      this.connectionCallbacks = this.connectionCallbacks.filter(cb => cb !== callback);
    };
  }

  /**
   * Subscribe to errors.
   */
  onError(callback: ErrorCallback): () => void {
    this.errorCallbacks.push(callback);
    return () => {
      this.errorCallbacks = this.errorCallbacks.filter(cb => cb !== callback);
    };
  }

  private scheduleReconnect(): void {
    if (this.manualClose || this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('[WS] Max reconnect attempts reached or manual close');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    );

    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private notifyMetricsCallbacks(data: MetricsSnapshot): void {
    this.metricsCallbacks.forEach(cb => {
      try {
        cb(data);
      } catch (e) {
        console.error('[WS] Metrics callback error:', e);
      }
    });
  }

  private notifyConnectionCallbacks(connected: boolean): void {
    this.connectionCallbacks.forEach(cb => {
      try {
        cb(connected);
      } catch (e) {
        console.error('[WS] Connection callback error:', e);
      }
    });
  }

  private notifyErrorCallbacks(error: Event): void {
    this.errorCallbacks.forEach(cb => {
      try {
        cb(error);
      } catch (e) {
        console.error('[WS] Error callback error:', e);
      }
    });
  }
}

// Singleton WebSocket client instance
let metricsWsClient: MetricsWebSocketClient | null = null;

/**
 * Get or create the singleton MetricsWebSocketClient.
 */
export function getMetricsWebSocket(
  interval = 5,
  environment = 'development'
): MetricsWebSocketClient {
  if (!metricsWsClient) {
    metricsWsClient = new MetricsWebSocketClient(interval, environment);
  }
  return metricsWsClient;
}

export default apiClient;
