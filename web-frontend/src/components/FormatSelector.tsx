"use client";

import { useState } from "react";
import { getApiUrl } from "@/utils/api";

interface FormatSelectorProps {
    taskId: string;
    onDownload?: (format: string) => void;
}

export default function FormatSelector({ taskId, onDownload }: FormatSelectorProps) {
    const [downloading, setDownloading] = useState<string | null>(null);

    const formats = [
        { value: 'txt', label: 'TXT', icon: '📄', color: '#94a3b8' },
        { value: 'docx', label: 'DOCX', icon: '📝', color: '#3b82f6' },
        { value: 'xlsx', label: 'XLSX', icon: '📊', color: '#10b981' },
        { value: 'pdf', label: 'PDF', icon: '📕', color: '#ef4444' },
        { value: 'md', label: 'Markdown', icon: '📋', color: '#8b5cf6' }
    ];

    const handleDownload = async (format: string) => {
        setDownloading(format);

        try {
            const apiUrl = getApiUrl();
            const endpoint = apiUrl ? `${apiUrl}/api/convert` : '/api/convert';

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: JSON.stringify({
                    task_id: taskId,
                    target_format: format,
                    include_metadata: true
                })
            });

            if (!response.ok) throw new Error('轉換失敗');

            // 從 Content-Disposition header 讀取檔名
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `ocr_result.${format}`;

            if (contentDisposition) {
                // 嘗試解析 filename*=utf-8''encoded_name 或 filename="name"
                const filenameMatch = contentDisposition.match(/filename\*=utf-8''(.+)|filename="?([^"]+)"?/);
                if (filenameMatch) {
                    const encodedName = filenameMatch[1];
                    const regularName = filenameMatch[2];
                    filename = encodedName ? decodeURIComponent(encodedName) : regularName;
                }
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            window.URL.revokeObjectURL(url);

            onDownload?.(format);
        } catch (err: any) {
            alert(`❌ ${format.toUpperCase()} 轉換失敗: ${err.message}`);
        } finally {
            setDownloading(null);
        }
    };

    return (
        <div className="format-selector" style={{ marginBottom: '20px' }}>
            <p style={{ fontSize: '14px', marginBottom: '12px', color: '#94a3b8', fontWeight: 500 }}>
                💾 選擇下載格式
            </p>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                {formats.map(({ value, label, icon, color }) => (
                    <button
                        key={value}
                        onClick={() => handleDownload(value)}
                        disabled={downloading === value}
                        className="format-btn"
                        style={{
                            padding: '10px 16px',
                            borderRadius: '8px',
                            background: downloading === value
                                ? 'rgba(255,255,255,0.1)'
                                : 'rgba(0,0,0,0.2)',
                            border: `1px solid ${downloading === value ? color : 'rgba(255,255,255,0.1)'}`,
                            color: '#fff',
                            cursor: downloading === value ? 'wait' : 'pointer',
                            transition: '0.2s',
                            fontSize: '14px',
                            fontWeight: 500,
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            opacity: downloading === value ? 0.6 : 1
                        }}
                        onMouseEnter={(e) => {
                            if (downloading !== value) {
                                e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
                                e.currentTarget.style.borderColor = color;
                                e.currentTarget.style.transform = 'translateY(-2px)';
                                e.currentTarget.style.boxShadow = `0 4px 12px ${color}40`;
                            }
                        }}
                        onMouseLeave={(e) => {
                            if (downloading !== value) {
                                e.currentTarget.style.background = 'rgba(0,0,0,0.2)';
                                e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)';
                                e.currentTarget.style.transform = 'translateY(0)';
                                e.currentTarget.style.boxShadow = 'none';
                            }
                        }}
                    >
                        <span>{icon}</span>
                        <span>{downloading === value ? '下載中...' : label}</span>
                    </button>
                ))}
            </div>
        </div>
    );
}
