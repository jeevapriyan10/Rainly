import React, { useState, useEffect } from 'react';
import { simulatePayload, fetchDevices } from '../api';
import { useWebSocket } from '../hooks/useWebSocket';

const SimulatorTab = () => {
    const [devices, setDevices] = useState([]);
    const [activeSimulations, setActiveSimulations] = useState([]);
    const [selectedDevice, setSelectedDevice] = useState(null);
    const [formData, setFormData] = useState({
        sensor_id: '',
        region_id: '',
        water_level: 290.0,
        rainfall: 30,
        flow_rate: 1000
    });
    const [simConfig, setSimConfig] = useState({
        trend: 'rising',
        speed: 'medium'
    });
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const { isConnected, deviceUpdates } = useWebSocket();

    useEffect(() => {
        loadDevices();
        loadActiveSimulations();
        const interval = setInterval(loadActiveSimulations, 5000);
        return () => clearInterval(interval);
    }, []);

    // Update form when device updates come via WebSocket
    useEffect(() => {
        if (selectedDevice && deviceUpdates[selectedDevice.device_id]) {
            const update = deviceUpdates[selectedDevice.device_id];
            setFormData(prev => ({
                ...prev,
                water_level: update.water_level || prev.water_level,
                rainfall: update.rainfall || prev.rainfall,
                flow_rate: update.flow_rate || prev.flow_rate
            }));
        }
    }, [deviceUpdates, selectedDevice]);

    // Auto-select active device on load
    useEffect(() => {
        if (activeSimulations.length > 0 && !selectedDevice && devices.length > 0) {
            const activeId = activeSimulations[0];
            const device = devices.find(d => d.device_id === activeId);
            if (device) {
                setSelectedDevice(device);
                setFormData({
                    sensor_id: device.device_id,
                    region_id: device.region_id,
                    water_level: device.last_water_level || 290,
                    rainfall: device.last_rainfall || 30,
                    flow_rate: device.last_flow_rate || 1000
                });
            }
        }
    }, [activeSimulations, devices, selectedDevice]);


    const loadDevices = async () => {
        try {
            const data = await fetchDevices();
            setDevices(data);
        } catch (err) {
            console.error('Failed to load devices:', err);
        }
    };

    const loadActiveSimulations = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/simulation/active');
            const data = await response.json();
            setActiveSimulations(data.active_simulations || []);
        } catch (err) {
            console.error('Failed to load active simulations:', err);
        }
    };

    const startSimulation = async () => {
        if (!selectedDevice) return;

        setLoading(true);
        try {
            const response = await fetch(
                `http://localhost:8000/api/simulation/start?device_id=${selectedDevice.device_id}`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        initial_water_level: parseFloat(formData.water_level),
                        initial_rainfall: parseFloat(formData.rainfall),
                        initial_flow_rate: parseFloat(formData.flow_rate),
                        variation_speed: simConfig.speed,
                        trend: simConfig.trend
                    })
                }
            );
            const result = await response.json();
            console.log('Simulation started:', result);
            await loadActiveSimulations();
        } catch (err) {
            console.error('Failed to start simulation:', err);
        } finally {
            setLoading(false);
        }
    };

    const stopSimulation = async (deviceId) => {
        try {
            await fetch(`http://localhost:8000/api/simulation/stop/${deviceId}`, {
                method: 'POST'
            });
            await loadActiveSimulations();
        } catch (err) {
            console.error('Failed to stop simulation:', err);
        }
    };

    const adjustSimulation = async (deviceId, params) => {
        try {
            await fetch(`http://localhost:8000/api/simulation/adjust/${deviceId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            });
        } catch (err) {
            console.error('Failed to adjust simulation:', err);
        }
    };

    const handleManualSimulate = async (e) => {
        e.preventDefault();
        setLoading(true);
        setResult(null);

        try {
            const response = await simulatePayload({
                ...formData,
                water_level: parseFloat(formData.water_level),
                rainfall: parseFloat(formData.rainfall),
                flow_rate: parseFloat(formData.flow_rate)
            });
            setResult(response);
        } catch (err) {
            setResult({ error: err.message });
        } finally {
            setLoading(false);
        }
    };



    const statusBadgeStyle = {
        padding: '0.5rem 1rem',
        borderRadius: '20px',
        fontSize: '0.875rem',
        fontWeight: '600',
        background: isConnected ? '#dcfce7' : '#fee2e2',
        color: isConnected ? '#166534' : '#991b1b'
    };

    return (
        <div className="container-responsive">
            <div className="page-header">
                <h1 className="header-title">Real-Time Simulator</h1>
                <div style={statusBadgeStyle}>
                    {isConnected ? 'Live Connected' : 'Disconnected'}
                </div>
            </div>

            <div className="simulator-grid">
                {/* Real-Time Simulation Panel */}
                <div className="card">
                    <h2 className="card-title">Continuous Simulation</h2>
                    <p className="text-secondary" style={{ fontSize: '0.875rem', marginBottom: '1.5rem' }}>
                        Start automated real-time data streaming that updates ALL tabs live
                    </p>

                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                            Select Device
                        </label>
                        <select
                            value={selectedDevice?.device_id || ''}
                            onChange={e => {
                                const device = devices.find(d => d.device_id === e.target.value);
                                setSelectedDevice(device);
                                if (device) {
                                    setFormData({
                                        sensor_id: device.device_id,
                                        region_id: device.region_id,
                                        water_level: device.last_water_level || 290,
                                        rainfall: device.last_rainfall || 30,
                                        flow_rate: device.last_flow_rate || 1000
                                    });
                                }
                            }}
                            className="w-full"
                        >
                            <option value="">Choose a device...</option>
                            {devices.map(d => (
                                <option key={d.device_id} value={d.device_id}>
                                    {d.name} ({activeSimulations.includes(d.device_id) ? 'LIVE' : 'Idle'})
                                </option>
                            ))}
                        </select>
                    </div>

                    {selectedDevice && (
                        <>
                            <div className="grid-2">
                                <div>
                                    <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.875rem' }}>
                                        Trend
                                    </label>
                                    <select
                                        value={simConfig.trend}
                                        onChange={e => setSimConfig({ ...simConfig, trend: e.target.value })}
                                        className="w-full"
                                    >
                                        <option value="rising">Rising</option>
                                        <option value="falling">Falling</option>
                                        <option value="stable">Stable</option>
                                        <option value="random">Random</option>
                                    </select>
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.875rem' }}>
                                        Speed
                                    </label>
                                    <select
                                        value={simConfig.speed}
                                        onChange={e => setSimConfig({ ...simConfig, speed: e.target.value })}
                                        className="w-full"
                                    >
                                        <option value="slow">Slow</option>
                                        <option value="medium">Medium</option>
                                        <option value="fast">Fast</option>
                                    </select>
                                </div>
                            </div>

                            {activeSimulations.includes(selectedDevice.device_id) ? (
                                <>
                                    <div style={{
                                        background: '#dcfce7',
                                        border: '1px solid #86efac',
                                        borderRadius: '8px',
                                        padding: '1rem',
                                        marginBottom: '1rem'
                                    }}>
                                        <div style={{ fontWeight: '600', color: '#166534', marginBottom: '0.5rem' }}>
                                            LIVE SIMULATION RUNNING
                                        </div>
                                        {deviceUpdates[selectedDevice.device_id] && (
                                            <div style={{ fontSize: '0.875rem', color: '#166534' }}>
                                                <div>Water: {deviceUpdates[selectedDevice.device_id].water_level?.toFixed(2)}m</div>
                                                <div>Rain: {deviceUpdates[selectedDevice.device_id].rainfall?.toFixed(1)}mm</div>
                                                <div>Flow: {deviceUpdates[selectedDevice.device_id].flow_rate?.toFixed(0)} m³/s</div>
                                                <div style={{ marginTop: '0.5rem', fontWeight: '600' }}>
                                                    Risk: {deviceUpdates[selectedDevice.device_id].risk_level}
                                                </div>
                                                {/* LLM Status Indicator */}
                                                {deviceUpdates[selectedDevice.device_id]?.llm_status === 'processing' && (
                                                    <div style={{
                                                        marginTop: '0.75rem',
                                                        padding: '0.75rem',
                                                        background: '#eff6ff',
                                                        borderRadius: '6px',
                                                        borderLeft: '4px solid #3b82f6',
                                                        fontSize: '0.8rem',
                                                        color: '#1e40af',
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        gap: '0.75rem'
                                                    }}>
                                                        <div style={{
                                                            width: '16px',
                                                            height: '16px',
                                                            border: '2px solid #3b82f6',
                                                            borderTopColor: 'transparent',
                                                            borderRadius: '50%',
                                                            animation: 'spin 1s linear infinite'
                                                        }} />
                                                        <strong>AI is analyzing flood risk...</strong>
                                                        <style>{`
                                                            @keyframes spin {
                                                                to { transform: rotate(360deg); }
                                                            }
                                                        `}</style>
                                                    </div>
                                                )}

                                                {deviceUpdates[selectedDevice.device_id]?.llm_reasoning && (
                                                    <div style={{
                                                        marginTop: '0.75rem',
                                                        padding: '0.75rem',
                                                        background: '#ffffff',
                                                        borderRadius: '6px',
                                                        borderLeft: '4px solid #10b981',
                                                        fontSize: '0.8rem',
                                                        color: '#1e293b'
                                                    }}>
                                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                                            <strong>AI Analysis Report:</strong>
                                                            <span style={{ fontSize: '0.7rem', color: '#64748b' }}>
                                                                {deviceUpdates[selectedDevice.device_id]?.llm_status === 'completed' ? 'Just Now' : 'Cached'}
                                                            </span>
                                                        </div>
                                                        {deviceUpdates[selectedDevice.device_id].llm_reasoning}
                                                    </div>
                                                )}

                                            </div>
                                        )}
                                    </div>

                                    <div className="grid-form">
                                        <button
                                            className="btn btn-secondary w-full"
                                            onClick={() => adjustSimulation(selectedDevice.device_id, {
                                                trend: 'rising',
                                                water_level: (deviceUpdates[selectedDevice.device_id]?.water_level || 290) + 5
                                            })}
                                            style={{ fontSize: '0.875rem' }}
                                        >
                                            Increase Water +5m
                                        </button>
                                        <button
                                            className="btn btn-secondary w-full"
                                            onClick={() => adjustSimulation(selectedDevice.device_id, {
                                                trend: 'falling',
                                                water_level: Math.max(250, (deviceUpdates[selectedDevice.device_id]?.water_level || 290) - 5)
                                            })}
                                            style={{ fontSize: '0.875rem' }}
                                        >
                                            Decrease Water -5m
                                        </button>
                                        <button
                                            className="btn w-full"
                                            onClick={() => stopSimulation(selectedDevice.device_id)}
                                            style={{ background: '#dc2626', color: 'white', fontSize: '0.875rem' }}
                                        >
                                            Stop Simulation
                                        </button>
                                    </div>
                                </>
                            ) : (
                                <button
                                    className="btn btn-primary w-full"
                                    onClick={startSimulation}
                                    disabled={loading}
                                    style={{ fontSize: '1rem' }}
                                >
                                    {loading ? 'Starting...' : 'Start Live Simulation'}
                                </button>
                            )}
                        </>
                    )}
                </div>

                {/* Manual One-Time Simulation */}
                <div className="card">
                    <h2 className="card-title">Manual Simulation</h2>
                    <p className="text-secondary" style={{ fontSize: '0.875rem', marginBottom: '1.5rem' }}>
                        Test one-time scenarios without continuous streaming
                    </p>
                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                            Test Location (Region/Device)
                        </label>
                        <select
                            value={formData.sensor_id}
                            onChange={e => {
                                const device = devices.find(d => d.device_id === e.target.value);
                                if (device) {
                                    setFormData(prev => ({
                                        ...prev,
                                        sensor_id: device.device_id,
                                        region_id: device.region_id
                                    }));
                                }
                            }}
                            className="w-full"
                        >
                            <option value="">Select a location to test...</option>
                            {devices.map(d => (
                                <option key={d.device_id} value={d.device_id}>
                                    {d.name} ({d.region_id})
                                </option>
                            ))}
                        </select>
                    </div>

                    <form onSubmit={handleManualSimulate} style={{ display: 'grid', gap: '1rem' }}>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', fontSize: '0.875rem' }}>
                                Water Level (m)
                            </label>
                            <input
                                type="number"
                                step="0.1"
                                value={formData.water_level}
                                onChange={e => setFormData({ ...formData, water_level: e.target.value })}
                                required
                            />
                            <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.25rem' }}>
                                Normal: 280-290m • Medium: 290-300m • High: &gt;300m
                            </div>
                        </div>

                        <div>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', fontSize: '0.875rem' }}>
                                Rainfall (mm)
                            </label>
                            <input
                                type="number"
                                step="1"
                                value={formData.rainfall}
                                onChange={e => setFormData({ ...formData, rainfall: e.target.value })}
                                required
                            />
                            <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.25rem' }}>
                                Low: &lt;75mm • Medium: 75-150mm • High: &gt;150mm
                            </div>
                        </div>

                        <div>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', fontSize: '0.875rem' }}>
                                Flow Rate (m³/s)
                            </label>
                            <input
                                type="number"
                                step="1"
                                value={formData.flow_rate}
                                onChange={e => setFormData({ ...formData, flow_rate: e.target.value })}
                                required
                            />
                        </div>

                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={loading || !formData.sensor_id}
                            style={{ fontSize: '1rem' }}
                        >
                            {loading ? 'Analyzing...' : 'Test Scenario'}
                        </button>
                    </form>

                    {result && (
                        <div style={{
                            marginTop: '1rem',
                            padding: '1rem',
                            background: result.error ? '#fef2f2' : '#f0fdf4',
                            border: `1px solid ${result.error ? '#fca5a5' : '#86efac'}`,
                            borderRadius: '8px'
                        }}>
                            {result.error ? (
                                <div style={{ color: '#dc2626' }}>{result.error}</div>
                            ) : (
                                <div style={{ fontSize: '0.875rem' }}>
                                    <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>Test Complete</div>
                                    <div>Risk: {result.prediction.risk_level}</div>
                                    <div>Action: {result.prediction.warning_type}</div>
                                    <div>Warnings: {result.warnings_generated}</div>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Active Simulations Panel */}
                {activeSimulations.length > 0 && (
                    <div className="card">
                        <h2 className="card-title">
                            Active Simulations ({activeSimulations.length})
                        </h2>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
                            {activeSimulations.map(deviceId => {
                                const device = devices.find(d => d.device_id === deviceId);
                                const update = deviceUpdates[deviceId];
                                return (
                                    <div key={deviceId} style={{
                                        padding: '1rem',
                                        background: '#fef3c7',
                                        border: '2px solid #fbbf24',
                                        borderRadius: '8px'
                                    }}>
                                        <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>
                                            {device?.name || deviceId}
                                        </div>
                                        {update && (
                                            <div style={{ fontSize: '0.75rem', color: '#78350f' }}>
                                                <div>Water: {update.water_level?.toFixed(1)}m</div>
                                                <div>Rain: {update.rainfall?.toFixed(0)}mm</div>
                                                <div style={{ marginTop: '0.5rem', fontWeight: '600' }}>
                                                    {update.risk_level}
                                                </div>
                                            </div>
                                        )}
                                        <button
                                            onClick={() => stopSimulation(deviceId)}
                                            style={{
                                                marginTop: '0.5rem',
                                                width: '100%',
                                                padding: '0.375rem',
                                                fontSize: '0.75rem',
                                                background: '#dc2626',
                                                color: 'white',
                                                border: 'none',
                                                borderRadius: '4px',
                                                cursor: 'pointer'
                                            }}
                                        >
                                            Stop
                                        </button>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default SimulatorTab;
