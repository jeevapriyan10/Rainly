import React, { useState, useEffect } from 'react';
import { fetchAnalytics, fetchRegions, fetchDevices } from '../api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { useWebSocket } from '../hooks/useWebSocket';

const Dashboard = () => {
    const [analytics, setAnalytics] = useState(null);
    const [regions, setRegions] = useState([]);
    const [devices, setDevices] = useState([]);
    const [loading, setLoading] = useState(true);
    const { isConnected } = useWebSocket();

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 30000); // Reduced from 10s to 30s since WebSocket provides real-time updates
        return () => clearInterval(interval);
    }, []);

    const loadData = async () => {
        try {
            const [analyticsData, regionsData, devicesData] = await Promise.all([
                fetchAnalytics(),
                fetchRegions(),
                fetchDevices()
            ]);
            setAnalytics(analyticsData);
            setRegions(regionsData);
            setDevices(devicesData);
            setLoading(false);
        } catch (err) {
            console.error('Failed to load data:', err);
            setLoading(false);
        }
    };

    const containerStyle = {
        maxWidth: '1280px',
        margin: '0 auto',
        padding: '3rem 2rem'
    };

    const heroStyle = {
        textAlign: 'center',
        marginBottom: '3rem'
    };

    const titleStyle = {
        fontSize: '2.5rem',
        fontWeight: '700',
        color: '#111827',
        marginBottom: '1rem',
        letterSpacing: '-0.025em'
    };

    const subtitleStyle = {
        fontSize: '1.125rem',
        color: '#6b7280',
        marginBottom: '2rem',
        maxWidth: '600px',
        margin: '0 auto 2rem'
    };

    const statsGridStyle = {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1.5rem',
        marginBottom: '3rem'
    };

    const statCardStyle = {
        background: 'white',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        padding: '2rem',
        textAlign: 'center'
    };

    const statValueStyle = {
        fontSize: '2.5rem',
        fontWeight: '700',
        color: '#2563eb',
        marginBottom: '0.5rem'
    };

    const statLabelStyle = {
        fontSize: '0.9375rem',
        color: '#6b7280',
        fontWeight: 500
    };

    const sectionStyle = {
        background: 'white',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        padding: '2rem',
        marginBottom: '2rem'
    };

    const sectionTitleStyle = {
        fontSize: '1.25rem',
        fontWeight: '600',
        color: '#111827',
        marginBottom: '1.5rem'
    };

    if (loading) {
        return (
            <div style={containerStyle}>
                <div style={{ textAlign: 'center', padding: '4rem 0' }}>
                    <div style={{ fontSize: '1.125rem', color: '#6b7280' }}>Loading dashboard...</div>
                </div>
            </div>
        );
    }

    if (!analytics) {
        return (
            <div style={containerStyle}>
                <div style={{ textAlign: 'center', padding: '4rem 0' }}>
                    <div style={{ fontSize: '1.125rem', color: '#6b7280' }}>Failed to load data. Please check if backend is running.</div>
                </div>
            </div>
        );
    }

    // Calculate additional stats
    const riverGroups = {};
    const stateGroups = {};
    const riskGroups = { HIGH: 0, MEDIUM: 0, LOW: 0 };
    const lowBatteryDevices = devices.filter(d => d.battery_level && d.battery_level < 30);

    regions.forEach(region => {
        // Group by river
        if (!riverGroups[region.river_name]) {
            riverGroups[region.river_name] = { regions: 0, devices: 0 };
        }
        riverGroups[region.river_name].regions++;

        // Group by state
        if (region.state) {
            if (!stateGroups[region.state]) {
                stateGroups[region.state] = 0;
            }
            stateGroups[region.state]++;
        }

        // Group by risk level
        if (region.risk_level) {
            riskGroups[region.risk_level]++;
        }

        // Count devices per river
        const regionDevices = devices.filter(d => d.region_id === region.region_id);
        riverGroups[region.river_name].devices += regionDevices.length;
    });

    const chartData = analytics.recent_warnings?.slice(0, 10).reverse().map((w, i) => ({
        name: `Alert ${i + 1}`,
        water: w.water_level,
        rainfall: w.rainfall
    })) || [];

    const riskPieData = [
        { name: 'High Risk', value: riskGroups.HIGH, color: '#dc2626' },
        { name: 'Medium Risk', value: riskGroups.MEDIUM, color: '#d97706' },
        { name: 'Low Risk', value: riskGroups.LOW, color: '#16a34a' }
    ];

    return (
        <div style={containerStyle}>
            <div style={heroStyle}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h1 style={titleStyle}>Real-time Flood Monitoring</h1>
                    <div style={{
                        padding: '0.5rem 1rem',
                        borderRadius: '20px',
                        fontSize: '0.875rem',
                        fontWeight: '600',
                        background: isConnected ? '#dcfce7' : '#fee2e2',
                        color: isConnected ? '#166534' : '#991b1b'
                    }}>
                        {isConnected ? 'Live' : 'Offline'}
                    </div>
                </div>
                <p style={subtitleStyle}>
                    Monitoring {regions.length} regions across {Object.keys(riverGroups).length} major Indian rivers
                </p>
            </div>

            {/* Battery Warnings */}
            {lowBatteryDevices.length > 0 && (
                <div style={{
                    ...sectionStyle,
                    background: '#fef2f2',
                    border: '1px solid #fca5a5',
                    marginBottom: '2rem'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <span style={{ fontSize: '1.5rem' }}>⚠️</span>
                        <div>
                            <h3 style={{ margin: 0, color: '#dc2626', fontSize: '1.125rem', fontWeight: '600' }}>
                                Low Battery Alert
                            </h3>
                            <p style={{ margin: '0.5rem 0 0 0', color: '#991b1b' }}>
                                {lowBatteryDevices.length} device(s) need battery attention: {lowBatteryDevices.map(d => d.name).join(', ')}
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Main Stats */}
            <div style={statsGridStyle}>
                <div style={statCardStyle}>
                    <div style={statValueStyle}>{analytics.total_devices}</div>
                    <div style={statLabelStyle}>Total Devices</div>
                </div>

                <div style={statCardStyle}>
                    <div style={{ ...statValueStyle, color: '#16a34a' }}>{analytics.active_devices}</div>
                    <div style={statLabelStyle}>Active Devices</div>
                </div>

                <div style={statCardStyle}>
                    <div style={{ ...statValueStyle, color: '#dc2626' }}>{analytics.devices_in_warning}</div>
                    <div style={statLabelStyle}>In Warning</div>
                </div>

                <div style={statCardStyle}>
                    <div style={{ ...statValueStyle, color: '#2563eb' }}>{regions.length}</div>
                    <div style={statLabelStyle}>Regions</div>
                </div>

                <div style={statCardStyle}>
                    <div style={{ ...statValueStyle, color: '#7c3aed' }}>{Object.keys(riverGroups).length}</div>
                    <div style={statLabelStyle}>Rivers</div>
                </div>
            </div>

            {/* River Overview & Risk Distribution */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '2rem', marginBottom: '2rem' }}>
                {/* River Overview */}
                <div style={sectionStyle}>
                    <h2 style={sectionTitleStyle}>Rivers Overview</h2>
                    <div style={{ display: 'grid', gap: '1rem' }}>
                        {Object.entries(riverGroups).map(([river, data]) => (
                            <div key={river} style={{
                                padding: '1rem',
                                background: '#f9fafb',
                                borderRadius: '6px',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center'
                            }}>
                                <div>
                                    <div style={{ fontWeight: '600', color: '#111827' }}>{river}</div>
                                    <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                                        {data.regions} regions • {data.devices} devices
                                    </div>
                                </div>
                                <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#2563eb' }}>
                                    {data.devices}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Risk Distribution */}
                <div style={sectionStyle}>
                    <h2 style={sectionTitleStyle}>Risk Distribution</h2>
                    <ResponsiveContainer width="100%" height={200}>
                        <PieChart>
                            <Pie
                                data={riskPieData}
                                cx="50%"
                                cy="50%"
                                outerRadius={80}
                                dataKey="value"
                                label={({ name, value }) => `${name}: ${value}`}
                            >
                                {riskPieData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Chart and Warnings */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '2rem', marginBottom: '2rem' }}>
                {chartData.length > 0 && (
                    <div style={sectionStyle}>
                        <h2 style={sectionTitleStyle}>Water Level & Rainfall Trends</h2>
                        <ResponsiveContainer width="100%" height={250}>
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                <XAxis dataKey="name" stroke="#6b7280" style={{ fontSize: '0.75rem' }} />
                                <YAxis stroke="#6b7280" style={{ fontSize: '0.75rem' }} />
                                <Tooltip
                                    contentStyle={{
                                        background: 'white',
                                        border: '1px solid #e5e7eb',
                                        borderRadius: '6px',
                                        fontSize: '0.875rem'
                                    }}
                                />
                                <Line type="monotone" dataKey="water" stroke="#2563eb" strokeWidth={2} name="Water Level (m)" />
                                <Line type="monotone" dataKey="rainfall" stroke="#16a34a" strokeWidth={2} name="Rainfall (mm)" />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                )}

                {/* State Distribution */}
                <div style={sectionStyle}>
                    <h2 style={sectionTitleStyle}>States Covered ({Object.keys(stateGroups).length})</h2>
                    <div style={{ display: 'grid', gap: '0.75rem', maxHeight: '250px', overflowY: 'auto' }}>
                        {Object.entries(stateGroups).sort((a, b) => b[1] - a[1]).map(([state, count]) => (
                            <div key={state} style={{
                                padding: '0.75rem 1rem',
                                background: '#f9fafb',
                                borderRadius: '6px',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center'
                            }}>
                                <span style={{ fontWeight: '500', color: '#111827' }}>{state}</span>
                                <span style={{
                                    background: '#2563eb',
                                    color: 'white',
                                    padding: '0.25rem 0.75rem',
                                    borderRadius: '999px',
                                    fontSize: '0.875rem',
                                    fontWeight: '600'
                                }}>
                                    {count}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Recent Warnings */}
            <div style={sectionStyle}>
                <h2 style={sectionTitleStyle}>Recent Warnings</h2>
                {analytics.recent_warnings?.length > 0 ? (
                    <div style={{ overflowX: 'auto' }}>
                        <table>
                            <thead>
                                <tr>
                                    <th>River</th>
                                    <th>Device</th>
                                    <th>Risk Level</th>
                                    <th>Action</th>
                                    <th>Water Level</th>
                                    <th>Rainfall</th>
                                    <th>Time</th>
                                </tr>
                            </thead>
                            <tbody>
                                {analytics.recent_warnings.map((warning, idx) => (
                                    <tr key={idx}>
                                        <td style={{ fontWeight: 500 }}>{warning.river_name}</td>
                                        <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{warning.device_id}</td>
                                        <td>
                                            <span className={`badge badge-${warning.risk_level.toLowerCase()}`}>
                                                {warning.risk_level}
                                            </span>
                                        </td>
                                        <td style={{ textTransform: 'capitalize' }}>{warning.warning_type}</td>
                                        <td style={{ color: '#2563eb', fontWeight: 600 }}>{warning.water_level.toFixed(2)}m</td>
                                        <td style={{ color: '#16a34a', fontWeight: 600 }}>{warning.rainfall.toFixed(1)}mm</td>
                                        <td style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                                            {new Date(warning.timestamp).toLocaleString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p style={{ color: '#6b7280', textAlign: 'center', padding: '2rem' }}>No warnings recorded yet</p>
                )}
            </div>
        </div>
    );
};

export default Dashboard;
