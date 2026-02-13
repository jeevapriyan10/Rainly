import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import NavBar from './components/NavBar';
import Dashboard from './components/Dashboard';
import MapTab from './components/MapTab';
import DevicesTab from './components/DevicesTab';
import ParticipantsTab from './components/ParticipantsTab';
import SimulatorTab from './components/SimulatorTab';
import RegionsTab from './components/RegionsTab';
import AnalyticsTab from './components/AnalyticsTab';

function App() {
    return (
        <Router>
            <div style={{ minHeight: '100vh', background: '#f9fafb' }}>
                <NavBar />
                <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/map" element={<MapTab />} />
                    <Route path="/regions" element={<RegionsTab />} />
                    <Route path="/devices" element={<DevicesTab />} />
                    <Route path="/participants" element={<ParticipantsTab />} />
                    <Route path="/analytics" element={<AnalyticsTab />} />
                    <Route path="/simulator" element={<SimulatorTab />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;
