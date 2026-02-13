import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const NavBar = () => {
    const location = useLocation();



    const tabs = [
        { path: '/', label: 'Home' },
        { path: '/map', label: 'Map' },
        { path: '/regions', label: 'Regions' },
        { path: '/devices', label: 'Devices' },
        { path: '/participants', label: 'People' },
        { path: '/analytics', label: 'Analytics' },
        { path: '/simulator', label: 'Simulator' }
    ];

    return (
        <nav className="navbar">
            <div className="nav-container">
                <Link to="/" className="nav-logo">
                    Rainly
                </Link>
                <div className="nav-links">
                    {tabs.map(tab => (
                        <Link
                            key={tab.path}
                            to={tab.path}
                            className={`nav-item ${location.pathname === tab.path ? 'active' : ''}`}
                        >
                            {tab.label}
                        </Link>
                    ))}
                </div>
            </div>
        </nav>
    );
};

export default NavBar;
