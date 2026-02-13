import React, { useState, useEffect } from 'react';
import { fetchRegions, fetchParticipants, fetchWarnings, createParticipant } from '../api';

const ParticipantsTab = () => {
    const [regions, setRegions] = useState([]);
    const [participants, setParticipants] = useState([]);
    const [warnings, setWarnings] = useState([]);
    const [showForm, setShowForm] = useState(false);
    const [selectedParticipant, setSelectedParticipant] = useState(null);
    const [formData, setFormData] = useState({
        name: '',
        age: '',
        phone: '',
        email: '',
        region_id: ''
    });

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const results = await Promise.allSettled([
                fetchRegions(),
                fetchParticipants(),
                fetchWarnings()
            ]);

            // Regions
            if (results[0].status === 'fulfilled') {
                setRegions(results[0].value);
            } else {
                console.error('Regions fetch failed:', results[0].reason);
            }

            // Participants
            if (results[1].status === 'fulfilled') {
                setParticipants(results[1].value);
            } else {
                console.error('Participants fetch failed:', results[1].reason);
                // Temporarily set empty if failed, won't break app
                setParticipants([]);
            }

            // Warnings
            if (results[2].status === 'fulfilled') {
                setWarnings(results[2].value);
            } else {
                console.error('Warnings fetch failed:', results[2].reason);
                setWarnings([]);
            }
        } catch (err) {
            console.error('Failed to load data:', err);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await createParticipant({
                ...formData,
                age: parseInt(formData.age)
            });
            setShowForm(false);
            setFormData({ name: '', age: '', phone: '', email: '', region_id: '' });
            loadData();
        } catch (err) {
            console.error('Failed to create participant:', err);
        }
    };

    const exportCSV = (data, filename) => {
        const csv = data.map(row => Object.values(row).join(',')).join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
    };

    const participantWarnings = selectedParticipant
        ? warnings.filter(w => w.participant_id === selectedParticipant.participant_id)
        : [];

    return (
        <div className="container-responsive">
            <div className="page-header">
                <h1 className="header-title">Participants</h1>
                <div className="button-group">
                    <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
                        {showForm ? 'Cancel' : '+ Register'}
                    </button>
                    <button className="btn btn-secondary" onClick={() => exportCSV(participants, 'participants.csv')}>
                        Export People
                    </button>
                    <button className="btn btn-secondary" onClick={() => exportCSV(warnings, 'warnings.csv')}>
                        Export Warnings
                    </button>
                </div>
            </div>

            {showForm && (
                <div className="card">
                    <h3 className="card-title">Register New Participant</h3>
                    <form onSubmit={handleSubmit} className="grid-form">
                        <input
                            placeholder="Full Name"
                            value={formData.name}
                            onChange={e => setFormData({ ...formData, name: e.target.value })}
                            required
                        />
                        <input
                            type="number"
                            placeholder="Age"
                            value={formData.age}
                            onChange={e => setFormData({ ...formData, age: e.target.value })}
                            required
                        />
                        <input
                            placeholder="Phone Number (e.g., +911234567890)"
                            value={formData.phone}
                            onChange={e => setFormData({ ...formData, phone: e.target.value })}
                            required
                        />
                        <input
                            type="email"
                            placeholder="Email Address (e.g., user@example.com)"
                            value={formData.email}
                            onChange={e => setFormData({ ...formData, email: e.target.value })}
                            required
                        />
                        <select
                            value={formData.region_id}
                            onChange={e => setFormData({ ...formData, region_id: e.target.value })}
                            required
                        >
                            <option value="">Select Region</option>
                            {regions.map(r => (
                                <option key={r.region_id} value={r.region_id}>
                                    {r.name} - {r.river_name}
                                </option>
                            ))}
                        </select>
                        <button type="submit" className="btn btn-primary w-full">Register Participant</button>
                    </form>
                </div>
            )}

            <div className="card">
                <h3 className="card-title">Registered Participants ({participants.length})</h3>
                <div className="grid-form">
                    {participants.map(participant => {
                        const region = regions.find(r => r.region_id === participant.region_id);
                        const participantWarningCount = warnings.filter(w => w.participant_id === participant.participant_id).length;
                        const isSelected = selectedParticipant?.participant_id === participant.participant_id;

                        return (
                            <div
                                key={participant.participant_id}
                                style={{
                                    padding: '1rem',
                                    background: isSelected ? '#eff6ff' : '#f9fafb',
                                    border: `1px solid ${isSelected ? '#2563eb' : '#e5e7eb'}`,
                                    borderRadius: '6px',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s ease'
                                }}
                                onClick={() => setSelectedParticipant(isSelected ? null : participant)}
                            >
                                <div style={{ fontWeight: '600', fontSize: '1rem', marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap' }}>
                                    <span>{participant.name}</span>
                                    <span style={{ fontSize: '0.875rem', fontWeight: 400, color: '#6b7280' }}>Age: {participant.age}</span>
                                </div>
                                <div style={{ fontSize: '0.9375rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                                    📱 {participant.phone}
                                </div>
                                <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                                    📧 {participant.email}
                                </div>
                                <div style={{ fontSize: '0.9375rem', color: '#2563eb', marginBottom: '0.25rem' }}>
                                    📍 {region?.name || 'Unknown'} - {region?.river_name || 'Unknown'}
                                </div>
                                <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                                    Warnings Received: <span style={{ color: participantWarningCount > 0 ? '#d97706' : '#16a34a', fontWeight: '500' }}>
                                        {participantWarningCount}
                                    </span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {selectedParticipant && (
                <div className="card">
                    <h3 className="card-title">
                        Warning History: {selectedParticipant.name}
                    </h3>
                    {participantWarnings.length === 0 ? (
                        <p style={{ color: '#6b7280', textAlign: 'center', padding: '2rem', fontStyle: 'italic' }}>
                            No warnings sent to this participant
                        </p>
                    ) : (
                        <div className="table-responsive">
                            <table>
                                <thead>
                                    <tr>
                                        <th>River</th>
                                        <th>Device</th>
                                        <th>Action</th>
                                        <th>Risk</th>
                                        <th>Time</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {participantWarnings.map((warning, idx) => (
                                        <tr key={idx}>
                                            <td style={{ fontWeight: 500 }}>{warning.river_name}</td>
                                            <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{warning.device_id}</td>
                                            <td style={{ textTransform: 'capitalize' }}>{warning.warning_type}</td>
                                            <td>
                                                <span className={`badge badge-${warning.risk_level.toLowerCase()}`}>
                                                    {warning.risk_level}
                                                </span>
                                            </td>
                                            <td style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                                                {new Date(warning.timestamp).toLocaleString()}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default ParticipantsTab;
