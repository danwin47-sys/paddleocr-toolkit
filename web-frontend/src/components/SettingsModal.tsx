import { useState, useEffect } from 'react';

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
    const [geminiKey, setGeminiKey] = useState('');
    const [claudeKey, setClaudeKey] = useState('');
    const [ocrMode, setOcrMode] = useState('hybrid');

    useEffect(() => {
        if (isOpen) {
            setGeminiKey(localStorage.getItem('gemini_api_key') || '');
            setClaudeKey(localStorage.getItem('claude_api_key') || '');
            setOcrMode(localStorage.getItem('ocr_mode') || 'hybrid');
        }
    }, [isOpen]);

    const handleSave = () => {
        localStorage.setItem('gemini_api_key', geminiKey);
        localStorage.setItem('claude_api_key', claudeKey);
        localStorage.setItem('ocr_mode', ocrMode);
        onClose();
        alert('設定已儲存！');
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay">
            <div className="modal-container">
                {/* Header */}
                <div className="modal-header">
                    <h2 className="modal-title">系統設定</h2>
                    <button className="modal-close" onClick={onClose}>
                        ✕
                    </button>
                </div>

                {/* Body */}
                <div className="modal-body">
                    {/* OCR Mode */}
                    <div className="form-group">
                        <label className="form-label">OCR 模式</label>
                        <div style={{ display: 'flex', gap: 'var(--spacing-3)' }}>
                            <label
                                style={{
                                    flex: 1,
                                    padding: 'var(--spacing-4)',
                                    borderRadius: 'var(--radius-md)',
                                    border: `2px solid ${ocrMode === 'hybrid' ? 'var(--color-primary)' : 'var(--border-color)'}`,
                                    background: ocrMode === 'hybrid' ? 'var(--color-primary-light)' : 'var(--bg-surface)',
                                    cursor: 'pointer',
                                    transition: 'all var(--transition-fast)'
                                }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-2)', marginBottom: 'var(--spacing-1)' }}>
                                    <input
                                        type="radio"
                                        name="ocr_mode"
                                        value="hybrid"
                                        checked={ocrMode === 'hybrid'}
                                        onChange={(e) => setOcrMode(e.target.value)}
                                    />
                                    <span className="font-semibold">智能混合 (Hybrid)</span>
                                </div>
                                <p className="text-secondary" style={{ fontSize: 'var(--font-size-xs)', paddingLeft: 'var(--spacing-5)' }}>
                                    推薦使用。保留排版結構、表格與段落。
                                </p>
                            </label>

                            <label
                                style={{
                                    flex: 1,
                                    padding: 'var(--spacing-4)',
                                    borderRadius: 'var(--radius-md)',
                                    border: `2px solid ${ocrMode === 'basic' ? 'var(--color-primary)' : 'var(--border-color)'}`,
                                    background: ocrMode === 'basic' ? 'var(--color-primary-light)' : 'var(--bg-surface)',
                                    cursor: 'pointer',
                                    transition: 'all var(--transition-fast)'
                                }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-2)', marginBottom: 'var(--spacing-1)' }}>
                                    <input
                                        type="radio"
                                        name="ocr_mode"
                                        value="basic"
                                        checked={ocrMode === 'basic'}
                                        onChange={(e) => setOcrMode(e.target.value)}
                                    />
                                    <span className="font-semibold">極速模式 (Basic)</span>
                                </div>
                                <p className="text-secondary" style={{ fontSize: 'var(--font-size-xs)', paddingLeft: 'var(--spacing-5)' }}>
                                    僅擷取純文字，速度最快。
                                </p>
                            </label>
                        </div>
                    </div>

                    {/* Gemini API Key */}
                    <div className="form-group">
                        <label className="form-label">Gemini API Key (Google)</label>
                        <input
                            type="password"
                            value={geminiKey}
                            onChange={(e) => setGeminiKey(e.target.value)}
                            placeholder="AIzaSy..."
                            className="form-input"
                        />
                        <p className="text-muted" style={{ fontSize: 'var(--font-size-xs)', marginTop: 'var(--spacing-1)' }}>
                            用於免費且快速的語義校正。
                            <a href="https://makersuite.google.com/app/apikey" target="_blank" style={{ color: 'var(--color-primary)', marginLeft: 'var(--spacing-1)' }}>
                                取得 Key
                            </a>
                        </p>
                    </div>

                    {/* Claude API Key */}
                    <div className="form-group">
                        <label className="form-label">Claude API Key (Anthropic)</label>
                        <input
                            type="password"
                            value={claudeKey}
                            onChange={(e) => setClaudeKey(e.target.value)}
                            placeholder="sk-ant-api03..."
                            className="form-input"
                        />
                        <p className="text-muted" style={{ fontSize: 'var(--font-size-xs)', marginTop: 'var(--spacing-1)' }}>
                            用於高品質的深度校正 (需付費)。
                        </p>
                    </div>
                </div>

                {/* Footer */}
                <div className="modal-footer">
                    <button className="btn btn-secondary" onClick={onClose}>
                        取消
                    </button>
                    <button className="btn btn-primary" onClick={handleSave}>
                        儲存設定
                    </button>
                </div>
            </div>
        </div>
    );
}
