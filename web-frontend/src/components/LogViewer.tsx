"use client";

import { useEffect, useRef, useState, useCallback } from "react";

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

export default function LogViewer() {
    const [logs, setLogs] = useState<string[]>([]);
    const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting');
    const [reconnectAttempts, setReconnectAttempts] = useState(0);
    const logsEndRef = useRef<HTMLDivElement>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);

    const connectWebSocket = useCallback(() => {
        // 清理現有連接
        if (wsRef.current) {
            wsRef.current.close();
        }

        const wsUrl = `ws://${window.location.hostname}:8000/ws/logs`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        setConnectionStatus('connecting');

        ws.onopen = () => {
            // WebSocket connected
            setConnectionStatus('connected');
            setReconnectAttempts(0);
            setLogs((prev) => [...prev, "[SYSTEM] ✅ Connected to log stream..."]);
        };

        ws.onmessage = (event) => {
            setLogs((prev) => {
                const newLogs = [...prev, event.data];
                if (newLogs.length > 1000) {
                    return newLogs.slice(newLogs.length - 1000);
                }
                return newLogs;
            });
        };

        ws.onclose = () => {
            // WebSocket disconnected
            setConnectionStatus('disconnected');

            // 指數退避重連
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
            setLogs((prev) => [...prev, `[SYSTEM] ⚠️ Connection lost. Reconnecting in ${Math.round(delay / 1000)}s...`]);

            setConnectionStatus('reconnecting');
            reconnectTimeoutRef.current = setTimeout(() => {
                setReconnectAttempts(prev => prev + 1);
                connectWebSocket();
            }, delay);
        };

        ws.onerror = (error) => {
            setLogs((prev) => [...prev, "[SYSTEM] ❌ Connection error."]);
        };

        return ws;
    }, [reconnectAttempts]);

    useEffect(() => {
        const ws = connectWebSocket();

        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
        };
    }, [connectWebSocket]);

    // Auto-scroll to bottom
    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [logs]);

    const clearLogs = () => {
        setLogs([]);
    };

    const manualReconnect = () => {
        setReconnectAttempts(0);
        connectWebSocket();
    };

    const getStatusColor = () => {
        switch (connectionStatus) {
            case 'connected': return '#2ecc71';
            case 'connecting': return '#f39c12';
            case 'reconnecting': return '#e67e22';
            case 'disconnected': return '#e74c3c';
        }
    };

    const getStatusText = () => {
        switch (connectionStatus) {
            case 'connected': return 'Connected';
            case 'connecting': return 'Connecting...';
            case 'reconnecting': return `Reconnecting (${reconnectAttempts})...`;
            case 'disconnected': return 'Disconnected';
        }
    };

    return (
        <div className="log-viewer-container">
            <div className="log-header">
                <div className="log-title">
                    <span className="status-indicator" style={{ backgroundColor: getStatusColor() }}></span>
                    <h3>System Logs</h3>
                    <span className="status-text">{getStatusText()}</span>
                </div>
                <div className="header-actions">
                    {connectionStatus !== 'connected' && (
                        <button onClick={manualReconnect} className="reconnect-btn">
                            🔄 Reconnect
                        </button>
                    )}
                    <button onClick={clearLogs} className="clear-btn">Clear</button>
                </div>
            </div>
            <div className="log-content">
                {logs.map((log, index) => (
                    <div key={index} className="log-line">
                        {log}
                    </div>
                ))}
                <div ref={logsEndRef} />
            </div>

            <style jsx>{`
                .log-viewer-container {
                    display: flex;
                    flex-direction: column;
                    height: 100%;
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                }

                .log-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 10px 16px;
                    background-color: #252526;
                    border-bottom: 1px solid #333;
                }

                .log-title {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }

                .status-indicator {
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    display: inline-block;
                    animation: pulse 2s infinite;
                }

                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }

                .status-text {
                    font-size: 12px;
                    color: #999;
                    font-weight: normal;
                }

                h3 {
                    margin: 0;
                    font-size: 14px;
                    font-weight: 600;
                    color: #fff;
                }

                .header-actions {
                    display: flex;
                    gap: 8px;
                }

                .reconnect-btn {
                    background: transparent;
                    border: 1px solid #e67e22;
                    color: #e67e22;
                    padding: 4px 10px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                    transition: all 0.2s;
                }

                .reconnect-btn:hover {
                    background-color: #e67e22;
                    color: #fff;
                }

                .clear-btn {
                    background: transparent;
                    border: 1px solid #555;
                    color: #ccc;
                    padding: 4px 10px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                    transition: all 0.2s;
                }

                .clear-btn:hover {
                    background-color: #333;
                    border-color: #777;
                    color: #fff;
                }

                .log-content {
                    flex: 1;
                    overflow-y: auto;
                    padding: 16px;
                    font-size: 13px;
                    line-height: 1.5;
                    white-space: pre-wrap;
                    word-break: break-all;
                }

                .log-line {
                    margin-bottom: 2px;
                }
                
                /* Custom Scrollbar */
                .log-content::-webkit-scrollbar {
                    width: 10px;
                }
                
                .log-content::-webkit-scrollbar-track {
                    background: #1e1e1e;
                }
                
                .log-content::-webkit-scrollbar-thumb {
                    background: #424242;
                    border-radius: 5px;
                }

                .log-content::-webkit-scrollbar-thumb:hover {
                    background: #555;
                }
            `}</style>
        </div>
    );
}
