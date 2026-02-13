import React, { useState, useEffect } from 'react';
import { fetchRegions, fetchDevices, createRegion } from '../api';

const RegionsTab = () => {
    const [regions, setRegions] = useState([]);
    const [devices, setDevices] = useState([]);
    const [showForm, setShowForm] = useState(false);
    const [selectedRiver, setSelectedRiver] = useState('all');
    const [formData, setFormData] = useState({
        region_id: '',
        name: '',
        latitude: '',
        longitude: '',
        river_name: '',
        state: '',
        district: '',
        risk_level: 'LOW'
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
            await createRegion({
                ...formData,
                latitude: parseFloat(formData.latitude),
                longitude: parseFloat(formData.longitude)
            });
            setShowForm(false);
            setFormData({
                region_id: '',
                name: '',
                latitude: '',
                longitude: '',
                river_name: '',
                state: '',
                district: '',
                risk_level: 'LOW'
            });
            loadData();
        } catch (err) {
            console.error('Failed to create region:', err);
        }
    };

    const containerStyle = {
        maxWidth: '1280px',
        margin: '0 auto',
        padding: '3rem 2rem'
    };

    const headerStyle = {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '2rem',
        flexWrap: 'wrap',
        gap: '1rem'
    };

    const titleStyle = {
        fontSize: '2rem',
        fontWeight: '700',
        color: '#111827',
        margin: 0
    };

    const formCardStyle = {
        background: 'white',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        padding: '2rem',
        marginBottom: '2rem'
    };

    const formTitleStyle = {
        fontSize: '1.25rem',
        fontWeight: '600',
        color: '#111827',
        marginTop: 0,
        marginBottom: '1.5rem'
    };

    const formGridStyle = {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '1rem'
    };

    const filterStyle = {
        display: 'flex',
        gap: '0.5rem',
        flexWrap: 'wrap',
        marginBottom: '2rem'
    };

    const filterButtonStyle = (isActive) => ({
        padding: '0.5rem 1rem',
        borderRadius: '6px',
        border: `1px solid ${isActive ? '#2563eb' : '#e5e7eb'}`,
        background: isActive ? '#2563eb' : 'white',
        color: isActive ? 'white' : '#6b7280',
        cursor: 'pointer',
        fontSize: '0.875rem',
        fontWeight: '500',
        transition: 'all 0.2s ease'
    });

    // Get unique rivers
    const rivers = ['all', ...new Set(regions.map(r => r.river_name))];

    // Filter regions
    const filteredRegions = selectedRiver === 'all'
        ? regions
        : regions.filter(r => r.river_name === selectedRiver);

    // Group by risk level
    const riskCounts = { HIGH: 0, MEDIUM: 0, LOW: 0 };
    filteredRegions.forEach(r => {
        if (r.risk_level) riskCounts[r.risk_level]++;
    });

    return (
        <div style={containerStyle}>
            <div style={headerStyle}>
                <div>
                    <h1 style={titleStyle}>Regions Management</h1>
                    <p style={{ color: '#6b7280', margin: '0.5rem 0 0 0' }}>
                        {filteredRegions.length} regions{selectedRiver !== 'all' ? ` on ${selectedRiver}` : ' across India'}
                    </p>
                </div>
                <button
                    className="btn btn-primary"
                    onClick={() => setShowForm(!showForm)}
                >
                    {showForm ? 'Cancel' : '+ Add Region'}
                </button>
            </div>

            {/* Add Region Form */}
            {showForm && (
                <div style={formCardStyle}>
                    <h3 style={formTitleStyle}>Add New Region</h3>
                    <form onSubmit={handleSubmit}>
                        <div style={formGridStyle}>
                            <input
                                placeholder="Region ID (e.g., r011)"
                                value={formData.region_id}
                                onChange={e => setFormData({ ...formData, region_id: e.target.value })}
                                required
                            />
                            <input
                                placeholder="Region Name"
                                value={formData.name}
                                onChange={e => setFormData({ ...formData, name: e.target.value })}
                                required
                            />
                            <input
                                placeholder="River Name"
                                value={formData.river_name}
                                onChange={e => setFormData({ ...formData, river_name: e.target.value })}
                                required
                            />
                            <input
                                placeholder="State"
                                value={formData.state}
                                onChange={e => setFormData({ ...formData, state: e.target.value })}
                                required
                            />
                            <input
                                placeholder="District"
                                value={formData.district}
                                onChange={e => setFormData({ ...formData, district: e.target.value })}
                                required
                            />
                            <input
                                type="number"
                                step="0.0001"
                                placeholder="Latitude"
                                value={formData.latitude}
                                onChange={e => setFormData({ ...formData, latitude: e.target.value })}
                                required
                            />
                            <input
                                type="number"
                                step="0.0001"
                                placeholder="Longitude"
                                value={formData.longitude}
                                onChange={e => setFormData({ ...formData, longitude: e.target.value })}
                                required
                            />
                            <select
                                value={formData.risk_level}
                                onChange={e => setFormData({ ...formData, risk_level: e.target.value })}
                                required
                            >
                                <option value="LOW">Low Risk</option>
                                <option value="MEDIUM">Medium Risk</option>
                                <option value="HIGH">High Risk</option>
                            </select>
                        </div>
                        <button type="submit" className="btn btn-primary" style={{ marginTop: '1rem' }}>
                            Create Region
                        </button>
                    </form>
                </div>
            )}

            {/* Risk Summary */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                gap: '1rem',
                marginBottom: '2rem'
            }}>
                <div style={{ padding: '1rem', background: '#fef2f2', borderRadius: '6px', border: '1px solid #fca5a5' }}>
                    <div style={{ fontSize: '2rem', fontWeight: '700', color: '#dc2626' }}>{riskCounts.HIGH}</div>
                    <div style={{ fontSize: '0.875rem', color: '#991b1b', fontWeight: '500' }}>High Risk</div>
                </div>
                <div style={{ padding: '1rem', background: '#fef3c7', borderRadius: '6px', border: '1px solid #fbbf24' }}>
                    <div style={{ fontSize: '2rem', fontWeight: '700', color: '#d97706' }}>{riskCounts.MEDIUM}</div>
                    <div style={{ fontSize: '0.875rem', color: '#92400e', fontWeight: '500' }}>Medium Risk</div>
                </div>
                <div style={{ padding: '1rem', background: '#f0fdf4', borderRadius: '6px', border: '1px solid #86efac' }}>
                    <div style={{ fontSize: '2rem', fontWeight: '700', color: '#16a34a' }}>{riskCounts.LOW}</div>
                    <div style={{ fontSize: '0.875rem', color: '#14532d', fontWeight: '500' }}>Low Risk</div>
                </div>
            </div>

            {/* River Filter */}
            <div style={filterStyle}>
                {rivers.map(river => (
                    <button
                        key={river}
                        style={filterButtonStyle(selectedRiver === river)}
                        onClick={() => setSelectedRiver(river)}
                    >
                        {river === 'all' ? 'All Rivers' : river}
                    </button>
                ))}
            </div>

            {/* Regions Grid */}
            <div style={{ display: 'grid', gap: '1.5rem' }}>
                {filteredRegions.map(region => {
                    const regionDevices = devices.filter(d => d.region_id === region.region_id);
                    const activeDevices = regionDevices.filter(d => d.is_active);

                    return (
                        <div key={region.region_id} style={{
                            background: 'white',
                            border: '1px solid #e5e7eb',
                            borderRadius: '8px',
                            padding: '2rem',
                            transition: 'box-shadow 0.2s ease'
                        }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '2rem', alignItems: 'start' }}>
                                <div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                                        <h3 style={{ margin: 0, fontSize: '1.5rem', fontWeight: '600', color: '#111827' }}>
                                            {region.name}
                                        </h3>
                                        <span className={`badge badge-${region.risk_level?.toLowerCase() || 'low'}`}>
                                            {region.risk_level || 'LOW'} RISK
                                        </span>
                                    </div>

                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
                                        <div>
                                            <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>River</div>
                                            <div style={{ fontWeight: '600', color: '#2563eb' }}>{region.river_name}</div>
                                        </div>
                                        <div>
                                            <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>State / District</div>
                                            <div style={{ fontWeight: '500', color: '#111827' }}>
                                                {region.state || 'N/A'} / {region.district || 'N/A'}
                                            </div>
                                        </div>
                                        <div>
                                            <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>Coordinates</div>
                                            <div style={{ fontFamily: 'monospace', fontSize: '0.875rem', color: '#111827' }}>
                                                {region.latitude.toFixed(4)}, {region.longitude.toFixed(4)}
                                            </div>
                                        </div>
                                        <div>
                                            <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>Devices</div>
                                            <div style={{ fontWeight: '600', color: '#16a34a' }}>
                                                {activeDevices.length} active / {regionDevices.length} total
                                            </div>
                                        </div>
                                    </div>

                                    {/* Devices List */}
                                    {regionDevices.length > 0 && (
                                        <div style={{ marginTop: '1.5rem' }}>
                                            <div style={{ fontSize: '0.875rem', fontWeight: '600', color: '#111827', marginBottom: '0.75rem' }}>
                                                Deployed Devices:
                                            </div>
                                            <div style={{ display: 'grid', gap: '0.5rem' }}>
                                                {regionDevices.map(device => (
                                                    <div key={device.device_id} style={{
                                                        padding: '0.75rem',
                                                        background: '#f9fafb',
                                                        borderRadius: '6px',
                                                        display: 'flex',
                                                        justifyContent: 'space-between',
                                                        alignItems: 'center'
                                                    }}>
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                                            <span style={{
                                                                width: '8px',
                                                                height: '8px',
                                                                borderRadius: '50%',
                                                                background: device.is_active ? '#16a34a' : '#dc2626'
                                                            }}></span>
                                                            <span style={{ fontWeight: '500', fontSize: '0.9375rem' }}>{device.name}</span>
                                                            <span style={{ fontSize: '0.8125rem', color: '#6b7280', fontFamily: 'monospace' }}>
                                                                {device.device_id}
                                                            </span>
                                                        </div>
                                                        {device.battery_level && (
                                                            <span style={{
                                                                fontSize: '0.875rem',
                                                                color: device.battery_level < 30 ? '#dc2626' : device.battery_level < 60 ? '#d97706' : '#16a34a',
                                                                fontWeight: '500'
                                                            }}>
                                                                🔋 {device.battery_level}%
                                                            </span>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default RegionsTab;
