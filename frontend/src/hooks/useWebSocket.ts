import { useEffect, useRef, useCallback } from 'react'
import type { WSMessage } from '../types'
import { useStore } from '../store/useStore'

export function useWebSocket(storyId: string) {
  const wsRef = useRef<WebSocket | null>(null)
  const handleWSMessage = useStore((s) => s.handleWSMessage)

  const connect = useCallback(() => {
    if (!storyId) return
    const ws = new WebSocket(`ws://localhost:8000/ws/stories/${storyId}`)
    wsRef.current = ws

    ws.onopen = () => console.log('[WS] Connected to', storyId)
    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data)
        handleWSMessage(msg)
      } catch (e) {
        console.error('[WS] Parse error', e)
      }
    }
    ws.onerror = (e) => console.error('[WS] Error', e)
    ws.onclose = () => {
      console.log('[WS] Disconnected')
      wsRef.current = null
    }
  }, [storyId, handleWSMessage])

  const disconnect = useCallback(() => {
    wsRef.current?.close()
    wsRef.current = null
  }, [])

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  useEffect(() => {
    return () => disconnect()
  }, [disconnect])

  return { connect, disconnect, send }
}
