// src/pages/ScanReview.jsx
// Doctor reviews AI results, edits corrections, downloads PDF report
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getScan, getResult, getCorrections, saveCorrection, reportUrl } from '../api/scans'

export default function ScanReview() {
    const { scanId } = useParams()
    const [scan, setScan] = useState(null)
    const [result, setResult] = useState(null)
    const [corrections, setCorrs] = useState([])
    const [notes, setNotes] = useState('')
    const [overrideConf, setOC] = useState('')
    const [saving, setSaving] = useState(false)
    const [saved, setSaved] = useState(false)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        Promise.all([
            getScan(scanId).then(r => setScan(r.data)),
            getResult(scanId).then(r => setResult(r.data)).catch(() => { }),
            getCorrections(scanId).then(r => setCorrs(r.data)).catch(() => { }),
        ]).finally(() => setLoading(false))
    }, [scanId])

    const handleSave = async () => {
        setSaving(true); setSaved(false)
        try {
            const payload = {
                doctor_notes: notes || null,
                override_confidence: overrideConf ? parseFloat(overrideConf) : null,
            }
            const r = await saveCorrection(scanId, payload)
            setCorrs(prev => [r.data, ...prev])
            setNotes(''); setOC(''); setSaved(true)
        } catch { alert('Failed to save correction.') }
        finally { setSaving(false) }
    }

    if (loading) return (
        <div className="page"><div className="container" style={{ textAlign: 'center', padding: '4rem' }}>
            <p className="pulse" style={{ color: 'var(--text-muted)' }}>Loading scan…</p>
        </div></div>
    )

    const conf = result?.confidence_score
    const severity = conf >= 0.7 ? 'HIGH' : conf >= 0.4 ? 'MODERATE' : 'LOW'
    const severityCls = conf >= 0.7 ? 'badge-danger' : conf >= 0.4 ? 'badge-warning' : 'badge-success'

    return (
        <div className="page">
            <div className="container">
                <div className="page-header">
                    <div>
                        <h1 className="page-title">Scan Review</h1>
                        <p className="page-subtitle" style={{ fontFamily: 'monospace' }}>{scanId}</p>
                    </div>
                    <div style={{ display: 'flex', gap: '.75rem' }}>
                        <a className="btn btn-ghost" href={reportUrl(scanId)} target="_blank" rel="noreferrer">
                            📄 Download PDF Report
                        </a>
                    </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '1.5rem', alignItems: 'start' }}>
                    {/* Left: overlay + findings */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                        {/* Overlay */}
                        {result?.overlay_path ? (
                            <div className="card" style={{ padding: '1.25rem' }}>
                                <h2 style={{ fontWeight: 600, marginBottom: '1rem' }}>AI Segmentation Overlay</h2>
                                <img
                                    src={`/api${result.overlay_path}`}
                                    alt="Scan overlay"
                                    style={{ width: '100%', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}
                                    onError={e => { e.target.style.display = 'none' }}
                                />
                                <p style={{ marginTop: '.5rem', fontSize: '.75rem', color: 'var(--text-muted)' }}>
                                    Red overlay = detected region(s) of interest
                                </p>
                            </div>
                        ) : (
                            <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
                                <p style={{ color: 'var(--text-muted)' }}>Overlay not available yet</p>
                            </div>
                        )}

                        {/* Scan info */}
                        <div className="card" style={{ padding: '1.25rem' }}>
                            <h2 style={{ fontWeight: 600, marginBottom: '1rem' }}>Scan Information</h2>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.75rem' }}>
                                {[
                                    ['Status', scan?.status],
                                    ['Filename', scan?.original_filename],
                                    ['Uploaded', scan?.upload_time ? new Date(scan.upload_time).toLocaleString() : '—'],
                                    ['Patient ID', scan?.patient_id?.slice(0, 8)],
                                ].map(([k, v]) => (
                                    <div key={k} style={{ background: 'var(--bg-surface)', padding: '.75rem', borderRadius: 'var(--radius-sm)' }}>
                                        <p style={{ fontSize: '.7rem', color: 'var(--text-muted)', marginBottom: '.2rem' }}>{k}</p>
                                        <p style={{ fontWeight: 500, fontSize: '.875rem' }}>{v || '—'}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Right: AI results + correction form */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                        {/* AI result */}
                        <div className="card" style={{ padding: '1.25rem' }}>
                            <h2 style={{ fontWeight: 600, marginBottom: '1rem' }}>AI Findings</h2>
                            {result ? (
                                <>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                                        <span className={`badge ${severityCls}`}>{severity}</span>
                                        <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>
                                            {(conf * 100).toFixed(1)}%
                                        </span>
                                    </div>
                                    <p style={{ fontSize: '.875rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                                        {result.findings_json?.summary || 'No summary available.'}
                                    </p>
                                    {result.findings_json?.num_regions > 0 && (
                                        <p style={{ marginTop: '.75rem', fontSize: '.8rem', color: 'var(--text-muted)' }}>
                                            {result.findings_json.num_regions} region(s) detected
                                        </p>
                                    )}
                                </>
                            ) : (
                                <p style={{ color: 'var(--text-muted)', fontSize: '.875rem' }}>
                                    No AI results yet. Scan may still be processing.
                                </p>
                            )}
                        </div>

                        {/* Correction form */}
                        <div className="card" style={{ padding: '1.25rem' }}>
                            <h2 style={{ fontWeight: 600, marginBottom: '1rem' }}>Doctor Correction</h2>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '.85rem' }}>
                                <div>
                                    <label>Clinical Notes</label>
                                    <textarea rows={4} value={notes} onChange={e => setNotes(e.target.value)}
                                        placeholder="Add your clinical observations or corrections…" />
                                </div>
                                <div>
                                    <label>Override Confidence (0–1)</label>
                                    <input type="number" step="0.01" min="0" max="1" value={overrideConf}
                                        onChange={e => setOC(e.target.value)} placeholder="e.g. 0.85" />
                                </div>
                                <button className="btn btn-primary" onClick={handleSave} disabled={saving}
                                    style={{ justifyContent: 'center' }}>
                                    {saving ? 'Saving…' : '💾 Save Correction'}
                                </button>
                                {saved && <p style={{ color: 'var(--success)', fontSize: '.8rem', textAlign: 'center' }}>
                                    ✓ Correction saved
                                </p>}
                            </div>
                        </div>

                        {/* Correction history */}
                        {corrections.length > 0 && (
                            <div className="card" style={{ padding: '1.25rem' }}>
                                <h2 style={{ fontWeight: 600, marginBottom: '.75rem' }}>Correction History</h2>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '.5rem' }}>
                                    {corrections.map(c => (
                                        <div key={c.id} style={{
                                            padding: '.75rem', background: 'var(--bg-surface)',
                                            borderRadius: 'var(--radius-sm)', fontSize: '.8rem'
                                        }}>
                                            {c.doctor_notes && <p style={{ marginBottom: '.3rem' }}>{c.doctor_notes}</p>}
                                            {c.override_confidence != null && (
                                                <p style={{ color: 'var(--text-muted)' }}>
                                                    Override: {(c.override_confidence * 100).toFixed(0)}%
                                                </p>
                                            )}
                                            <p style={{ color: 'var(--text-muted)', marginTop: '.3rem' }}>
                                                {new Date(c.created_at).toLocaleString()}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
