// src/api/scans.js
import client from './client'

export const listScans = (patientId) => client.get(`/scans?patient_id=${patientId}`)
export const getScan = (id) => client.get(`/scans/${id}`)
export const uploadScan = (patientId, file) => {
    const fd = new FormData()
    fd.append('patient_id', patientId)
    fd.append('file', file)
    return client.post('/scans/upload', fd)
}
export const getResult = (scanId) => client.get(`/results/${scanId}`)
export const getCorrections = (scanId) => client.get(`/scans/${scanId}/corrections`)
export const saveCorrection = (scanId, data) => client.patch(`/scans/${scanId}/result`, data)
export const reportUrl = (scanId) => `/api/scans/${scanId}/report.pdf`
