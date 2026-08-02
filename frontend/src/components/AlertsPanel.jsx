// src/components/AlertsPanel.jsx
// Shows high-confidence findings as actionable alerts

export default function AlertsPanel({ scans = [] }) {
    const alerts = scans
        .filter(s => s.result?.confidence_score >= 0.4)
        .map(s => ({
            scanId: s.id,
            confidence: s.result.confidence_score,
            summary: s.result.findings_json?.summary || 'Finding detected',
            severity: s.result.confidence_score >= 0.7 ? 'high' : 'moderate',
        }))

    if (!alerts.length) return (
        <div className="card" style={{ padding: '1.5rem', textAlign: 'center' }}>
            <p style={{ color: 'var(--text-muted)', fontSize: '.875rem' }}>✅ No active alerts</p>
        </div>
    )

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '.75rem' }}>
            {alerts.map((a, i) => (
                <div key={i} className="card fade-up" style={{
                    padding: '1rem 1.25rem',
                    borderLeft: `3px solid ${a.severity === 'high' ? 'var(--danger)' : 'var(--warning)'}`,
                }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                            <span className={`badge ${a.severity === 'high' ? 'badge-danger' : 'badge-warning'}`}>
                                {a.severity === 'high' ? '⚠ HIGH' : '⚡ MODERATE'}
                            </span>
                            <p style={{ marginTop: '.5rem', fontSize: '.875rem', lineHeight: 1.5 }}>{a.summary}</p>
                        </div>
                        <span style={{ fontSize: '.75rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', marginLeft: '1rem' }}>
                            {(a.confidence * 100).toFixed(0)}% conf.
                        </span>
                    </div>
                </div>
            ))}
        </div>
    )
}
