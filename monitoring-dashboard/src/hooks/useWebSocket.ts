import { useEffect, useRef, useState, useCallback } from 'react'
import type { WSMessage, WSJobUpdate, WSRobotUpdate, WSQueueUpdate } from '../types'

const WS_BASE = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/ws`

interface UseWebSocketOptions {
  onMessage?: (message: WSMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  reconnectInterval?: number
}

function useWebSocket(endpoint: string, options: UseWebSocketOptions = {}) {
  const { onMessage, onConnect, onDisconnect, reconnectInterval = 3000 } = options
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(`${WS_BASE}${endpoint}`)

    ws.onopen = () => {
      setIsConnected(true)
      onConnect?.()
    }

    ws.onclose = () => {
      setIsConnected(false)
      onDisconnect?.()
      // Reconnect after delay
      reconnectTimeoutRef.current = window.setTimeout(connect, reconnectInterval)
    }

    ws.onerror = () => {
      ws.close()
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WSMessage
        onMessage?.(message)
      } catch {
        console.warn('Failed to parse WebSocket message:', event.data)
      }
    }

    wsRef.current = ws
  }, [endpoint, onMessage, onConnect, onDisconnect, reconnectInterval])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      wsRef.current?.close()
    }
  }, [connect])

  return { isConnected }
}

// Hook for job status updates
export function useJobsWebSocket(onUpdate: (update: WSJobUpdate) => void) {
  return useWebSocket('/jobs', {
    onMessage: (msg) => {
      if (msg.type === 'job_status') {
        onUpdate(msg as WSJobUpdate)
      }
    },
  })
}

// Hook for robot heartbeat updates
export function useRobotsWebSocket(onUpdate: (update: WSRobotUpdate) => void) {
  return useWebSocket('/robots', {
    onMessage: (msg) => {
      if (msg.type === 'robot_heartbeat' || msg.type === 'robot_status') {
        onUpdate(msg as WSRobotUpdate)
      }
    },
  })
}

// Hook for queue depth updates
export function useQueueWebSocket(onUpdate: (update: WSQueueUpdate) => void) {
  return useWebSocket('/queue-depth', {
    onMessage: (msg) => {
      if (msg.type === 'queue_depth') {
        onUpdate(msg as WSQueueUpdate)
      }
    },
  })
}

export { useWebSocket }
