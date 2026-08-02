// src/pages/PatientDashboard.jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listPatients } from '../api/patients'
import { listScans, getResult } from '../api/scans'
import AlertsPanel from '../components/AlertsPanel'

function StatusBadge({ status }) {
    const map = {
        done: 'badge-success', processing: 'badge-warning',
        failed: 'badge-danger', uploaded: 'badge-muted', preprocessed: 'badge-primary'
    }
    return <span className={`badge ${map[status] || 'badge-muted'}`}>{status}</span>
}

function ConfidenceBar({ value }) {
    const pct = Math.round((value || 0) * 100)
    const cls = value >= 0.7 ? 'high' : value >= 0.4 ? 'mod' : 'low'
    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontSize: '.75rem', color: 'var(--text-muted)' }}>Confidence</span>
                <span style={{ fontSize: '.75rem', fontWeight: 600 }}>{pct}%</span>
            </div>
            <div className="confidence-bar">
                <div className={`confidence-fill ${cls}`} style={{ width: `${pct}%` }} />
            </div>
        </div>
    )
}

export default function PatientDashboard() {
    const [patients, setPatients] = useState([])
    const [selected, setSelected] = useState(null)
    const [scans, setScans] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        listPatients()
            .then(r => { setPatients(r.data); if (r.data.length) setSelected(r.data[0]) })
            .catch(() => { })
            .finally(() => setLoading(false))
    }, [])

    useEffect(() => {
        if (!selected) return
        listScans(selected.id).then(async r => {
            // Enrich with AI results
            const enriched = await Promise.all(
                r.data.map(async scan => {
                    if (scan.status === 'done') {
                        try { const res = await getResult(scan.id); return { ...scan, result: res.data } }
                        catch { return scan }
                    }
                    return scan
                })
            )
            setScans(enriched)
        }).catch(() => setScans([]))
    }, [selected])

    if (loading) return (
        <div className="page"><div className="container" style={{ textAlign: 'center', marginTop: '4rem' }}>
            <p className="pulse" style={{ color: 'var(--text-muted)' }}>Loading patients…</p>
        </div></div>
    )

    return (
        <div className="page">
            <div className="container">
                <div className="page-header">
                    <div>
                        <h1 className="page-title">Patient Dashboard</h1>
                        <p className="page-subtitle">{patients.length} patients assigned to you</p>
                    </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '1.5rem', alignItems: 'start' }}>
                    {/* Patient list */}
                    <div className="card" style={{ overflow: 'hidden' }}>
                        <div style={{
                            padding: '.75rem 1rem', borderBottom: '1px solid var(--border)',
                            fontSize: '.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '.06em'
                        }}>
                            Patients
                        </div>
                        {patients.map(p => (
                            <button key={p.id} onClick={() => setSelected(p)} style={{
                                width: '100%', display: 'block', textAlign: 'left',
                                padding: '.85rem 1rem', background: selected?.id === p.id ? 'var(--bg-surface)' : 'transparent',
                                border: 'none', color: 'var(--text)', fontSize: '.875rem',
                                borderBottom: '1px solid var(--border)', transition: 'var(--transition)',
                                borderLeft: selected?.id === p.id ? '3px solid var(--primary)' : '3px solid transparent',
                            }}>
                                <p style={{ fontWeight: 600 }}>{p.name || 'Unknown'}</p>
                                <p style={{ fontSize: '.75rem', color: 'var(--text-muted)', marginTop: '.2rem' }}>
                                    {p.date_of_birth || 'DOB —'}
                                </p>
                            </button>
                        ))}
                        {!patients.length && (
                            <p style={{ padding: '1.5rem', color: 'var(--text-muted)', fontSize: '.875rem' }}>
                                No patients yet.
                            </p>
                        )}
                    </div>

                    {/* Right panel */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                        {/* Alerts */}
                        {selected && <AlertsPanel scans={scans} />}

                        {/* Scans table */}
                        <div className="card" style={{ padding: '1.25rem' }}>
                            <h2 style={{ fontWeight: 600, marginBottom: '1rem' }}>
                                Scans {selected ? `— ${selected.name || selected.id}` : ''}
                            </h2>
                            {scans.length ? (
                                <div className="table-wrap">
                                    <table>
                                        <thead><tr>
                                            <th>File</th><th>Status</th><th>AI Confidence</th><th>Uploaded</th><th></th>
                                        </tr></thead>
                                        <tbody>
                                            {scans.map(s => (
                                                <tr key={s.id}>
                                                    <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                        {s.original_filename || s.id.slice(0, 8)}
                                                    </td>
                                                    <td><StatusBadge status={s.status} /></td>
                                                    <td style={{ minWidth: 140 }}>
                                                        {s.result ? <ConfidenceBar value={s.result.confidence_score} /> : '—'}
                                                    </td>
                                                    <td style={{ color: 'var(--text-muted)', fontSize: '.8rem' }}>
                                                        {new Date(s.upload_time).toLocaleDateString()}
                                                    </td>
                                                    <td>
                                                        {s.status === 'done' && (
                                                            <Link to={`/scans/${s.id}`} className="btn btn-ghost"
                                                                style={{ padding: '.35rem .85rem', fontSize: '.8rem' }}>
                                                                Review →
                                                            </Link>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : <p style={{ color: 'var(--text-muted)', fontSize: '.875rem' }}>No scans found for this patient.</p>}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
