"use client";

import { useState } from "react";
import { getApiUrl } from "@/utils/api";

interface TranslationModalProps {
    isOpen: boolean;
    onClose: () => void;
    originalText: string;
}

export default function TranslationModal({ isOpen, onClose, originalText }: TranslationModalProps) {
    const [targetLang, setTargetLang] = useState('en');
    const [provider, setProvider] = useState('ollama');
    const [translatedText, setTranslatedText] = useState('');
    const [isTranslating, setIsTranslating] = useState(false);
    const [error, setError] = useState('');
    const [statusText, setStatusText] = useState('');

    const languages = [
        { value: 'en', label: 'English 🇬🇧' },
        { value: 'zh-TW', label: '繁體中文 🇹🇼' },
        { value: 'zh-CN', label: '简体中文 🇨🇳' },
        { value: 'ja', label: '日本語 🇯🇵' },
        { value: 'ko', label: '한국어 🇰🇷' },
        { value: 'es', label: 'Español 🇪🇸' },
        { value: 'fr', label: 'Français 🇫🇷' },
        { value: 'de', label: 'Deutsch 🇩🇪' }
    ];

    const providers = [
        { value: 'ollama', label: 'Ollama (本地免費)', icon: '🖥️' },
        { value: 'gemini', label: 'Gemini (Google AI)', icon: '🌟' },
        { value: 'claude', label: 'Claude (Anthropic)', icon: '🤖' }
    ];

    const handleTranslate = async () => {
        setIsTranslating(true);
        setError('');
        setTranslatedText('');
        setStatusText('正在連線至 AI 服務...');

        try {
            const body: Record<string, string> = {
                text: originalText,
                target_lang: targetLang,
                provider: provider
            };

            if (provider === 'gemini') {
                const apiKey = localStorage.getItem('gemini_api_key');
                if (apiKey) body.api_key = apiKey;
            } else if (provider === 'claude') {
                const apiKey = localStorage.getItem('claude_api_key');
                if (apiKey) body.api_key = apiKey;
            }

            const apiUrl = getApiUrl();
            const endpoint = apiUrl ? `${apiUrl}/api/translate` : '/api/translate';

            setStatusText('正在翻譯中，請稍候...');

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: JSON.stringify(body)
            });

            if (!response.ok) {
                throw new Error(`伺服器錯誤: ${response.status}`);
            }

            const data = await response.json();

            if (data.status === 'success') {
                setTranslatedText(data.translated_text);
                setStatusText('');
            } else {
                setError(data.message || '翻譯失敗');
            }
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : '未知錯誤';
            setError('翻譯失敗: ' + message);
        } finally {
            setIsTranslating(false);
        }
    };

    const handleCopy = () => {
        navigator.clipboard.writeText(translatedText);
        alert('✅ 已複製翻譯結果');
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div
                className="modal-container"
                style={{ maxWidth: '600px' }}
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="modal-header">
                    <h2 className="modal-title">🌐 AI 翻譯</h2>
                    <button className="modal-close" onClick={onClose}>
                        ✕
                    </button>
                </div>

                {/* Body */}
                <div className="modal-body">
                    {/* Language Selection */}
                    <div className="form-group">
                        <label className="form-label">目標語言</label>
                        <select
                            value={targetLang}
                            onChange={(e) => setTargetLang(e.target.value)}
                            className="form-select"
                        >
                            {languages.map(lang => (
                                <option key={lang.value} value={lang.value}>
                                    {lang.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Provider Selection */}
                    <div className="form-group">
                        <label className="form-label">AI 提供商</label>
                        <select
                            value={provider}
                            onChange={(e) => setProvider(e.target.value)}
                            className="form-select"
                        >
                            {providers.map(prov => (
                                <option key={prov.value} value={prov.value}>
                                    {prov.icon} {prov.label}
                                </option>
                            ))}
                        </select>
                        {provider !== 'ollama' && (
                            <p className="text-muted" style={{ marginTop: 'var(--spacing-2)', fontSize: 'var(--font-size-xs)' }}>
                                ⚠️ 需要在設定中配置 API Key
                            </p>
                        )}
                    </div>

                    {/* Translate Button */}
                    <button
                        onClick={handleTranslate}
                        disabled={isTranslating}
                        className="btn btn-primary btn-full"
                        style={{ marginBottom: 'var(--spacing-4)' }}
                    >
                        {isTranslating ? '🔄 翻譯中...' : '🚀 開始翻譯'}
                    </button>

                    {/* Status */}
                    {statusText && (
                        <div className="text-secondary text-center" style={{ marginBottom: 'var(--spacing-4)', fontSize: 'var(--font-size-sm)' }}>
                            {statusText}
                        </div>
                    )}

                    {/* Error */}
                    {error && (
                        <div style={{
                            padding: 'var(--spacing-4)',
                            marginBottom: 'var(--spacing-4)',
                            borderRadius: 'var(--radius-md)',
                            background: 'var(--color-error-light)',
                            border: '1px solid var(--color-error)',
                            color: 'var(--color-error)'
                        }}>
                            ❌ {error}
                        </div>
                    )}

                    {/* Result */}
                    {translatedText && (
                        <div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-2)' }}>
                                <label className="form-label" style={{ marginBottom: 0 }}>翻譯結果</label>
                                <button className="btn btn-ghost" onClick={handleCopy} style={{ fontSize: 'var(--font-size-sm)' }}>
                                    📋 複製
                                </button>
                            </div>
                            <div style={{
                                padding: 'var(--spacing-4)',
                                borderRadius: 'var(--radius-md)',
                                background: 'var(--color-slate-50)',
                                border: '1px solid var(--border-color)',
                                whiteSpace: 'pre-wrap',
                                lineHeight: '1.7',
                                maxHeight: '300px',
                                overflowY: 'auto'
                            }}>
                                {translatedText}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
