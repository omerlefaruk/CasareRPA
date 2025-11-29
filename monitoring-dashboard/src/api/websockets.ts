/**
 * WebSocket hooks for real-time updates.
 *
 * Provides auto-reconnecting WebSocket connections with React hooks.
 */

import { useEffect, useRef, useState, useCallback } from 'react';

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

interface UseWebSocketOptions {
  onMessage?: (data: any) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

export function useWebSocket(
  endpoint: string,
  options: UseWebSocketOptions = {}
) {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    reconnectAttempts = 5,
    reconnectInterval = 3000,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    const url = `${WS_BASE_URL}${endpoint}`;
    console.log(`[WS] Connecting to ${url}`);

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log(`[WS] Connected to ${endpoint}`);
      setIsConnected(true);
      reconnectCountRef.current = 0;
      onConnect?.();
    };

    ws.onclose = () => {
      console.log(`[WS] Disconnected from ${endpoint}`);
      setIsConnected(false);
      onDisconnect?.();

      // Auto-reconnect
      if (reconnectCountRef.current < reconnectAttempts) {
        reconnectCountRef.current++;
        console.log(
          `[WS] Reconnecting... (${reconnectCountRef.current}/${reconnectAttempts})`
        );

        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, reconnectInterval);
      } else {
        console.error(`[WS] Max reconnect attempts reached for ${endpoint}`);
      }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log(`[WS] Message from ${endpoint}:`, data);
        setLastMessage(data);
        onMessage?.(data);
      } catch (error) {
        console.error(`[WS] Failed to parse message:`, error);
      }
    };

    ws.onerror = (error) => {
      console.error(`[WS] Error on ${endpoint}:`, error);
    };
  }, [endpoint, onConnect, onDisconnect, onMessage, reconnectAttempts, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('[WS] WebSocket not connected, cannot send message');
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { isConnected, lastMessage, sendMessage, disconnect };
}

// Specific hooks for different WebSocket endpoints
export function useLiveJobs(onMessage?: (data: any) => void) {
  return useWebSocket('/ws/live-jobs', { onMessage });
}

export function useRobotStatus(onMessage?: (data: any) => void) {
  return useWebSocket('/ws/robot-status', { onMessage });
}

export function useQueueMetrics(onMessage?: (data: any) => void) {
  return useWebSocket('/ws/queue-metrics', { onMessage });
}
