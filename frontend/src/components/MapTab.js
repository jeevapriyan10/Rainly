import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import { fetchRegions, fetchDevices } from '../api';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Custom colored markers for risk levels
const createCustomIcon = (color) => {
    return L.divIcon({
        className: 'custom-marker',
        html: `<div style="
            background-color: ${color};
            width: 24px;
            height: 24px;
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        "></div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });
};

const riskColors = {
    LOW: '#10b981',      // Green
    MEDIUM: '#f59e0b',   // Orange
    HIGH: '#ef4444',     // Red
    CRITICAL: '#dc2626'  // Dark Red
};

const MapTab = () => {
    const [regions, setRegions] = useState([]);
    const [devices, setDevices] = useState([]);
    const [mapStyle, setMapStyle] = useState('satellite');

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 30000); // Refresh every 30s
        return () => clearInterval(interval);
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
            console.error('Failed to load map data:', err);
        }
    };

    // Map tile configurations
    const mapTiles = {
        satellite: {
            url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attribution: 'Tiles &copy; Esri'
        },
        terrain: {
            url: "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
            attribution: 'Map data: &copy; OpenTopoMap'
        },
        street: {
            url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attribution: '&copy; OpenStreetMap'
        }
    };

    const getRiskLevel = (device) => {
        if (!device.last_water_level) return 'LOW';
        const ratio = device.last_water_level / device.alert_threshold;

        if (ratio >= 1.2) return 'CRITICAL';
        if (ratio >= 1.0) return 'HIGH';
        if (ratio >= 0.8) return 'MEDIUM';
        return 'LOW';
    };

    const containerStyle = {
        maxWidth: '100%',
        margin: '0',
        padding: '2rem'
    };

    const titleStyle = {
        fontSize: '2rem',
        fontWeight: '700',
        color: '#111827',
        marginBottom: '1rem'
    };

    const mapContainerStyle = {
        height: '700px',
        borderRadius: '12px',
        border: '2px solid #e5e7eb',
        overflow: 'hidden',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
    };

    const controlPanelStyle = {
        marginBottom: '1.5rem',
        display: 'flex',
        gap: '1rem',
        flexWrap: 'wrap',
        alignItems: 'center'
    };

    const buttonStyle = (active) => ({
        padding: '0.625rem 1.25rem',
        fontSize: '0.875rem',
        fontWeight: '500',
        borderRadius: '6px',
        border: active ? '2px solid #2563eb' : '1px solid #d1d5db',
        background: active ? '#eff6ff' : 'white',
        color: active ? '#2563eb' : '#374151',
        cursor: 'pointer',
        transition: 'all 0.2s'
    });

    const legendStyle = {
        background: 'white',
        padding: '1rem',
        borderRadius: '8px',
        border: '1px solid #e5e7eb',
        display: 'flex',
        gap: '1.5rem',
        flexWrap: 'wrap'
    };

    const legendItemStyle = {
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        fontSize: '0.875rem'
    };

    return (
        <div style={containerStyle}>
            <h1 style={titleStyle}>🗺️ India Flood Monitoring Map</h1>

            <div style={controlPanelStyle}>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                        style={buttonStyle(mapStyle === 'satellite')}
                        onClick={() => setMapStyle('satellite')}
                    >
                        Satellite
                    </button>
                    <button
                        style={buttonStyle(mapStyle === 'terrain')}
                        onClick={() => setMapStyle('terrain')}
                    >
                        Terrain
                    </button>
                    <button
                        style={buttonStyle(mapStyle === 'street')}
                        onClick={() => setMapStyle('street')}
                    >
                        Street
                    </button>
                </div>

                <div style={legendStyle}>
                    <div style={{ fontWeight: '600', color: '#374151' }}>Risk Levels:</div>
                    {Object.entries(riskColors).map(([level, color]) => (
                        <div key={level} style={legendItemStyle}>
                            <div style={{
                                width: '16px',
                                height: '16px',
                                borderRadius: '50%',
                                background: color,
                                border: '2px solid white',
                                boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                            }}></div>
                            <span style={{ fontWeight: '500', color: '#6b7280' }}>{level}</span>
                        </div>
                    ))}
                </div>
            </div>

            <div style={mapContainerStyle}>
                <MapContainer
                    center={[23.5, 80.0]} // Center of India
                    zoom={5}
                    minZoom={4}
                    maxZoom={18}
                    style={{ height: '100%', width: '100%' }}
                    maxBounds={[[6, 68], [36, 98]]} // Restricts to India bounds
                    maxBoundsViscosity={1.0}
                >
                    <TileLayer
                        attribution={mapTiles[mapStyle].attribution}
                        url={mapTiles[mapStyle].url}
                        maxZoom={18}
                    />

                    {regions.map(region => {
                        const regionDevices = devices.filter(d => d.region_id === region.region_id);
                        const activeCount = regionDevices.filter(d => d.is_active).length;

                        // Calculate highest risk level in region
                        let highestRisk = 'LOW';
                        regionDevices.forEach(device => {
                            const risk = getRiskLevel(device);
                            if (risk === 'CRITICAL') highestRisk = 'CRITICAL';
                            else if (risk === 'HIGH' && highestRisk !== 'CRITICAL') highestRisk = 'HIGH';
                            else if (risk === 'MEDIUM' && highestRisk === 'LOW') highestRisk = 'MEDIUM';
                        });

                        const riskColor = riskColors[highestRisk];
                        const radiusKm = highestRisk === 'CRITICAL' ? 50 : highestRisk === 'HIGH' ? 35 : highestRisk === 'MEDIUM' ? 25 : 15;

                        return (
                            <React.Fragment key={region.region_id}>
                                {/* Risk radius circle */}
                                <Circle
                                    center={[region.latitude, region.longitude]}
                                    radius={radiusKm * 1000} // Convert km to meters
                                    pathOptions={{
                                        color: riskColor,
                                        fillColor: riskColor,
                                        fillOpacity: 0.15,
                                        weight: 2
                                    }}
                                />

                                {/* Region marker */}
                                <Marker
                                    position={[region.latitude, region.longitude]}
                                    icon={createCustomIcon(riskColor)}
                                >
                                    <Popup maxWidth={300}>
                                        <div style={{ minWidth: '260px' }}>
                                            {/* Header */}
                                            <div style={{
                                                background: `linear-gradient(135deg, ${riskColor}15, ${riskColor}05)`,
                                                padding: '1rem',
                                                margin: '-0.5rem -0.5rem 1rem',
                                                borderRadius: '6px 6px 0 0'
                                            }}>
                                                <h3 style={{
                                                    margin: '0 0 0.5rem 0',
                                                    fontSize: '1.25rem',
                                                    fontWeight: '700',
                                                    color: '#111827'
                                                }}>
                                                    {region.name}
                                                </h3>
                                                <div style={{
                                                    display: 'inline-block',
                                                    padding: '0.25rem 0.75rem',
                                                    background: riskColor,
                                                    color: 'white',
                                                    borderRadius: '12px',
                                                    fontSize: '0.75rem',
                                                    fontWeight: '600'
                                                }}>
                                                    {highestRisk} RISK
                                                </div>
                                            </div>

                                            {/* Region Info */}
                                            <div style={{ marginBottom: '1rem' }}>
                                                <p style={{ margin: '0.375rem 0', fontSize: '0.875rem' }}>
                                                    <strong>River:</strong> {region.river_name}
                                                </p>
                                                {region.state && (
                                                    <p style={{ margin: '0.375rem 0', fontSize: '0.875rem' }}>
                                                        <strong>State:</strong> {region.state}
                                                    </p>
                                                )}
                                                <p style={{ margin: '0.375rem 0', fontSize: '0.875rem' }}>
                                                    <strong>Devices:</strong> {activeCount} active / {regionDevices.length} total
                                                </p>
                                            </div>

                                            {/* Device List */}
                                            <div style={{
                                                borderTop: '1px solid #e5e7eb',
                                                paddingTop: '0.75rem'
                                            }}>
                                                <h4 style={{
                                                    margin: '0 0 0.625rem 0',
                                                    fontSize: '0.875rem',
                                                    fontWeight: '600',
                                                    color: '#6b7280'
                                                }}>
                                                    SENSORS
                                                </h4>
                                                <div style={{ display: 'grid', gap: '0.5rem', maxHeight: '200px', overflowY: 'auto' }}>
                                                    {regionDevices.map(device => {
                                                        const deviceRisk = getRiskLevel(device);
                                                        const deviceColor = riskColors[deviceRisk];

                                                        return (
                                                            <div key={device.device_id} style={{
                                                                padding: '0.625rem',
                                                                background: '#f9fafb',
                                                                borderRadius: '6px',
                                                                borderLeft: `3px solid ${deviceColor}`,
                                                                fontSize: '0.8125rem'
                                                            }}>
                                                                <div style={{
                                                                    fontWeight: 600,
                                                                    marginBottom: '0.25rem',
                                                                    color: '#111827'
                                                                }}>
                                                                    {device.name}
                                                                </div>
                                                                <div style={{
                                                                    display: 'flex',
                                                                    justifyContent: 'space-between',
                                                                    alignItems: 'center',
                                                                    gap: '0.5rem'
                                                                }}>
                                                                    <span style={{
                                                                        color: device.is_active ? '#16a34a' : '#dc2626',
                                                                        fontSize: '0.75rem',
                                                                        fontWeight: '500'
                                                                    }}>
                                                                        ● {device.is_active ? 'ACTIVE' : 'OFFLINE'}
                                                                    </span>
                                                                    {device.battery_level && (
                                                                        <span style={{
                                                                            fontSize: '0.75rem',
                                                                            color: device.battery_level > 30 ? '#16a34a' : '#dc2626'
                                                                        }}>
                                                                            {device.battery_level}%
                                                                        </span>
                                                                    )}
                                                                </div>
                                                                {device.last_water_level && (
                                                                    <div style={{
                                                                        marginTop: '0.375rem',
                                                                        paddingTop: '0.375rem',
                                                                        borderTop: '1px solid #e5e7eb'
                                                                    }}>
                                                                        <div style={{ color: '#2563eb', fontSize: '0.75rem' }}>
                                                                            Water: {device.last_water_level.toFixed(2)}m / {device.alert_threshold.toFixed(1)}m
                                                                        </div>
                                                                        {device.last_rainfall && (
                                                                            <div style={{ color: '#7c3aed', fontSize: '0.75rem', marginTop: '0.125rem' }}>
                                                                                Rain: {device.last_rainfall.toFixed(0)}mm
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                )}
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        </div>
                                    </Popup>
                                </Marker>
                            </React.Fragment>
                        );
                    })}
                </MapContainer>
            </div>

            {/* Statistics Panel */}
            <div style={{
                marginTop: '2rem',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '1rem'
            }}>
                {Object.entries(riskColors).map(([level, color]) => {
                    const count = regions.filter(region => {
                        const regionDevices = devices.filter(d => d.region_id === region.region_id);
                        return regionDevices.some(d => getRiskLevel(d) === level);
                    }).length;

                    return (
                        <div key={level} style={{
                            background: 'white',
                            padding: '1.25rem',
                            borderRadius: '8px',
                            border: `2px solid ${color}`,
                            textAlign: 'center'
                        }}>
                            <div style={{
                                fontSize: '2rem',
                                fontWeight: '700',
                                color,
                                marginBottom: '0.25rem'
                            }}>
                                {count}
                            </div>
                            <div style={{
                                fontSize: '0.875rem',
                                fontWeight: '600',
                                color: '#6b7280'
                            }}>
                                {level} RISK ZONES
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default MapTab;
