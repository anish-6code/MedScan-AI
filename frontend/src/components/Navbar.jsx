// src/components/Navbar.jsx
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Navbar() {
    const { user, logout } = useAuth()
    const nav = useNavigate()

    const handleLogout = () => { logout(); nav('/login') }

    return (
        <nav style={{
            background: 'var(--bg-card)', borderBottom: '1px solid var(--border)',
            padding: '.85rem 0', position: 'sticky', top: 0, zIndex: 100,
            backdropFilter: 'blur(8px)',
        }}>
            <div className="container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '.6rem' }}>
                    <span style={{ fontSize: '1.4rem' }}>🧬</span>
                    <span style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--primary)' }}>MedScan AI</span>
                </Link>
                {user && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                        <Link to="/" style={{ fontSize: '.875rem', color: 'var(--text-muted)' }} className="nav-link">Patients</Link>
                        <span style={{ fontSize: '.875rem', color: 'var(--text-muted)' }}>
                            Dr. {user.full_name || user.email}
                        </span>
                        <button className="btn btn-ghost" style={{ padding: '.4rem .9rem', fontSize: '.8rem' }} onClick={handleLogout}>
                            Sign out
                        </button>
                    </div>
                )}
            </div>
        </nav>
    )
}
