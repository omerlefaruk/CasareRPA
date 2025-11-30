/**
 * Enhanced WebSocket manager with batched updates and auto-reconnect.
 *
 * Connects to multiple WebSocket endpoints and batches updates using
 * requestAnimationFrame for optimal rendering performance.
 */

import { useEffect, useRef, useCallback } from 'react';
import {
  useMetricsStore,
  type FleetMetrics,
  type RobotStatus,
  type ActivityEvent,
} from '@/store/metricsStore';
import {
  RobotStatusSchema,
  RobotBatchSchema,
  FleetMetricsSchema,
  QueueDepthSchema,
  RobotEventSchema,
  ScheduleEventSchema,
  JobEventSchema,
  safeParseMessage,
} from '@/schemas/websocket';

// ============================================================================
// Configuration
// ============================================================================

// In production, VITE_WS_BASE_URL must be set. In development, fall back to localhost.
const getWebSocketBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_WS_BASE_URL;
  if (envUrl) return envUrl;

  if (import.meta.env.PROD) {
    // In production, derive WebSocket URL from current location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}`;
  }

  // Development fallback
  return 'ws://localhost:8000';
};

const WS_BASE_URL = getWebSocketBaseUrl();

// Batching configuration
const BATCH_INTERVAL_MS = 100;

// Reconnect configuration (exponential backoff)
const INITIAL_RECONNECT_DELAY_MS = 1000;
const MAX_RECONNECT_DELAY_MS = 30000;
const MAX_RECONNECT_ATTEMPTS = 10;

// WebSocket endpoints
const WS_ENDPOINTS = {
  robotStatus: '/ws/robot-status',
  queueMetrics: '/ws/queue-metrics',
  liveJobs: '/ws/live-jobs',
} as const;

// ============================================================================
// Types
// ============================================================================

type WebSocketEndpoint = keyof typeof WS_ENDPOINTS;

interface WebSocketState {
  socket: WebSocket | null;
  reconnectAttempts: number;
  reconnectTimeout: ReturnType<typeof setTimeout> | null;
}

interface BatchedUpdate {
  robotStatuses: RobotStatus[];
  fleetMetrics: FleetMetrics | null;
  queueDepth: number | null;
  activityEvents: ActivityEvent[];
}

