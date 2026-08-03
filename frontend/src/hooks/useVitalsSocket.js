// src/hooks/useVitalsSocket.js
// Module 10: React hook for subscribing to real-time vitals + alerts via WebSocket
import { useEffect, useRef, useState, useCallback } from 'react'

/**
 * useVitalsSocket — connects to /ws/dashboard?token=<jwt>
 * Returns:
 *   latestVitals     — most recent vitals reading for any patient
 *   liveAlerts       — array of real-time alert objects (critical/moderate)
 *   connected        — boolean WebSocket state
 *   clearAlerts()    — dismiss all live alerts
 */
export default function useVitalsSocket() {
    const [latestVitals, setLatestVitals] = useState(null)
    const [liveAlerts, setLiveAlerts] = useState([])
    const [connected, setConnected] = useState(false)
    const wsRef = useRef(null)

    const connect = useCallback(() => {
        const token = localStorage.getItem('medscan_token') || ''
        const wsBase = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
        const url = `${wsBase}/ws/dashboard?token=${token}`

        const ws = new WebSocket(url)
        wsRef.current = ws

        ws.onopen = () => setConnected(true)

        ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data)
                if (msg.type === 'ping') {
                    ws.send(JSON.stringify({ type: 'pong' }))
                } else if (msg.type === 'vitals') {
                    setLatestVitals(msg.reading)
                } else if (msg.type === 'alert') {
                    setLiveAlerts(prev => [...msg.alerts, ...prev].slice(0, 20))
                }
            } catch { /* ignore malformed */ }
        }

        ws.onclose = () => { setConnected(false); wsRef.current = null }
        ws.onerror = () => ws.close()
    }, [])

    useEffect(() => {
        connect()
        // Reconnect on disconnect with 3s backoff
        const interval = setInterval(() => {
            if (!wsRef.current || wsRef.current.readyState > 1) connect()
        }, 3000)
        return () => {
            clearInterval(interval)
            wsRef.current?.close()
        }
    }, [connect])

    const clearAlerts = useCallback(() => setLiveAlerts([]), [])

    return { latestVitals, liveAlerts, connected, clearAlerts }
}
