// src/api/auth.js
import client from './client'

export const login = (email, password) =>
    client.post('/auth/login', new URLSearchParams({ username: email, password }), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })

export const getMe = () => client.get('/auth/me')
