const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export const fetchRegions = async () => {
    const response = await fetch(`${API_BASE}/regions`);
    return response.json();
};

export const createRegion = async (region) => {
    const response = await fetch(`${API_BASE}/regions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(region)
    });
    return response.json();
};

export const fetchDevices = async () => {
    const response = await fetch(`${API_BASE}/devices`);
    return response.json();
};

export const createDevice = async (device) => {
    const response = await fetch(`${API_BASE}/devices`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(device)
    });
    return response.json();
};

export const toggleDevice = async (deviceId) => {
    const response = await fetch(`${API_BASE}/devices/${deviceId}/toggle`, {
        method: 'PUT'
    });
    return response.json();
};

export const fetchParticipants = async () => {
    const response = await fetch(`${API_BASE}/participants`);
    return response.json();
};

export const createParticipant = async (participant) => {
    const response = await fetch(`${API_BASE}/participants`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(participant)
    });
    return response.json();
};

export const fetchWarnings = async () => {
    const response = await fetch(`${API_BASE}/warnings`);
    return response.json();
};

export const fetchParticipantWarnings = async (participantId) => {
    const response = await fetch(`${API_BASE}/warnings/participant/${participantId}`);
    return response.json();
};

export const simulatePayload = async (payload) => {
    const response = await fetch(`${API_BASE}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    return response.json();
};

export const fetchAnalytics = async () => {
    const response = await fetch(`${API_BASE}/analytics`);
    return response.json();
};
