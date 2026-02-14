import { useEffect, useState, useCallback, useRef } from 'react';

const getWebSocketUrl = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use the API URL from env if available (removing /api if present), or fallback to window.location.host
    const host = process.env.REACT_APP_API_URL
        ? new URL(process.env.REACT_APP_API_URL).host
        : window.location.host;
    // Ensure we don't have double slashes if running locally via proxy or potential mismatched base paths
    // For production (Render), typically the frontend and backend are on same domain or specified via env
    if (process.env.NODE_ENV === 'development') {
        return 'ws://localhost:8000/ws/realtime';
    }
    return `${protocol}//${host}/ws/realtime`;
};

const WS_URL = getWebSocketUrl();

export const useWebSocket = () => {
    const [isConnected, setIsConnected] = useState(false);
    const [lastMessage, setLastMessage] = useState(null);
    const [deviceUpdates, setDeviceUpdates] = useState({});
    const [alerts, setAlerts] = useState([]);
    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);

    const connect = useCallback(() => {
        try {
            const ws = new WebSocket(WS_URL);

            ws.onopen = () => {
                console.log('WebSocket connected');
                setIsConnected(true);
                // Send ping to keep alive
                const pingInterval = setInterval(() => {
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({ type: 'ping' }));
                    }
                }, 30000);
                ws.pingInterval = pingInterval;
            };

            ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                setLastMessage(message);

                if (message.type === 'device_update') {
                    setDeviceUpdates(prev => ({
                        ...prev,
                        [message.device_id]: {
                            ...message.data,
                            timestamp: message.timestamp
                        }
                    }));
                } else if (message.type === 'flood_alert') {
                    setAlerts(prev => [...prev, message.data]);
                    // Show browser notification if permitted
                    if ('Notification' in window && Notification.permission === 'granted') {
                        new Notification('Flood Alert', {
                            body: `${message.data.risk_level} risk at ${message.data.region}`,
                            icon: '/favicon.ico'
                        });
                    }
                } else if (message.type === 'warning_generated') {
                    console.log('Warning generated:', message.data);
                }
            };

            ws.onerror = (error) => {
                console.error(' WebSocket error:', error);
            };

            ws.onclose = () => {
                console.log('WebSocket disconnected');
                setIsConnected(false);
                if (ws.pingInterval) {
                    clearInterval(ws.pingInterval);
                }
                // Attempt to reconnect after 5 seconds
                reconnectTimeoutRef.current = setTimeout(() => {
                    console.log('Attempting to reconnect...');
                    connect();
                }, 5000);
            };

            wsRef.current = ws;
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
        }
    }, []);

    useEffect(() => {
        connect();

        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
        };
    }, [connect]);

    const sendMessage = useCallback((message) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message));
        }
    }, []);

    return {
        isConnected,
        lastMessage,
        deviceUpdates,
        alerts,
        sendMessage
    };
};
