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

// ============================================================================
// Configuration
// ============================================================================

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

// Batching configuration
const BATCH_INTERVAL_MS = 100;

// Reconnect configuration (exponential backoff)
const INITIAL_RECONNECT_DELAY_MS = 1000;
const MAX_RECONNECT_DELAY_MS = 30000;

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

    const message = data as Record<string, unknown>;

    // Handle single robot status update
    if (message.robot_id && message.status) {
      batchBuffer.current.robotStatuses.push(message as unknown as RobotStatus);
      return;
    }

    // Handle batch of robot statuses
    if (Array.isArray(message.robots)) {
      for (const robot of message.robots) {
        if (robot.robot_id && robot.status) {
          batchBuffer.current.robotStatuses.push(robot as RobotStatus);
        }
      }
      return;
    }

    // Handle robot online/offline events
    if (message.type === 'robot_online' || message.type === 'robot_offline') {
      const event: ActivityEvent = {
        id: crypto.randomUUID(),
        type: message.type as 'robot_online' | 'robot_offline',
        timestamp: (message.timestamp as string) || new Date().toISOString(),
        title: message.type === 'robot_online' ? 'Robot Online' : 'Robot Offline',
        details: `Robot ${message.robot_id} is now ${message.type === 'robot_online' ? 'online' : 'offline'}`,
        robotId: message.robot_id as string,
      };
      batchBuffer.current.activityEvents.push(event);
    }
  }, []);

  const handleQueueMetricsMessage = useCallback((data: unknown) => {
    if (!data || typeof data !== 'object') return;

    const message = data as Record<string, unknown>;

    // Handle fleet metrics update
    if (typeof message.total_robots === 'number') {
      batchBuffer.current.fleetMetrics = message as unknown as FleetMetrics;
      return;
    }

    // Handle queue depth update
    if (typeof message.queue_depth === 'number') {
      batchBuffer.current.queueDepth = message.queue_depth;
      return;
    }

    // Handle schedule triggered events
    if (message.type === 'schedule_triggered') {
      const event: ActivityEvent = {
        id: crypto.randomUUID(),
        type: 'schedule_triggered',
        timestamp: (message.timestamp as string) || new Date().toISOString(),
        title: 'Schedule Triggered',
        details: message.schedule_name as string,
        jobId: message.job_id as string,
      };
      batchBuffer.current.activityEvents.push(event);
    }
  }, []);

  const handleLiveJobsMessage = useCallback((data: unknown) => {
    if (!data || typeof data !== 'object') return;

    const message = data as Record<string, unknown>;
    const messageType = message.type as string;

    // Map job events to activity events
    if (messageType === 'job_started' || messageType === 'job_completed' || messageType === 'job_failed') {
      const event: ActivityEvent = {
        id: crypto.randomUUID(),
        type: messageType as 'job_started' | 'job_completed' | 'job_failed',
        timestamp: (message.timestamp as string) || new Date().toISOString(),
        title: formatJobEventTitle(messageType),
        details: message.workflow_name as string | undefined,
        robotId: message.robot_id as string | undefined,
        jobId: message.job_id as string,
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

    // Calculate delay with exponential backoff
    const delay = Math.min(
      INITIAL_RECONNECT_DELAY_MS * Math.pow(2, state.reconnectAttempts),
      MAX_RECONNECT_DELAY_MS
    );

    if (import.meta.env.DEV) {
      console.log(`[WSManager] Reconnecting ${endpoint} in ${delay}ms (attempt ${state.reconnectAttempts + 1})`);
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
