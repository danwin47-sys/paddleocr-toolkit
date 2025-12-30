import { useState, useEffect } from 'react';

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
    const [geminiKey, setGeminiKey] = useState('');
    const [claudeKey, setClaudeKey] = useState('');

    // Load keys from localStorage on mount
    useEffect(() => {
        if (isOpen) {
            setGeminiKey(localStorage.getItem('gemini_api_key') || '');
            setClaudeKey(localStorage.getItem('claude_api_key') || '');
        }
    }, [isOpen]);

    const handleSave = () => {
        localStorage.setItem('gemini_api_key', geminiKey);
        localStorage.setItem('claude_api_key', claudeKey);
        onClose();
        alert('設定已儲存！');
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="glass-card w-[90%] max-w-md relative" style={{ background: 'rgba(30, 41, 59, 0.9)' }}>
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-slate-400 hover:text-white"
                >
                    ✕
                </button>

                <h2 className="text-xl font-bold mb-6 text-white">系統設定</h2>

                <div className="space-y-6">
                    {/* Gemini Setting */}
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Gemini API Key (Google)
                        </label>
                        <input
                            type="password"
                            value={geminiKey}
                            onChange={(e) => setGeminiKey(e.target.value)}
                            placeholder="AIzaSy..."
                            className="glass-input"
                        />
                        <p className="text-xs text-slate-500 mt-1">
                            用於免費且快速的語義校正。
                            <a href="https://makersuite.google.com/app/apikey" target="_blank" className="text-indigo-400 hover:text-indigo-300 ml-1">
                                取得 Key
                            </a>
                        </p>
                    </div>

                    {/* Claude Setting */}
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Claude API Key (Anthropic)
                        </label>
                        <input
                            type="password"
                            value={claudeKey}
                            onChange={(e) => setClaudeKey(e.target.value)}
                            placeholder="sk-ant-api03..."
                            className="glass-input"
                        />
                        <p className="text-xs text-slate-500 mt-1">
                            用於高品質的深度校正 (需付費)。
                        </p>
                    </div>
                </div>

                <div className="mt-8 flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 rounded-lg text-slate-300 hover:bg-white/10 transition-colors"
                    >
                        取消
                    </button>
                    <button
                        onClick={handleSave}
                        className="btn-primary"
                        style={{ width: 'auto' }}
                    >
                        儲存設定
                    </button>
                </div>
            </div>
        </div>
    );
}
