"use client";

import LogViewer from "@/components/LogViewer";

export default function LogsPage() {
    return (
        <div className="container" style={{ height: 'calc(100vh - 40px)', padding: '20px' }}>
            <h1 style={{ marginBottom: '20px', fontSize: '24px', fontWeight: 'bold' }}>系統日誌監控</h1>
            <div style={{ height: 'calc(100% - 60px)' }}>
                <LogViewer />
            </div>
        </div>
    );
}
