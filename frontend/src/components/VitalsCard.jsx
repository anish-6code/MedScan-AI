// src/components/VitalsCard.jsx
// Module 10: Live vitals display card — updates in real-time via useVitalsSocket
import { useEffect, useState } from 'react'

const VITAL_LABELS = {
    heart_rate: { label: 'Heart Rate', unit: 'bpm', icon: '♥', normal: [60, 100] },
    spo2: { label: 'SpO₂', unit: '%', icon: '🫁', normal: [95, 100] },
    systolic_bp: { label: 'Systolic BP', unit: 'mmHg', icon: '🩸', normal: [90, 140] },
    diastolic_bp: { label: 'Diastolic BP', unit: 'mmHg', icon: '🩸', normal: [60, 90] },
    temperature: { label: 'Temperature', unit: '°C', icon: '🌡', normal: [36, 37.5] },
    respiratory_rate: { label: 'Resp. Rate', unit: '/min', icon: '💨', normal: [12, 20] },
}

function vitalStatus(key, value) {
    const cfg = VITAL_LABELS[key]
    if (!cfg || value == null) return 'muted'
    const [lo, hi] = cfg.normal
    if (value < lo || value > hi) return 'danger'
    const margin = (hi - lo) * 0.1
    if (value < lo + margin || value > hi - margin) return 'warning'
    return 'success'
}

function SingleVital({ name, value }) {
    const cfg = VITAL_LABELS[name]
    const status = vitalStatus(name, value)
    const color = { danger: 'var(--danger)', warning: 'var(--warning)', success: 'var(--success)', muted: 'var(--text-muted)' }[status]

    return (
        <div style={{
            background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)',
            padding: '.85rem 1rem', display: 'flex', flexDirection: 'column', gap: '.25rem',
            borderLeft: `3px solid ${color}`,
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '.4rem', fontSize: '.75rem', color: 'var(--text-muted)' }}>
                <span>{cfg?.icon}</span>
                <span>{cfg?.label || name}</span>
            </div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, color }}>
                {value != null ? value : '—'}
                <span style={{ fontSize: '.75rem', fontWeight: 400, color: 'var(--text-muted)', marginLeft: '.3rem' }}>
                    {cfg?.unit}
                </span>
            </div>
        </div>
    )
}

export default function VitalsCard({ reading, connected }) {
    const [flash, setFlash] = useState(false)

    useEffect(() => {
        if (reading) { setFlash(true); setTimeout(() => setFlash(false), 600) }
    }, [reading])

    const VITALS = ['heart_rate', 'spo2', 'systolic_bp', 'diastolic_bp', 'temperature', 'respiratory_rate']

    return (
        <div className="card" style={{
            padding: '1.25rem',
            outline: flash ? '2px solid var(--primary)' : '2px solid transparent',
            transition: 'outline .3s ease',
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h2 style={{ fontWeight: 600, fontSize: '1rem' }}>Live Vitals</h2>
                <span style={{
                    fontSize: '.7rem', padding: '.2rem .6rem', borderRadius: 999,
                    background: connected ? 'rgba(16,185,129,.15)' : 'rgba(239,68,68,.15)',
                    color: connected ? 'var(--success)' : 'var(--danger)',
                }}>
                    {connected ? '● LIVE' : '○ DISCONNECTED'}
                </span>
            </div>
            {reading ? (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.65rem' }}>
                    {VITALS.map(k => <SingleVital key={k} name={k} value={reading[k]} />)}
                </div>
            ) : (
                <p style={{ color: 'var(--text-muted)', fontSize: '.875rem' }}>
                    {connected ? 'Waiting for first reading…' : 'Connecting to real-time feed…'}
                </p>
            )}
            {reading && (
                <p style={{ marginTop: '.75rem', fontSize: '.7rem', color: 'var(--text-muted)' }}>
                    Source: {reading.source || 'unknown'} · {new Date(reading.recorded_at || Date.now()).toLocaleTimeString()}
                </p>
            )}
        </div>
    )
}
