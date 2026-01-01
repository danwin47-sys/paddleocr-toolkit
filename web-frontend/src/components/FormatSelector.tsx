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
        { value: 'txt', label: 'TXT', icon: '📄' },
        { value: 'docx', label: 'DOCX', icon: '📝' },
        { value: 'xlsx', label: 'XLSX', icon: '📊' },
        { value: 'pdf', label: 'PDF', icon: '📕' },
        { value: 'md', label: 'Markdown', icon: '📋' }
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

            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `ocr_result.${format}`;

            if (contentDisposition) {
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
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : '未知錯誤';
            alert(`❌ ${format.toUpperCase()} 轉換失敗: ${message}`);
        } finally {
            setDownloading(null);
        }
    };

    return (
        <div style={{ marginBottom: 'var(--spacing-4)' }}>
            <p className="text-secondary font-medium" style={{ fontSize: 'var(--font-size-sm)', marginBottom: 'var(--spacing-3)' }}>
                💾 選擇下載格式
            </p>
            <div style={{ display: 'flex', gap: 'var(--spacing-2)', flexWrap: 'wrap' }}>
                {formats.map(({ value, label, icon }) => (
                    <button
                        key={value}
                        onClick={() => handleDownload(value)}
                        disabled={downloading === value}
                        className="btn btn-secondary"
                        style={{
                            opacity: downloading === value ? 0.6 : 1,
                            cursor: downloading === value ? 'wait' : 'pointer'
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
