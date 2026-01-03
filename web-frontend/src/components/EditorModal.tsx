"use client";

import { useState, useEffect } from "react";
import { getApiUrl } from "@/utils/api";

interface EditorModalProps {
    isOpen: boolean;
    onClose: () => void;
    taskId: string;
    initialText: string;
    fileUrl?: string; // Optional URL to the file for split view
}

export default function EditorModal({ isOpen, onClose, taskId, initialText, fileUrl }: EditorModalProps) {
    const [text, setText] = useState(initialText);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        setText(initialText);
    }, [initialText]);

    if (!isOpen) return null;

    const handleSave = async () => {
        setIsSaving(true);
        try {
            const apiUrl = getApiUrl();
            const response = await fetch(`${apiUrl || ''}/api/results/${taskId}/update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            if (!response.ok) throw new Error("Failed to save");
            alert("儲存成功！");
            onClose();
        } catch (e) {
            alert("儲存失敗");
            console.error(e);
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className="modal-overlay">
            <div className="modal-container" style={{ maxWidth: '95vw', height: '90vh', display: 'flex', flexDirection: 'column' }}>
                <div className="modal-header">
                    <h2 className="modal-title">✏️ 互動式校對</h2>
                    <button className="modal-close" onClick={onClose}>✕</button>
                </div>

                <div className="modal-body" style={{ flex: 1, display: 'flex', gap: '20px', overflow: 'hidden', padding: '0' }}>
                    {/* Left: File Viewer (if available) - Currently Placeholder/Iframe */}
                    <div style={{ flex: 1, background: '#f1f5f9', borderRight: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {fileUrl ? (
                            <iframe src={fileUrl} style={{ width: '100%', height: '100%', border: 'none' }} title="Document Viewer" />
                        ) : (
                            <div className="text-secondary">原始文件預覽 (需實作檔案 URL 傳遞)</div>
                        )}
                    </div>

                    {/* Right: Text Editor */}
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '20px' }}>
                        <label className="form-label">OCR 辨識結果 (可編輯)</label>
                        <textarea
                            className="form-input"
                            style={{ flex: 1, resize: 'none', fontFamily: 'monospace', lineHeight: '1.6' }}
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                        />
                    </div>
                </div>

                <div className="modal-footer">
                    <button className="btn btn-secondary" onClick={onClose}>取消</button>
                    <button className="btn btn-primary" onClick={handleSave} disabled={isSaving}>
                        {isSaving ? "儲存中..." : "儲存變更"}
                    </button>
                </div>
            </div>
            <style jsx>{`
                .modal-overlay {
                    position: fixed; inset: 0; background: rgba(0,0,0,0.5); 
                    display: flex; align-items: center; justifyContent: center; z-index: 1000;
                }
                .modal-container { background: white; border-radius: 12px; width: 100%; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
                /* ... reuse other modal styles from globals.css or define here ... */
            `}</style>
        </div>
    );
}
