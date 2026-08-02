// src/contexts/AuthContext.jsx
import { createContext, useContext, useState, useEffect } from 'react'
import { getMe } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const token = localStorage.getItem('medscan_token')
        if (token) {
            getMe()
                .then((r) => setUser(r.data))
                .catch(() => localStorage.removeItem('medscan_token'))
                .finally(() => setLoading(false))
        } else {
            setLoading(false)
        }
    }, [])

    const login = (token, userData) => {
        localStorage.setItem('medscan_token', token)
        setUser(userData)
    }

    const logout = () => {
        localStorage.removeItem('medscan_token')
        setUser(null)
    }

    return (
        <AuthContext.Provider value={{ user, login, logout, loading }}>
            {!loading && children}
        </AuthContext.Provider>
    )
}

export const useAuth = () => useContext(AuthContext)
