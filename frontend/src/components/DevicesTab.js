import React, { useState, useEffect } from 'react';
import { fetchRegions, fetchDevices, createDevice, toggleDevice } from '../api';

const DevicesTab = () => {
    const [regions, setRegions] = useState([]);
    const [devices, setDevices] = useState([]);
    const [showForm, setShowForm] = useState(false);
    const [formData, setFormData] = useState({
        device_id: '',
        name: '',
        region_id: '',
        alert_threshold: 5.0,
        is_active: true
    });

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [regionsData, devicesData] = await Promise.all([
                fetchRegions(),
                fetchDevices()
            ]);
            setRegions(regionsData);
            setDevices(devicesData);
        } catch (err) {
            console.error('Failed to load data:', err);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await createDevice(formData);
            setShowForm(false);
            setFormData({
                device_id: '',
                name: '',
                region_id: '',
                alert_threshold: 5.0,
                is_active: true
            });
            loadData();
        } catch (err) {
            console.error('Failed to create device:', err);
        }
    };

    const handleToggle = async (deviceId) => {
        try {
            await toggleDevice(deviceId);
            loadData();
        } catch (err) {
            console.error('Failed to toggle device:', err);
        }
    };



    return (

        <div className="container-responsive">
            <div className="page-header">
                <h1 className="header-title">Rivers & Devices</h1>
                <button
                    className="btn btn-primary"
                    onClick={() => setShowForm(!showForm)}
                >
                    {showForm ? 'Cancel' : '+ Add Device'}
                </button>
            </div>

            {showForm && (
                <div className="card" style={{ marginBottom: '2rem' }}>
                    <h3 className="card-title">Add New Device</h3>
                    <form onSubmit={handleSubmit} className="grid-form">
                        <input
                            placeholder="Device ID (e.g., d007)"
                            value={formData.device_id}
                            onChange={e => setFormData({ ...formData, device_id: e.target.value })}
                            required
                        />
                        <input
                            placeholder="Device Name"
                            value={formData.name}
                            onChange={e => setFormData({ ...formData, name: e.target.value })}
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
                        <input
                            type="number"
                            step="0.1"
                            placeholder="Alert Threshold (meters)"
                            value={formData.alert_threshold}
                            onChange={e => setFormData({ ...formData, alert_threshold: parseFloat(e.target.value) })}
                            required
                        />
                        <button type="submit" className="btn btn-primary w-full">Create Device</button>
                    </form>
                </div>
            )}

            {regions.map(region => {
                const regionDevices = devices.filter(d => d.region_id === region.region_id);

                return (
                    <div key={region.region_id} className="card" style={{ marginBottom: '1.5rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                            <div>
                                <h3 className="card-title" style={{ marginBottom: '0.5rem' }}>
                                    {region.name} - {region.river_name}
                                </h3>
                                {(region.state || region.district) && (
                                    <p className="text-secondary" style={{ fontSize: '0.875rem' }}>
                                        {region.state} {region.district && `• ${region.district}`}
                                        {region.risk_level && (
                                            <span className={`badge badge-${region.risk_level.toLowerCase()}`} style={{ marginLeft: '0.5rem' }}>
                                                {region.risk_level} RISK
                                            </span>
                                        )}
                                    </p>
                                )}
                            </div>
                            <div className="text-muted" style={{ fontSize: '0.9375rem' }}>
                                {regionDevices.filter(d => d.is_active).length} / {regionDevices.length} active
                            </div>
                        </div>

                        {regionDevices.length === 0 ? (
                            <p className="text-muted" style={{ fontStyle: 'italic' }}>No devices in this region</p>
                        ) : (
                            <div>
                                {regionDevices.map(device => (
                                    <div key={device.device_id} className="device-item">
                                        <div>
                                            <div style={{ fontWeight: '600', fontSize: '1rem', marginBottom: '0.5rem' }}>
                                                {device.name}
                                            </div>
                                            <div style={{ fontSize: '0.875rem', color: '#6b7280', fontFamily: 'monospace', marginBottom: '0.5rem' }}>
                                                ID: {device.device_id}
                                            </div>
                                            <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', fontSize: '0.9375rem' }}>
                                                <div>
                                                    <span className="text-muted">Alert Threshold: </span>
                                                    <span style={{ color: '#2563eb', fontWeight: '500' }}>{device.alert_threshold}m</span>
                                                </div>
                                                {device.last_water_level && (
                                                    <div>
                                                        <span className="text-muted">Current Level: </span>
                                                        <span style={{ color: '#16a34a', fontWeight: '500' }}>{device.last_water_level.toFixed(2)}m</span>
                                                    </div>
                                                )}
                                                {device.battery_level !== null && device.battery_level !== undefined && (
                                                    <div>
                                                        <span className="text-muted">Battery: </span>
                                                        <span style={{
                                                            color: device.battery_level < 30 ? '#dc2626' : device.battery_level < 60 ? '#d97706' : '#16a34a',
                                                            fontWeight: '600'
                                                        }}>
                                                            🔋 {device.battery_level}%
                                                        </span>
                                                    </div>
                                                )}
                                            </div>
                                            {device.last_seen && (
                                                <div style={{ fontSize: '0.8125rem', color: '#9ca3af', marginTop: '0.5rem' }}>
                                                    Last Seen: {new Date(device.last_seen).toLocaleString()}
                                                </div>
                                            )}
                                        </div>

                                        <button
                                            onClick={() => handleToggle(device.device_id)}
                                            className={`${device.is_active ? 'btn btn-primary' : 'btn btn-secondary'} w-full`}
                                            style={{ minWidth: '100px' }}
                                        >
                                            {device.is_active ? 'Active' : 'Inactive'}
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
};

export default DevicesTab;
