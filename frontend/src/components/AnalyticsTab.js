import React, { useState, useEffect } from 'react';
import { fetchAnalytics, fetchDevices, fetchWarnings, fetchRegions } from '../api';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const AnalyticsTab = () => {
    const [analytics, setAnalytics] = useState(null);
    const [devices, setDevices] = useState([]);
    const [warnings, setWarnings] = useState([]);
    const [regions, setRegions] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [analyticsData, devicesData, warningsData, regionsData] = await Promise.all([
                fetchAnalytics(),
                fetchDevices(),
                fetchWarnings(),
                fetchRegions()
            ]);
            setAnalytics(analyticsData);
            setDevices(devicesData);
            setWarnings(warningsData);
            setRegions(regionsData);
            setLoading(false);
        } catch (err) {
            console.error('Failed to load analytics:', err);
            setLoading(false);
        }
    };

    const containerStyle = {
        maxWidth: '1280px',
        margin: '0 auto',
        padding: '3rem 2rem'
    };

    const titleStyle = {
        fontSize: '2rem',
        fontWeight: '700',
        color: '#111827',
        marginBottom: '0.5rem'
    };

    const subtitleStyle = {
        color: '#6b7280',
        marginBottom: '3rem'
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
                    <div style={{ fontSize: '1.125rem', color: '#6b7280' }}>Loading analytics...</div>
                </div>
            </div>
        );
    }

    // River-wise device distribution
    const riverDeviceData = {};
    regions.forEach(region => {
        const regionDevices = devices.filter(d => d.region_id === region.region_id);
        if (!riverDeviceData[region.river_name]) {
            riverDeviceData[region.river_name] = { active: 0, inactive: 0, total: 0 };
        }
        riverDeviceData[region.river_name].total += regionDevices.length;
        riverDeviceData[region.river_name].active += regionDevices.filter(d => d.is_active).length;
        riverDeviceData[region.river_name].inactive += regionDevices.filter(d => !d.is_active).length;
    });

    const riverChartData = Object.entries(riverDeviceData).map(([river, data]) => ({
        river: river.length > 10 ? river.substring(0, 10) + '...' : river,
        fullName: river,
        Active: data.active,
        Inactive: data.inactive
    }));

    // Risk level distribution by river
    const riverRiskData = {};
    regions.forEach(region => {
        if (!riverRiskData[region.river_name]) {
            riverRiskData[region.river_name] = { HIGH: 0, MEDIUM: 0, LOW: 0 };
        }
        const riskLevel = region.risk_level || 'LOW';
        riverRiskData[region.river_name][riskLevel]++;
    });

    const riverRiskChartData = Object.entries(riverRiskData).map(([river, data]) => ({
        river: river.length > 10 ? river.substring(0, 10) + '...' : river,
        High: data.HIGH,
        Medium: data.MEDIUM,
        Low: data.LOW
    }));

    // Battery health distribution
    const batteryData = {
        healthy: devices.filter(d => d.battery_level && d.battery_level >= 70).length,
        good: devices.filter(d => d.battery_level && d.battery_level >= 40 && d.battery_level < 70).length,
        low: devices.filter(d => d.battery_level && d.battery_level < 40).length,
        unknown: devices.filter(d => !d.battery_level).length
    };

    const batteryChartData = [
        { status: 'Healthy (≥70%)', count: batteryData.healthy, color: '#16a34a' },
        { status: 'Good (40-69%)', count: batteryData.good, color: '#d97706' },
        { status: 'Low (<40%)', count: batteryData.low, color: '#dc2626' },
        { status: 'Unknown', count: batteryData.unknown, color: '#9ca3af' }
    ];

    // Warning type distribution
    const warningTypes = {};
    warnings.forEach(w => {
        const type = w.warning_type || 'unknown';
        warningTypes[type] = (warningTypes[type] || 0) + 1;
    });

    const warningTypeData = Object.entries(warningTypes).map(([type, count]) => ({
        type: type.charAt(0).toUpperCase() + type.slice(1),
        count
    }));

    // Recent trend data
    const trendData = analytics?.recent_warnings?.slice(0, 15).reverse().map((w, i) => ({
        index: i + 1,
        water: w.water_level,
        rainfall: w.rainfall,
        flow: w.flow_rate
    })) || [];

    return (
        <div style={containerStyle}>
            <h1 style={titleStyle}>Analytics & Insights</h1>
            <p style={subtitleStyle}>
                Comprehensive analysis of flood monitoring system across {regions.length} regions
            </p>

            {/* Key Metrics */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '1.5rem',
                marginBottom: '2rem'
            }}>
                <div style={{ ...sectionStyle, textAlign: 'center' }}>
                    <div style={{ fontSize: '2.5rem', fontWeight: '700', color: '#2563eb' }}>
                        {devices.length}
                    </div>
                    <div style={{ color: '#6b7280', fontWeight: '500' }}>Total Devices</div>
                </div>
                <div style={{ ...sectionStyle, textAlign: 'center' }}>
                    <div style={{ fontSize: '2.5rem', fontWeight: '700', color: '#16a34a' }}>
                        {devices.filter(d => d.is_active).length}
                    </div>
                    <div style={{ color: '#6b7280', fontWeight: '500' }}>Active Devices</div>
                </div>
                <div style={{ ...sectionStyle, textAlign: 'center' }}>
                    <div style={{ fontSize: '2.5rem', fontWeight: '700', color: '#d97706' }}>
                        {warnings.length}
                    </div>
                    <div style={{ color: '#6b7280', fontWeight: '500' }}>Total Warnings</div>
                </div>
                <div style={{ ...sectionStyle, textAlign: 'center' }}>
                    <div style={{ fontSize: '2.5rem', fontWeight: '700', color: '#7c3aed' }}>
                        {Object.keys(riverDeviceData).length}
                    </div>
                    <div style={{ color: '#6b7280', fontWeight: '500' }}>Rivers Monitored</div>
                </div>
            </div>

            {/* River-wise Device Distribution */}
            <div style={sectionStyle}>
                <h2 style={sectionTitleStyle}>Device Distribution by River</h2>
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={riverChartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis dataKey="river" stroke="#6b7280" style={{ fontSize: '0.875rem' }} />
                        <YAxis stroke="#6b7280" style={{ fontSize: '0.875rem' }} />
                        <Tooltip
                            contentStyle={{
                                background: 'white',
                                border: '1px solid #e5e7eb',
                                borderRadius: '6px'
                            }}
                            formatter={(value, name, props) => [value, name, props.payload.fullName]}
                        />
                        <Legend />
                        <Bar dataKey="Active" fill="#16a34a" />
                        <Bar dataKey="Inactive" fill="#dc2626" />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Risk Distribution by River */}
            <div style={sectionStyle}>
                <h2 style={sectionTitleStyle}>Risk Level Distribution by River</h2>
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={riverRiskChartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis dataKey="river" stroke="#6b7280" style={{ fontSize: '0.875rem' }} />
                        <YAxis stroke="#6b7280" style={{ fontSize: '0.875rem' }} />
                        <Tooltip
                            contentStyle={{
                                background: 'white',
                                border: '1px solid #e5e7eb',
                                borderRadius: '6px'
                            }}
                        />
                        <Legend />
                        <Bar dataKey="High" fill="#dc2626" stackId="a" />
                        <Bar dataKey="Medium" fill="#d97706" stackId="a" />
                        <Bar dataKey="Low" fill="#16a34a" stackId="a" />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Battery Health & Warning Types */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '2rem', marginBottom: '2rem' }}>
                {/* Battery Health */}
                <div style={sectionStyle}>
                    <h2 style={sectionTitleStyle}>Battery Health Status</h2>
                    <div style={{ display: 'grid', gap: '1rem' }}>
                        {batteryChartData.map((item, idx) => (
                            <div key={idx} style={{
                                display: 'flex',
                                alignItems: 'center',
                                padding: '1rem',
                                background: '#f9fafb',
                                borderRadius: '6px'
                            }}>
                                <div style={{
                                    width: '12px',
                                    height: '12px',
                                    borderRadius: '50%',
                                    background: item.color,
                                    marginRight: '1rem'
                                }}></div>
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontWeight: '500', color: '#111827' }}>{item.status}</div>
                                    <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>{item.count} devices</div>
                                </div>
                                <div style={{ fontSize: '1.5rem', fontWeight: '700', color: item.color }}>
                                    {item.count}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Warning Types */}
                <div style={sectionStyle}>
                    <h2 style={sectionTitleStyle}>Warning Type Distribution</h2>
                    <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={warningTypeData} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                            <XAxis type="number" stroke="#6b7280" style={{ fontSize: '0.875rem' }} />
                            <YAxis dataKey="type" type="category" stroke="#6b7280" style={{ fontSize: '0.875rem' }} />
                            <Tooltip
                                contentStyle={{
                                    background: 'white',
                                    border: '1px solid #e5e7eb',
                                    borderRadius: '6px'
                                }}
                            />
                            <Bar dataKey="count" fill="#2563eb" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Trends */}
            {trendData.length > 0 && (
                <div style={sectionStyle}>
                    <h2 style={sectionTitleStyle}>Recent Warning Trends</h2>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={trendData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                            <XAxis dataKey="index" stroke="#6b7280" style={{ fontSize: '0.875rem' }} label={{ value: 'Recent Warnings', position: 'insideBottom', offset: -5 }} />
                            <YAxis stroke="#6b7280" style={{ fontSize: '0.875rem' }} />
                            <Tooltip
                                contentStyle={{
                                    background: 'white',
                                    border: '1px solid #e5e7eb',
                                    borderRadius: '6px'
                                }}
                            />
                            <Legend />
                            <Line type="monotone" dataKey="water" stroke="#2563eb" strokeWidth={2} name="Water Level (m)" />
                            <Line type="monotone" dataKey="rainfall" stroke="#16a34a" strokeWidth={2} name="Rainfall (mm)" />
                            <Line type="monotone" dataKey="flow" stroke="#d97706" strokeWidth={2} name="Flow Rate (m³/s)" />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Summary Stats */}
            <div style={sectionStyle}>
                <h2 style={sectionTitleStyle}>System Health Summary</h2>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem' }}>
                    <div>
                        <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>Active Device Rate</div>
                        <div style={{ fontSize: '2rem', fontWeight: '700', color: '#16a34a' }}>
                            {((devices.filter(d => d.is_active).length / devices.length) * 100).toFixed(1)}%
                        </div>
                    </div>
                    <div>
                        <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>Healthy Battery Rate</div>
                        <div style={{ fontSize: '2rem', fontWeight: '700', color: '#16a34a' }}>
                            {devices.filter(d => d.battery_level).length > 0
                                ? ((batteryData.healthy / devices.filter(d => d.battery_level).length) * 100).toFixed(1)
                                : '0.0'}%
                        </div>
                    </div>
                    <div>
                        <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>High Risk Regions</div>
                        <div style={{ fontSize: '2rem', fontWeight: '700', color: '#dc2626' }}>
                            {regions.filter(r => r.risk_level === 'HIGH').length}
                        </div>
                    </div>
                    <div>
                        <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>Avg Devices per Region</div>
                        <div style={{ fontSize: '2rem', fontWeight: '700', color: '#2563eb' }}>
                            {(devices.length / regions.length).toFixed(1)}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AnalyticsTab;
