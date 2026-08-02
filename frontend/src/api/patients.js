// src/api/patients.js
import client from './client'

export const listPatients = () => client.get('/patients')
export const getPatient = (id) => client.get(`/patients/${id}`)
export const createPatient = (data) => client.post('/patients', data)