interface WebSocketManagerResult {
  isConnected: boolean;
  connectionStates: Record<WebSocketEndpoint, boolean>;
  reconnect: () => void;
  disconnect: () => void;
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useWebSocketManager(): WebSocketManagerResult {
  // Access store actions directly - they are stable references and don't need subscription
  const updateFleetMetrics = useMetricsStore((state) => state.updateFleetMetrics);
  const batchUpdateRobotStatuses = useMetricsStore((state) => state.batchUpdateRobotStatuses);
  const addActivityEvent = useMetricsStore((state) => state.addActivityEvent);
  const setQueueDepth = useMetricsStore((state) => state.setQueueDepth);

  // WebSocket state for each endpoint
  const socketStates = useRef<Record<WebSocketEndpoint, WebSocketState>>({
    robotStatus: { socket: null, reconnectAttempts: 0, reconnectTimeout: null },
    queueMetrics: { socket: null, reconnectAttempts: 0, reconnectTimeout: null },
    liveJobs: { socket: null, reconnectAttempts: 0, reconnectTimeout: null },
  });

  // Connection state tracking
  const connectionStates = useRef<Record<WebSocketEndpoint, boolean>>({
    robotStatus: false,
    queueMetrics: false,
    liveJobs: false,
  });

  // Batched updates buffer
  const batchBuffer = useRef<BatchedUpdate>({
    robotStatuses: [],
    fleetMetrics: null,
    queueDepth: null,
    activityEvents: [],
  });

  // RAF handle for batching
  const rafHandle = useRef<number | null>(null);
  const lastBatchTime = useRef<number>(0);

  // ============================================================================
  // Batched Update Processor
  // ============================================================================

  const processBatchedUpdates = useCallback(() => {
    const now = performance.now();
    const timeSinceLastBatch = now - lastBatchTime.current;

    // Only process if enough time has passed
    if (timeSinceLastBatch < BATCH_INTERVAL_MS) {
      rafHandle.current = requestAnimationFrame(processBatchedUpdates);
      return;
    }

    const buffer = batchBuffer.current;

    // Process robot status updates
    if (buffer.robotStatuses.length > 0) {
      batchUpdateRobotStatuses(buffer.robotStatuses);
      buffer.robotStatuses = [];
    }

    // Process fleet metrics
    if (buffer.fleetMetrics !== null) {
      updateFleetMetrics(buffer.fleetMetrics);
      buffer.fleetMetrics = null;
    }

    // Process queue depth
    if (buffer.queueDepth !== null) {
      setQueueDepth(buffer.queueDepth);
      buffer.queueDepth = null;
    }

    // Process activity events
    if (buffer.activityEvents.length > 0) {
      for (const event of buffer.activityEvents) {
        addActivityEvent(event);
      }
      buffer.activityEvents = [];
    }

    lastBatchTime.current = now;
    rafHandle.current = requestAnimationFrame(processBatchedUpdates);
  }, [batchUpdateRobotStatuses, updateFleetMetrics, setQueueDepth, addActivityEvent]);

  // ============================================================================
  // Message Handlers
  // ============================================================================

  const handleRobotStatusMessage = useCallback((data: unknown) => {
    if (!data || typeof data !== 'object') return;

    // Try to parse as single robot status (with Zod validation)
    const singleStatus = safeParseMessage(RobotStatusSchema, data);
    if (singleStatus) {
      batchBuffer.current.robotStatuses.push(singleStatus as RobotStatus);
      return;
    }

    // Try to parse as batch of robot statuses
    const batchStatus = safeParseMessage(RobotBatchSchema, data);
    if (batchStatus) {
      for (const robot of batchStatus.robots) {
        batchBuffer.current.robotStatuses.push(robot as RobotStatus);
      }
      return;
    }

    // Try to parse as robot event
    const robotEvent = safeParseMessage(RobotEventSchema, data);
    if (robotEvent) {
      const event: ActivityEvent = {
        id: crypto.randomUUID(),
        type: robotEvent.type,
        timestamp: robotEvent.timestamp || new Date().toISOString(),
        title: robotEvent.type === 'robot_online' ? 'Robot Online' : 'Robot Offline',
        details: `Robot ${robotEvent.robot_id} is now ${robotEvent.type === 'robot_online' ? 'online' : 'offline'}`,
        robotId: robotEvent.robot_id,
      };
      batchBuffer.current.activityEvents.push(event);
    }
  }, []);

  const handleQueueMetricsMessage = useCallback((data: unknown) => {
    if (!data || typeof data !== 'object') return;

    // Try to parse as fleet metrics (with Zod validation)
    const fleetMetrics = safeParseMessage(FleetMetricsSchema, data);
    if (fleetMetrics) {
      batchBuffer.current.fleetMetrics = fleetMetrics as FleetMetrics;
      return;
    }

    // Try to parse as queue depth update
    const queueDepth = safeParseMessage(QueueDepthSchema, data);
    if (queueDepth) {
      batchBuffer.current.queueDepth = queueDepth.queue_depth;
      return;
    }

    // Try to parse as schedule triggered event
    const scheduleEvent = safeParseMessage(ScheduleEventSchema, data);
    if (scheduleEvent) {
      const event: ActivityEvent = {
        id: crypto.randomUUID(),
        type: 'schedule_triggered',
        timestamp: scheduleEvent.timestamp || new Date().toISOString(),
        title: 'Schedule Triggered',
        details: scheduleEvent.schedule_name,
        jobId: scheduleEvent.job_id,
      };
      batchBuffer.current.activityEvents.push(event);
    }
  }, []);

  const handleLiveJobsMessage = useCallback((data: unknown) => {
    if (!data || typeof data !== 'object') return;

    // Try to parse as job event (with Zod validation)
    const jobEvent = safeParseMessage(JobEventSchema, data);
    if (jobEvent) {
      const event: ActivityEvent = {
        id: crypto.randomUUID(),
        type: jobEvent.type,
        timestamp: jobEvent.timestamp || new Date().toISOString(),
        title: formatJobEventTitle(jobEvent.type),
        details: jobEvent.workflow_name,
        robotId: jobEvent.robot_id,
        jobId: jobEvent.job_id,
      };
      batchBuffer.current.activityEvents.push(event);
    }
  }, []);

  // ============================================================================
  // WebSocket Connection Management
  // ============================================================================

  const createWebSocket = useCallback((endpoint: WebSocketEndpoint): WebSocket => {
    const url = `${WS_BASE_URL}${WS_ENDPOINTS[endpoint]}`;
    const ws = new WebSocket(url);
    const state = socketStates.current[endpoint];

    ws.onopen = () => {
      if (import.meta.env.DEV) {
        console.log(`[WSManager] Connected: ${endpoint}`);
      }
      connectionStates.current[endpoint] = true;
      state.reconnectAttempts = 0;
    };

    ws.onclose = () => {
      if (import.meta.env.DEV) {
        console.log(`[WSManager] Disconnected: ${endpoint}`);
      }
      connectionStates.current[endpoint] = false;
      scheduleReconnect(endpoint);
    };

    ws.onerror = (error) => {
      console.error(`[WSManager] Error on ${endpoint}:`, error);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        switch (endpoint) {
          case 'robotStatus':
            handleRobotStatusMessage(data);
            break;
          case 'queueMetrics':
            handleQueueMetricsMessage(data);
            break;
          case 'liveJobs':
            handleLiveJobsMessage(data);
            break;
        }
      } catch (error) {
        console.error(`[WSManager] Failed to parse message from ${endpoint}:`, error);
      }
    };

    return ws;
  }, [handleRobotStatusMessage, handleQueueMetricsMessage, handleLiveJobsMessage]);

