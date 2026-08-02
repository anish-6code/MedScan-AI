// src/pages/Login.jsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login as apiLogin } from '../api/auth'
import { useAuth } from '../contexts/AuthContext'

export default function Login() {
    const [email, setEmail] = useState('')
    const [password, setPass] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const { login } = useAuth()
    const nav = useNavigate()

    const submit = async (e) => {
        e.preventDefault()
        setLoading(true); setError('')
        try {
            const { data } = await apiLogin(email, password)
            login(data.access_token, { email })
            nav('/')
        } catch {
            setError('Invalid credentials. Please try again.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div style={{
            minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'radial-gradient(ellipse at 50% 0%, rgba(14,165,233,.15) 0%, var(--bg-base) 60%)',
        }}>
            <div className="card fade-up" style={{ width: '100%', maxWidth: 400, padding: '2.5rem' }}>
                {/* Logo */}
                <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                    <span style={{ fontSize: '2.5rem' }}>🧬</span>
                    <h1 style={{ fontSize: '1.4rem', fontWeight: 700, marginTop: '.5rem', color: 'var(--primary)' }}>
                        MedScan AI
                    </h1>
                    <p style={{ color: 'var(--text-muted)', fontSize: '.85rem', marginTop: '.3rem' }}>
                        Doctor Portal
                    </p>
                </div>

                <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    <div>
                        <label>Email</label>
                        <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                            placeholder="doctor@hospital.com" required autoFocus />
                    </div>
                    <div>
                        <label>Password</label>
                        <input type="password" value={password} onChange={e => setPass(e.target.value)}
                            placeholder="••••••••" required />
                    </div>
                    {error && (
                        <p style={{
                            color: 'var(--danger)', fontSize: '.85rem', padding: '.6rem .75rem',
                            background: 'rgba(239,68,68,.1)', borderRadius: 'var(--radius-sm)'
                        }}>{error}</p>
                    )}
                    <button className="btn btn-primary" type="submit" disabled={loading}
                        style={{ justifyContent: 'center', marginTop: '.5rem', padding: '.75rem' }}>
                        {loading ? 'Signing in…' : 'Sign In'}
                    </button>
                </form>

                <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '.75rem', color: 'var(--text-muted)' }}>
                    MedScan AI Platform — Authorised Access Only
                </p>
            </div>
        </div>
    )
}