  const scheduleReconnect = useCallback((endpoint: WebSocketEndpoint) => {
    const state = socketStates.current[endpoint];

    // Clear existing timeout
    if (state.reconnectTimeout) {
      clearTimeout(state.reconnectTimeout);
    }

    // Stop reconnecting after max attempts
    if (state.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.warn(`[WSManager] Max reconnect attempts (${MAX_RECONNECT_ATTEMPTS}) reached for ${endpoint}. Use reconnect() to retry.`);
      return;
    }

    // Calculate delay with exponential backoff
    const delay = Math.min(
      INITIAL_RECONNECT_DELAY_MS * Math.pow(2, state.reconnectAttempts),
      MAX_RECONNECT_DELAY_MS
    );

    if (import.meta.env.DEV) {
      console.log(`[WSManager] Reconnecting ${endpoint} in ${delay}ms (attempt ${state.reconnectAttempts + 1}/${MAX_RECONNECT_ATTEMPTS})`);
    }

    state.reconnectTimeout = setTimeout(() => {
      state.reconnectAttempts++;
      state.socket = createWebSocket(endpoint);
    }, delay);
  }, [createWebSocket]);

  const connectAll = useCallback(() => {
    const endpoints: WebSocketEndpoint[] = ['robotStatus', 'queueMetrics', 'liveJobs'];

    for (const endpoint of endpoints) {
      const state = socketStates.current[endpoint];

      // Close existing connection if any
      if (state.socket) {
        state.socket.close();
      }

      // Clear any pending reconnect
      if (state.reconnectTimeout) {
        clearTimeout(state.reconnectTimeout);
        state.reconnectTimeout = null;
      }

      state.reconnectAttempts = 0;
      state.socket = createWebSocket(endpoint);
    }

    // Start batched update processor
    if (rafHandle.current === null) {
      lastBatchTime.current = performance.now();
      rafHandle.current = requestAnimationFrame(processBatchedUpdates);
    }
  }, [createWebSocket, processBatchedUpdates]);

  const disconnectAll = useCallback(() => {
    const endpoints: WebSocketEndpoint[] = ['robotStatus', 'queueMetrics', 'liveJobs'];

    for (const endpoint of endpoints) {
      const state = socketStates.current[endpoint];

      if (state.reconnectTimeout) {
        clearTimeout(state.reconnectTimeout);
        state.reconnectTimeout = null;
      }

      if (state.socket) {
        state.socket.close();
        state.socket = null;
      }

      connectionStates.current[endpoint] = false;
    }

    // Stop batched update processor
    if (rafHandle.current !== null) {
      cancelAnimationFrame(rafHandle.current);
      rafHandle.current = null;
    }
  }, []);

  // ============================================================================
  // Lifecycle
  // ============================================================================

  useEffect(() => {
    connectAll();
    return () => disconnectAll();
  }, [connectAll, disconnectAll]);

  // ============================================================================
  // Return Value
  // ============================================================================

  const isConnected = connectionStates.current.robotStatus ||
    connectionStates.current.queueMetrics ||
    connectionStates.current.liveJobs;

  return {
    isConnected,
    connectionStates: { ...connectionStates.current },
    reconnect: connectAll,
    disconnect: disconnectAll,
  };
}

// ============================================================================
// Helpers
// ============================================================================

function formatJobEventTitle(type: string): string {
  switch (type) {
    case 'job_started':
      return 'Job Started';
    case 'job_completed':
      return 'Job Completed';
    case 'job_failed':
      return 'Job Failed';
    default:
      return 'Job Event';
  }
}
